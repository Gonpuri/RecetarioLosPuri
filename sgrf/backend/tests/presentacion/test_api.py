"""Pruebas de integracion de la API REST.

Verifican el contrato HTTP: codigos de estado, forma de las respuestas y
traduccion de los errores del negocio. Requieren base de datos.

    cd backend && pytest tests/presentacion
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from sgrf.infraestructura.recetario.models import (
    FuenteModelo,
    IngredienteModelo,
    UsuarioModelo,
)

pytestmark = pytest.mark.django_db

CLAVE = "una-clave-segura"


@pytest.fixture
def administrador():
    """Administrador con contrasenia utilizable."""
    return UsuarioModelo.objects.create_superuser(
        correo="admin@familia.test", nombre="Gonza", password=CLAVE
    )


@pytest.fixture
def familiar():
    """Usuario Familiar con contrasenia utilizable."""
    return UsuarioModelo.objects.create_user(
        correo="ana@familia.test", nombre="Ana", password=CLAVE
    )


@pytest.fixture
def catalogo():
    """Fuente e ingredientes minimos."""
    return {
        "fuente": FuenteModelo.objects.create(nombre="Cuaderno de la abuela"),
        "harina": IngredienteModelo.objects.create(nombre="Harina 000"),
        "sal": IngredienteModelo.objects.create(nombre="Sal fina"),
    }


def autenticar(usuario) -> APIClient:
    """Devuelve un cliente con el token del usuario indicado."""
    cliente = APIClient()
    respuesta = cliente.post(
        "/api/auth/token/",
        {"correo": usuario.correo, "password": CLAVE},
        format="json",
    )
    assert respuesta.status_code == 200, respuesta.data
    cliente.credentials(HTTP_AUTHORIZATION=f"Bearer {respuesta.data['access']}")
    return cliente


def cuerpo_receta(catalogo, nombre="Pan casero") -> dict:
    """Cuerpo valido para el alta de una receta."""
    return {
        "nombre": nombre,
        "descripcion": "Receta familiar.",
        "rendimiento_base": "4",
        "rendimiento_descripcion": "porciones",
        "fuente_id": str(catalogo["fuente"].id),
        "preparaciones": [
            {
                "nombre": "Masa",
                "ingredientes": [
                    {
                        "ingrediente_id": str(catalogo["harina"].id),
                        "cantidad": "500",
                        "unidad": "g",
                        "tipo_escalado": "lineal",
                    },
                    {
                        "ingrediente_id": str(catalogo["sal"].id),
                        "tipo_escalado": "a_gusto",
                    },
                ],
                "pasos": ["Mezclar los secos.", "Amasar diez minutos."],
            }
        ],
    }


class TestAutenticacion:
    """El acceso exige un token valido."""

    def test_sin_token_devuelve_401(self):
        assert APIClient().get("/api/recetas/").status_code == 401

    def test_el_token_habilita_el_acceso(self, familiar):
        assert autenticar(familiar).get("/api/recetas/").status_code == 200

    def test_credenciales_incorrectas_devuelven_401(self, familiar):
        respuesta = APIClient().post(
            "/api/auth/token/",
            {"correo": familiar.correo, "password": "incorrecta"},
            format="json",
        )
        assert respuesta.status_code == 401

    def test_el_perfil_informa_el_rol(self, administrador):
        respuesta = autenticar(administrador).get("/api/perfil/")
        assert respuesta.data["rol"] == "administrador"


class TestRecetas:
    """Alta, consulta y edicion de Recetas."""

    def test_crear_devuelve_201(self, familiar, catalogo):
        respuesta = autenticar(familiar).post(
            "/api/recetas/", cuerpo_receta(catalogo), format="json"
        )
        assert respuesta.status_code == 201
        assert respuesta.data["nombre"] == "Pan casero"

    def test_las_cantidades_viajan_como_texto(self, familiar, catalogo):
        """Evita que el front pierda precision al convertirlas a float."""
        respuesta = autenticar(familiar).post(
            "/api/recetas/", cuerpo_receta(catalogo), format="json"
        )
        ingrediente = respuesta.data["preparaciones"][0]["ingredientes"][0]
        assert isinstance(ingrediente["cantidad"], str)

    def test_el_rendimiento_no_se_lee_como_miles(self, familiar, catalogo):
        """Bug reportado: la tarjeta de receta mostraba "50 porciones" como
        "50000". PostgreSQL devuelve la columna con su precision completa
        (50.000) y, como en Argentina el punto es separador de miles, ese
        texto se lee como cincuenta mil. La API debe devolver "50", no
        "50.000" ni "50000".
        """
        cuerpo = cuerpo_receta(catalogo)
        cuerpo["rendimiento_base"] = "50"
        cliente = autenticar(familiar)
        creada = cliente.post("/api/recetas/", cuerpo, format="json")
        assert creada.data["rendimiento_base"] == "50"

        # La tarjeta del listado usa el mismo campo: debe coincidir.
        listado = cliente.get("/api/recetas/")
        resumen = next(r for r in listado.data if r["id"] == creada.data["id"])
        assert resumen["rendimiento_base"] == "50"

        # Y tiene que sobrevivir tambien a una relectura desde la base.
        recuperada = cliente.get(f"/api/recetas/{creada.data['id']}/")
        assert recuperada.data["rendimiento_base"] == "50"

    def test_los_ingredientes_a_gusto_traen_su_texto(self, familiar, catalogo):
        respuesta = autenticar(familiar).post(
            "/api/recetas/", cuerpo_receta(catalogo), format="json"
        )
        sal = next(
            i
            for i in respuesta.data["preparaciones"][0]["ingredientes"]
            if i["tipo_escalado"] == "a_gusto"
        )
        assert sal["texto_cantidad"] == "a gusto"
        assert sal["cantidad"] is None

    def test_nombre_duplicado_devuelve_409(self, familiar, catalogo):
        cliente = autenticar(familiar)
        cliente.post("/api/recetas/", cuerpo_receta(catalogo), format="json")
        respuesta = cliente.post(
            "/api/recetas/", cuerpo_receta(catalogo), format="json"
        )
        assert respuesta.status_code == 409
        assert "error" in respuesta.data

    def test_receta_sin_preparaciones_devuelve_422(self, familiar, catalogo):
        """RN-003 se traduce a 422 con el codigo de la regla."""
        cuerpo = cuerpo_receta(catalogo)
        cuerpo["preparaciones"] = []
        respuesta = autenticar(familiar).post(
            "/api/recetas/", cuerpo, format="json"
        )
        assert respuesta.status_code == 422

    def test_fuente_inexistente_devuelve_404(self, familiar, catalogo):
        cuerpo = cuerpo_receta(catalogo)
        cuerpo["fuente_id"] = "00000000-0000-0000-0000-000000000000"
        respuesta = autenticar(familiar).post(
            "/api/recetas/", cuerpo, format="json"
        )
        assert respuesta.status_code == 404

    def test_datos_mal_formados_devuelven_400(self, familiar, catalogo):
        cuerpo = cuerpo_receta(catalogo)
        cuerpo["rendimiento_base"] = "no-es-un-numero"
        respuesta = autenticar(familiar).post(
            "/api/recetas/", cuerpo, format="json"
        )
        assert respuesta.status_code == 400

    def test_receta_inexistente_devuelve_404(self, familiar):
        respuesta = autenticar(familiar).get(
            "/api/recetas/00000000-0000-0000-0000-000000000000/"
        )
        assert respuesta.status_code == 404

    def test_editar_cambia_el_nombre(self, administrador, catalogo):
        cliente = autenticar(administrador)
        creada = cliente.post(
            "/api/recetas/", cuerpo_receta(catalogo), format="json"
        )
        respuesta = cliente.patch(
            f"/api/recetas/{creada.data['id']}/",
            {"nombre": "Pan integral"},
            format="json",
        )
        assert respuesta.status_code == 200
        assert respuesta.data["nombre"] == "Pan integral"

    def test_editar_receta_archivada_devuelve_409(self, administrador, catalogo):
        cliente = autenticar(administrador)
        creada = cliente.post(
            "/api/recetas/", cuerpo_receta(catalogo), format="json"
        )
        cliente.post(f"/api/recetas/{creada.data['id']}/archivar/")
        respuesta = cliente.patch(
            f"/api/recetas/{creada.data['id']}/",
            {"nombre": "Otro nombre"},
            format="json",
        )
        assert respuesta.status_code == 409


class TestEscaladoApi:
    """El escalado no debe alterar la receta almacenada (RN-004)."""

    def test_devuelve_las_cantidades_ajustadas(self, familiar, catalogo):
        cliente = autenticar(familiar)
        creada = cliente.post(
            "/api/recetas/", cuerpo_receta(catalogo), format="json"
        )
        respuesta = cliente.post(
            f"/api/recetas/{creada.data['id']}/escalar/",
            {"rendimiento_objetivo": "8"},
            format="json",
        )
        assert respuesta.status_code == 200
        harina = respuesta.data["preparaciones"][0]["ingredientes"][0]
        assert harina["texto_cantidad"] == "1000 g"

    def test_los_pasos_y_las_fotos_se_ven_al_escalar(self, administrador, catalogo):
        """Bug reportado en producción: al ajustar el rendimiento, la
        pantalla se quedaba solo con los ingredientes; pasos y fotos
        desaparecían porque el escalado no los copiaba desde la receta
        original.
        """
        cliente = autenticar(administrador)
        creada = cliente.post(
            "/api/recetas/", cuerpo_receta(catalogo), format="json"
        )
        receta_id = creada.data["id"]
        preparacion_id = creada.data["preparaciones"][0]["id"]
        cliente.post(
            f"/api/recetas/{receta_id}/preparaciones/{preparacion_id}/fotografias/",
            {"ruta": "https://cdn.test/final.jpg", "tipo": "final"},
            format="json",
        )

        respuesta = cliente.post(
            f"/api/recetas/{receta_id}/escalar/",
            {"rendimiento_objetivo": "8"},
            format="json",
        )
        preparacion_escalada = respuesta.data["preparaciones"][0]
        assert len(preparacion_escalada["pasos"]) == 2
        assert len(preparacion_escalada["fotografias"]) == 1
        assert preparacion_escalada["fotografias"][0]["ruta"] == (
            "https://cdn.test/final.jpg"
        )

    def test_la_receta_almacenada_no_cambia(self, familiar, catalogo):
        cliente = autenticar(familiar)
        creada = cliente.post(
            "/api/recetas/", cuerpo_receta(catalogo), format="json"
        )
        cliente.post(
            f"/api/recetas/{creada.data['id']}/escalar/",
            {"rendimiento_objetivo": "100"},
            format="json",
        )
        recuperada = cliente.get(f"/api/recetas/{creada.data['id']}/")
        assert recuperada.data["rendimiento_base"] == "4"


class TestListaComprasApi:
    """RN-006: solo lo que el usuario selecciona."""

    def test_genera_la_lista_con_lo_seleccionado(self, familiar, catalogo):
        cliente = autenticar(familiar)
        creada = cliente.post(
            "/api/recetas/", cuerpo_receta(catalogo), format="json"
        )
        harina = creada.data["preparaciones"][0]["ingredientes"][0]
        respuesta = cliente.post(
            f"/api/recetas/{creada.data['id']}/lista-compras/",
            {
                "ingredientes_seleccionados": [
                    harina["ingrediente_preparacion_id"]
                ],
                "rendimiento_objetivo": "8",
                "persistir": True,
            },
            format="json",
        )
        assert respuesta.status_code == 200
        assert len(respuesta.data["items"]) == 1
        assert respuesta.data["items"][0]["texto_cantidad"] == "1000 g"

    def test_las_listas_son_personales(self, familiar, administrador, catalogo):
        """Cada usuario ve solo sus propias listas."""
        cliente_ana = autenticar(familiar)
        creada = cliente_ana.post(
            "/api/recetas/", cuerpo_receta(catalogo), format="json"
        )
        harina = creada.data["preparaciones"][0]["ingredientes"][0]
        cliente_ana.post(
            f"/api/recetas/{creada.data['id']}/lista-compras/",
            {
                "ingredientes_seleccionados": [
                    harina["ingrediente_preparacion_id"]
                ],
                "persistir": True,
            },
            format="json",
        )
        assert len(cliente_ana.get("/api/listas-compra/").data) == 1
        assert autenticar(administrador).get("/api/listas-compra/").data == []


class TestPermisosApi:
    """Decision D-9 y D-19: catalogos y usuarios, segun el tipo.

    Los ingredientes los puede crear cualquier usuario activo (D-19). El
    resto de los catalogos y la gestion de usuarios siguen reservados al
    Administrador (D-9).
    """

    def test_familiar_crea_ingredientes(self, familiar):
        respuesta = autenticar(familiar).post(
            "/api/ingredientes/", {"nombre": "Azucar"}, format="json"
        )
        assert respuesta.status_code == 201

    def test_administrador_crea_ingredientes(self, administrador):
        respuesta = autenticar(administrador).post(
            "/api/ingredientes/", {"nombre": "Azucar"}, format="json"
        )
        assert respuesta.status_code == 201

    def test_familiar_no_crea_categorias(self, familiar):
        respuesta = autenticar(familiar).post(
            "/api/categorias/", {"nombre": "Panaderia"}, format="json"
        )
        assert respuesta.status_code == 403

    def test_familiar_no_crea_fuentes(self, familiar):
        respuesta = autenticar(familiar).post(
            "/api/fuentes/", {"nombre": "Internet"}, format="json"
        )
        assert respuesta.status_code == 403

    def test_familiar_consulta_el_catalogo(self, familiar, catalogo):
        respuesta = autenticar(familiar).get("/api/ingredientes/")
        assert respuesta.status_code == 200
        assert len(respuesta.data) == 2

    def test_familiar_no_administra_usuarios(self, familiar):
        respuesta = autenticar(familiar).get("/api/usuarios/")
        assert respuesta.status_code == 403


class TestBusquedaApi:
    """Criterio de aceptacion 4.12."""

    def test_busca_por_nombre(self, familiar, catalogo):
        cliente = autenticar(familiar)
        cliente.post("/api/recetas/", cuerpo_receta(catalogo), format="json")
        respuesta = cliente.get("/api/recetas/?texto=pan")
        assert len(respuesta.data) == 1

    def test_excluye_archivadas_por_defecto(self, administrador, catalogo):
        cliente = autenticar(administrador)
        creada = cliente.post(
            "/api/recetas/", cuerpo_receta(catalogo), format="json"
        )
        cliente.post(f"/api/recetas/{creada.data['id']}/archivar/")
        assert cliente.get("/api/recetas/?texto=pan").data == []

    def test_incluye_archivadas_si_se_pide(self, administrador, catalogo):
        cliente = autenticar(administrador)
        creada = cliente.post(
            "/api/recetas/", cuerpo_receta(catalogo), format="json"
        )
        cliente.post(f"/api/recetas/{creada.data['id']}/archivar/")
        respuesta = cliente.get("/api/recetas/?texto=pan&incluir_archivadas=true")
        assert len(respuesta.data) == 1


class TestFotografiasApi:
    """RN-005: el limite se traduce a 422 con el codigo de la regla."""

    def test_rechaza_la_cuarta_fotografia(self, administrador, catalogo):
        cliente = autenticar(administrador)
        creada = cliente.post(
            "/api/recetas/", cuerpo_receta(catalogo), format="json"
        )
        receta_id = creada.data["id"]
        preparacion_id = creada.data["preparaciones"][0]["id"]
        ruta = f"/api/recetas/{receta_id}/preparaciones/{preparacion_id}/fotografias/"

        for indice in range(2):
            respuesta = cliente.post(
                ruta,
                {"ruta": f"https://cdn.test/p{indice}.jpg", "tipo": "proceso"},
                format="json",
            )
            assert respuesta.status_code == 201

        assert (
            cliente.post(
                ruta,
                {"ruta": "https://cdn.test/final.jpg", "tipo": "final"},
                format="json",
            ).status_code
            == 201
        )

        cuarta = cliente.post(
            ruta,
            {"ruta": "https://cdn.test/extra.jpg", "tipo": "proceso"},
            format="json",
        )
        assert cuarta.status_code == 422
        assert cuarta.data["regla"] == "RN-005"


class TestFirmaFotografia:
    """Firma de subida directa a Cloudinary."""

    def test_exige_autenticacion(self):
        assert APIClient().post("/api/fotografias/firma/").status_code == 401

    def test_sin_configurar_devuelve_503_con_indicacion(self, familiar, settings):
        """El fallo debe decir que falta configurar, no romper de forma opaca."""
        settings.CLOUDINARY_URL = ""
        respuesta = autenticar(familiar).post("/api/fotografias/firma/")
        assert respuesta.status_code == 503
        assert "CLOUDINARY_URL" in respuesta.data["error"]

    def test_configurado_devuelve_la_firma_sin_el_secreto(self, familiar, settings):
        """El secreto de la cuenta jamas debe viajar al navegador."""
        settings.CLOUDINARY_URL = "cloudinary://123456789:secreto-privado@cuenta-test"
        import cloudinary

        cloudinary.config(
            cloud_name="cuenta-test", api_key="123456789", api_secret="secreto-privado"
        )

        respuesta = autenticar(familiar).post("/api/fotografias/firma/")
        assert respuesta.status_code == 200
        assert respuesta.data["signature"]
        assert respuesta.data["folder"] == "sgrf/recetas"
        assert "secreto-privado" not in str(respuesta.data)


class TestReordenamientoApi:
    """RF-014 y RF-022: reordenar preparaciones y pasos."""

    def test_reordenar_preparaciones(self, administrador, catalogo):
        cliente = autenticar(administrador)
        creada = cliente.post(
            "/api/recetas/", cuerpo_receta(catalogo), format="json"
        )
        receta_id = creada.data["id"]
        masa_id = creada.data["preparaciones"][0]["id"]

        nueva = cliente.post(
            f"/api/recetas/{receta_id}/preparaciones/",
            {"nombre": "Salsa", "ingredientes": [], "pasos": []},
            format="json",
        )
        salsa_id = nueva.data["id"]

        respuesta = cliente.post(
            f"/api/recetas/{receta_id}/preparaciones/reordenar/",
            {"ids_en_orden": [salsa_id, masa_id]},
            format="json",
        )
        assert respuesta.status_code == 204

        recuperada = cliente.get(f"/api/recetas/{receta_id}/")
        assert recuperada.data["preparaciones"][0]["nombre"] == "Salsa"

    def test_reordenar_pasos(self, administrador, catalogo):
        cliente = autenticar(administrador)
        creada = cliente.post(
            "/api/recetas/", cuerpo_receta(catalogo), format="json"
        )
        receta_id = creada.data["id"]
        preparacion = creada.data["preparaciones"][0]
        primero, segundo = [p["id"] for p in preparacion["pasos"]]

        respuesta = cliente.post(
            f"/api/recetas/{receta_id}/preparaciones/{preparacion['id']}/pasos/reordenar/",
            {"ids_en_orden": [segundo, primero]},
            format="json",
        )
        assert respuesta.status_code == 204

        recuperada = cliente.get(f"/api/recetas/{receta_id}/")
        assert recuperada.data["preparaciones"][0]["pasos"][0]["id"] == segundo


class TestClasificacionApi:
    """RF-027 y RF-028: asignar y quitar categorias y etiquetas."""

    def test_asignar_y_quitar_categoria(self, administrador, catalogo):
        cliente = autenticar(administrador)
        categoria = cliente.post(
            "/api/categorias/", {"nombre": "Panaderia"}, format="json"
        )
        creada = cliente.post(
            "/api/recetas/", cuerpo_receta(catalogo), format="json"
        )
        receta_id = creada.data["id"]
        ruta = f"/api/recetas/{receta_id}/categorias/{categoria.data['id']}/"

        assert cliente.post(ruta).status_code == 204
        assert len(cliente.get(f"/api/recetas/{receta_id}/").data["categorias_ids"]) == 1

        assert cliente.delete(ruta).status_code == 204
        assert cliente.get(f"/api/recetas/{receta_id}/").data["categorias_ids"] == []

    def test_categoria_inexistente_devuelve_404(self, administrador, catalogo):
        cliente = autenticar(administrador)
        creada = cliente.post(
            "/api/recetas/", cuerpo_receta(catalogo), format="json"
        )
        respuesta = cliente.post(
            f"/api/recetas/{creada.data['id']}/categorias/"
            "00000000-0000-0000-0000-000000000000/"
        )
        assert respuesta.status_code == 404


class TestModificarIngredienteApi:
    """RF-017: cambiar cantidad, unidad y tipo de escalado."""

    def test_cambiar_la_cantidad(self, administrador, catalogo):
        cliente = autenticar(administrador)
        creada = cliente.post(
            "/api/recetas/", cuerpo_receta(catalogo), format="json"
        )
        receta_id = creada.data["id"]
        preparacion = creada.data["preparaciones"][0]
        harina = preparacion["ingredientes"][0]

        respuesta = cliente.patch(
            f"/api/recetas/{receta_id}/preparaciones/{preparacion['id']}/"
            f"ingredientes/{harina['ingrediente_preparacion_id']}/",
            {"cantidad": "750", "unidad": "g"},
            format="json",
        )
        assert respuesta.status_code == 204

        recuperada = cliente.get(f"/api/recetas/{receta_id}/")
        actualizado = recuperada.data["preparaciones"][0]["ingredientes"][0]
        assert actualizado["texto_cantidad"] == "750 g"

    def test_pasar_a_a_gusto_descarta_la_cantidad(self, administrador, catalogo):
        """Decision D-1: los tipos sin cantidad no pueden conservarla."""
        cliente = autenticar(administrador)
        creada = cliente.post(
            "/api/recetas/", cuerpo_receta(catalogo), format="json"
        )
        receta_id = creada.data["id"]
        preparacion = creada.data["preparaciones"][0]
        harina = preparacion["ingredientes"][0]

        cliente.patch(
            f"/api/recetas/{receta_id}/preparaciones/{preparacion['id']}/"
            f"ingredientes/{harina['ingrediente_preparacion_id']}/",
            {"tipo_escalado": "a_gusto"},
            format="json",
        )

        recuperada = cliente.get(f"/api/recetas/{receta_id}/")
        actualizado = recuperada.data["preparaciones"][0]["ingredientes"][0]
        assert actualizado["cantidad"] is None
        assert actualizado["texto_cantidad"] == "a gusto"


class TestDuplicarApi:
    """RF-010: variantes independientes de la original."""

    def test_duplicar_crea_una_receta_nueva(self, familiar, catalogo):
        cliente = autenticar(familiar)
        creada = cliente.post(
            "/api/recetas/", cuerpo_receta(catalogo), format="json"
        )
        respuesta = cliente.post(
            f"/api/recetas/{creada.data['id']}/duplicar/",
            {"nombre": "Pan de centeno"},
            format="json",
        )
        assert respuesta.status_code == 201
        assert respuesta.data["id"] != creada.data["id"]
        assert len(respuesta.data["preparaciones"][0]["ingredientes"]) == 2

    def test_duplicar_con_nombre_existente_devuelve_409(self, familiar, catalogo):
        cliente = autenticar(familiar)
        creada = cliente.post(
            "/api/recetas/", cuerpo_receta(catalogo), format="json"
        )
        respuesta = cliente.post(
            f"/api/recetas/{creada.data['id']}/duplicar/",
            {"nombre": "Pan casero"},
            format="json",
        )
        assert respuesta.status_code == 409


class TestNotasApi:
    """RF-025 y RF-026: notas permanentes."""

    def test_agregar_editar_y_eliminar(self, administrador, catalogo):
        cliente = autenticar(administrador)
        creada = cliente.post(
            "/api/recetas/", cuerpo_receta(catalogo), format="json"
        )
        receta_id = creada.data["id"]

        nota = cliente.post(
            f"/api/recetas/{receta_id}/notas/",
            {"texto": "Queda mejor con harina integral."},
            format="json",
        )
        assert nota.status_code == 201

        assert (
            cliente.patch(
                f"/api/recetas/{receta_id}/notas/{nota.data['id']}/",
                {"texto": "Usar harina integral y mas agua."},
                format="json",
            ).status_code
            == 204
        )
        recuperada = cliente.get(f"/api/recetas/{receta_id}/")
        assert recuperada.data["notas"][0]["texto"] == "Usar harina integral y mas agua."

        assert (
            cliente.delete(
                f"/api/recetas/{receta_id}/notas/{nota.data['id']}/"
            ).status_code
            == 204
        )
        assert cliente.get(f"/api/recetas/{receta_id}/").data["notas"] == []


class TestPermisosEdicionRecetaApi:
    """Decision D-20: crear una Receta es libre; editarla es del Administrador.

    Se separa asi para que ningun integrante pueda alterar sin querer una
    receta que cargo otra persona. Duplicar cuenta como crear -genera una
    copia independiente (RN-004)- y marcar favorita es una preferencia
    personal, asi que ambas siguen abiertas a cualquier usuario activo.
    """

    def test_familiar_crea_recetas(self, familiar, catalogo):
        respuesta = autenticar(familiar).post(
            "/api/recetas/", cuerpo_receta(catalogo), format="json"
        )
        assert respuesta.status_code == 201

    def test_familiar_duplica_recetas(self, administrador, familiar, catalogo):
        original = autenticar(administrador).post(
            "/api/recetas/", cuerpo_receta(catalogo), format="json"
        )
        respuesta = autenticar(familiar).post(
            f"/api/recetas/{original.data['id']}/duplicar/",
            {"nombre": "Variante de la familia"},
            format="json",
        )
        assert respuesta.status_code == 201

    def test_familiar_marca_favorita(self, administrador, familiar, catalogo):
        creada = autenticar(administrador).post(
            "/api/recetas/", cuerpo_receta(catalogo), format="json"
        )
        respuesta = autenticar(familiar).post(
            f"/api/recetas/{creada.data['id']}/favorita/",
            {"favorita": True},
            format="json",
        )
        assert respuesta.status_code == 204

    def test_familiar_no_edita_datos_generales(self, administrador, familiar, catalogo):
        creada = autenticar(administrador).post(
            "/api/recetas/", cuerpo_receta(catalogo), format="json"
        )
        respuesta = autenticar(familiar).patch(
            f"/api/recetas/{creada.data['id']}/",
            {"nombre": "Otro nombre"},
            format="json",
        )
        assert respuesta.status_code == 403

    def test_familiar_no_archiva(self, administrador, familiar, catalogo):
        creada = autenticar(administrador).post(
            "/api/recetas/", cuerpo_receta(catalogo), format="json"
        )
        respuesta = autenticar(familiar).post(
            f"/api/recetas/{creada.data['id']}/archivar/"
        )
        assert respuesta.status_code == 403

    def test_familiar_no_agrega_preparaciones(
        self, administrador, familiar, catalogo
    ):
        creada = autenticar(administrador).post(
            "/api/recetas/", cuerpo_receta(catalogo), format="json"
        )
        respuesta = autenticar(familiar).post(
            f"/api/recetas/{creada.data['id']}/preparaciones/",
            {"nombre": "Salsa", "ingredientes": [], "pasos": []},
            format="json",
        )
        assert respuesta.status_code == 403

    def test_familiar_no_agrega_fotografias(
        self, administrador, familiar, catalogo
    ):
        creada = autenticar(administrador).post(
            "/api/recetas/", cuerpo_receta(catalogo), format="json"
        )
        preparacion_id = creada.data["preparaciones"][0]["id"]
        respuesta = autenticar(familiar).post(
            f"/api/recetas/{creada.data['id']}/preparaciones/{preparacion_id}/"
            "fotografias/",
            {"ruta": "https://cdn.test/final.jpg", "tipo": "final"},
            format="json",
        )
        assert respuesta.status_code == 403

    def test_familiar_no_agrega_notas(self, administrador, familiar, catalogo):
        creada = autenticar(administrador).post(
            "/api/recetas/", cuerpo_receta(catalogo), format="json"
        )
        respuesta = autenticar(familiar).post(
            f"/api/recetas/{creada.data['id']}/notas/",
            {"texto": "Una nota"},
            format="json",
        )
        assert respuesta.status_code == 403

    def test_familiar_no_asigna_categorias(
        self, administrador, familiar, catalogo
    ):
        cliente_admin = autenticar(administrador)
        categoria = cliente_admin.post(
            "/api/categorias/", {"nombre": "Panaderia"}, format="json"
        )
        creada = cliente_admin.post(
            "/api/recetas/", cuerpo_receta(catalogo), format="json"
        )
        respuesta = autenticar(familiar).post(
            f"/api/recetas/{creada.data['id']}/categorias/{categoria.data['id']}/"
        )
        assert respuesta.status_code == 403

    def test_administrador_edita_una_receta_de_otro_usuario(
        self, administrador, familiar, catalogo
    ):
        """El recetario es compartido: el admin no necesita ser el autor."""
        creada = autenticar(familiar).post(
            "/api/recetas/", cuerpo_receta(catalogo), format="json"
        )
        respuesta = autenticar(administrador).patch(
            f"/api/recetas/{creada.data['id']}/",
            {"nombre": "Corregido por el administrador"},
            format="json",
        )
        assert respuesta.status_code == 200
