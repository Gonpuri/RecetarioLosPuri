"""Pruebas de integracion del Escalado, la Lista de Compras, la busqueda y
los permisos.

Incluye el flujo completo del Capitulo 6.8, que constituye el recorrido
principal del sistema.
"""

from decimal import Decimal
from uuid import uuid4

import pytest

from sgrf.aplicacion.casos_uso import (
    ArchivarReceta,
    AsignarClasificacion,
    BuscarRecetas,
    CrearReceta,
    EscalarReceta,
    GenerarListaCompras,
    GestionarCatalogoIngredientes,
    GestionarCategorias,
    GestionarFuentes,
    GestionarPreparaciones,
    GestionarUsuarios,
    ListarRecetas,
    MarcarFavorita,
)
from sgrf.aplicacion.dto import (
    ComandoBuscarRecetas,
    ComandoCrearReceta,
    ComandoEscalarReceta,
    ComandoGenerarListaCompras,
    DatosIngrediente,
    DatosPreparacion,
)
from sgrf.aplicacion.excepciones import (
    ConflictoDeDatos,
    PermisoDenegado,
    RecursoNoEncontrado,
)


class TestEscalarReceta:
    """CU-013: escalado sin persistencia (RF-031 y RF-032)."""

    def test_duplica_los_ingredientes_lineales(self, uow, familiar, receta_creada):
        comando = ComandoEscalarReceta(
            solicitante_id=familiar.id,
            receta_id=receta_creada.id,
            rendimiento_objetivo=Decimal("8"),
        )
        resultado = EscalarReceta(uow).ejecutar(comando)
        harina = self._buscar(resultado, "lineal")
        assert resultado.factor == Decimal("2")
        assert harina.cantidad == Decimal("1000")

    def test_conserva_los_ingredientes_fijos(self, uow, familiar, receta_creada):
        comando = ComandoEscalarReceta(
            solicitante_id=familiar.id,
            receta_id=receta_creada.id,
            rendimiento_objetivo=Decimal("8"),
        )
        resultado = EscalarReceta(uow).ejecutar(comando)
        assert self._buscar(resultado, "fijo").cantidad == Decimal("10")

    def test_no_persiste_nada(self, uow, familiar, receta_creada):
        """ADR-003: escalar no guarda datos."""
        confirmaciones_previas = uow.confirmaciones
        comando = ComandoEscalarReceta(
            solicitante_id=familiar.id,
            receta_id=receta_creada.id,
            rendimiento_objetivo=Decimal("20"),
        )
        EscalarReceta(uow).ejecutar(comando)
        assert uow.confirmaciones == confirmaciones_previas

    def test_la_receta_almacenada_no_cambia(self, uow, familiar, receta_creada):
        """RN-004: la receta base permanece intacta tras escalar."""
        comando = ComandoEscalarReceta(
            solicitante_id=familiar.id,
            receta_id=receta_creada.id,
            rendimiento_objetivo=Decimal("100"),
        )
        EscalarReceta(uow).ejecutar(comando)
        almacenada = uow.recetas.obtener(receta_creada.id)
        assert almacenada.rendimiento_base.valor == Decimal("4")
        assert almacenada.preparaciones[0].ingredientes[0].cantidad.valor == Decimal("500")

    def test_receta_archivada_puede_escalarse(self, uow, familiar, receta_creada):
        """Escalar es una lectura: no modifica y por eso no exige restaurar."""
        ArchivarReceta(uow).ejecutar(familiar.id, receta_creada.id)
        comando = ComandoEscalarReceta(
            solicitante_id=familiar.id,
            receta_id=receta_creada.id,
            rendimiento_objetivo=Decimal("8"),
        )
        assert EscalarReceta(uow).ejecutar(comando).factor == Decimal("2")

    @staticmethod
    def _buscar(resultado, tipo_escalado):
        """Localiza el primer ingrediente de un tipo de escalado dado."""
        return next(
            i
            for p in resultado.preparaciones
            for i in p.ingredientes
            if i.tipo_escalado == tipo_escalado
        )


class TestGenerarListaCompras:
    """CU-014: Lista de Compras consolidada (RF-034 y RF-035)."""

    def test_incluye_solo_lo_seleccionado(self, uow, familiar, receta_creada):
        """RN-006."""
        harina = receta_creada.preparaciones[0].ingredientes[0]
        comando = ComandoGenerarListaCompras(
            solicitante_id=familiar.id,
            receta_id=receta_creada.id,
            ingredientes_seleccionados=(harina.ingrediente_preparacion_id,),
        )
        lista = GenerarListaCompras(uow).ejecutar(comando)
        assert len(lista.items) == 1
        assert lista.items[0].nombre == "Harina 000"

    def test_sin_seleccion_la_lista_queda_vacia(self, uow, familiar, receta_creada):
        comando = ComandoGenerarListaCompras(
            solicitante_id=familiar.id,
            receta_id=receta_creada.id,
            ingredientes_seleccionados=(),
        )
        assert GenerarListaCompras(uow).ejecutar(comando).items == ()

    def test_usa_las_cantidades_escaladas(self, uow, familiar, receta_creada):
        harina = receta_creada.preparaciones[0].ingredientes[0]
        comando = ComandoGenerarListaCompras(
            solicitante_id=familiar.id,
            receta_id=receta_creada.id,
            ingredientes_seleccionados=(harina.ingrediente_preparacion_id,),
            rendimiento_objetivo=Decimal("8"),
        )
        lista = GenerarListaCompras(uow).ejecutar(comando)
        assert lista.items[0].texto_cantidad == "1000 g"

    def test_no_persiste_salvo_que_se_solicite(self, uow, familiar, receta_creada):
        harina = receta_creada.preparaciones[0].ingredientes[0]
        comando = ComandoGenerarListaCompras(
            solicitante_id=familiar.id,
            receta_id=receta_creada.id,
            ingredientes_seleccionados=(harina.ingrediente_preparacion_id,),
        )
        GenerarListaCompras(uow).ejecutar(comando)
        assert uow.listas_compra.datos == {}

    def test_persiste_cuando_se_solicita(self, uow, familiar, receta_creada):
        harina = receta_creada.preparaciones[0].ingredientes[0]
        comando = ComandoGenerarListaCompras(
            solicitante_id=familiar.id,
            receta_id=receta_creada.id,
            ingredientes_seleccionados=(harina.ingrediente_preparacion_id,),
            persistir=True,
        )
        lista = GenerarListaCompras(uow).ejecutar(comando)
        assert uow.listas_compra.obtener(lista.id) is not None

    def test_muestra_texto_para_ingredientes_sin_cantidad(
        self, uow, familiar, receta_creada
    ):
        sal = next(
            i
            for i in receta_creada.preparaciones[0].ingredientes
            if i.tipo_escalado == "a_gusto"
        )
        comando = ComandoGenerarListaCompras(
            solicitante_id=familiar.id,
            receta_id=receta_creada.id,
            ingredientes_seleccionados=(sal.ingrediente_preparacion_id,),
        )
        lista = GenerarListaCompras(uow).ejecutar(comando)
        assert lista.items[0].texto_cantidad == "a gusto"


class TestFlujoCompleto:
    """Recorrido principal del Capitulo 6.8."""

    def test_buscar_abrir_escalar_y_generar_lista(self, uow, familiar, receta_creada):
        # 1 y 2: buscar y abrir la receta
        encontradas = BuscarRecetas(uow).ejecutar(
            ComandoBuscarRecetas(solicitante_id=familiar.id, texto="pan")
        )
        assert len(encontradas) == 1

        # 3 y 4: elegir rendimiento y escalar
        escalada = EscalarReceta(uow).ejecutar(
            ComandoEscalarReceta(
                solicitante_id=familiar.id,
                receta_id=encontradas[0].id,
                rendimiento_objetivo=Decimal("12"),
            )
        )
        assert escalada.factor == Decimal("3")

        # 5 y 6: marcar faltantes y generar la lista
        faltantes = tuple(
            i.ingrediente_preparacion_id
            for p in escalada.preparaciones
            for i in p.ingredientes
            if i.tipo_escalado == "lineal"
        )
        lista = GenerarListaCompras(uow).ejecutar(
            ComandoGenerarListaCompras(
                solicitante_id=familiar.id,
                receta_id=encontradas[0].id,
                ingredientes_seleccionados=faltantes,
                rendimiento_objetivo=Decimal("12"),
            )
        )
        assert lista.items[0].texto_cantidad == "1500 g"

        # La receta base sigue intacta tras todo el recorrido
        almacenada = uow.recetas.obtener(encontradas[0].id)
        assert almacenada.rendimiento_base.valor == Decimal("4")


class TestBusqueda:
    """CU-022: busquedas por los criterios del negocio (RF-038 a RF-043)."""

    def test_busca_por_nombre(self, uow, familiar, receta_creada):
        comando = ComandoBuscarRecetas(solicitante_id=familiar.id, texto="PAN")
        assert len(BuscarRecetas(uow).ejecutar(comando)) == 1

    def test_busca_por_ingrediente(self, uow, familiar, receta_creada, harina):
        comando = ComandoBuscarRecetas(
            solicitante_id=familiar.id, ingrediente_id=harina.id
        )
        assert len(BuscarRecetas(uow).ejecutar(comando)) == 1

    def test_excluye_archivadas_por_defecto(self, uow, familiar, receta_creada):
        """Criterio de aceptacion 4.12."""
        ArchivarReceta(uow).ejecutar(familiar.id, receta_creada.id)
        comando = ComandoBuscarRecetas(solicitante_id=familiar.id, texto="pan")
        assert BuscarRecetas(uow).ejecutar(comando) == []

    def test_incluye_archivadas_si_se_pide(self, uow, familiar, receta_creada):
        ArchivarReceta(uow).ejecutar(familiar.id, receta_creada.id)
        comando = ComandoBuscarRecetas(
            solicitante_id=familiar.id, texto="pan", incluir_archivadas=True
        )
        assert len(BuscarRecetas(uow).ejecutar(comando)) == 1

    def test_filtra_favoritas(self, uow, familiar, receta_creada):
        comando = ComandoBuscarRecetas(
            solicitante_id=familiar.id, solo_favoritas=True
        )
        assert BuscarRecetas(uow).ejecutar(comando) == []
        MarcarFavorita(uow).ejecutar(familiar.id, receta_creada.id)
        assert len(BuscarRecetas(uow).ejecutar(comando)) == 1

    def test_busca_por_categoria(self, uow, familiar, receta_creada, categoria):
        AsignarClasificacion(uow).asignar_categoria(
            familiar.id, receta_creada.id, categoria.id
        )
        comando = ComandoBuscarRecetas(
            solicitante_id=familiar.id, categoria_id=categoria.id
        )
        assert len(BuscarRecetas(uow).ejecutar(comando)) == 1

    def test_listar_devuelve_orden_alfabetico(self, uow, familiar, receta_creada, comando_pan):
        segunda = ComandoCrearReceta(
            solicitante_id=familiar.id,
            nombre="Alfajores",
            rendimiento_base=Decimal("12"),
            fuente_id=comando_pan.fuente_id,
            preparaciones=comando_pan.preparaciones,
        )
        CrearReceta(uow).ejecutar(segunda)
        nombres = [r.nombre for r in ListarRecetas(uow).ejecutar(familiar.id)]
        assert nombres == ["Alfajores", "Pan casero"]


class TestPermisos:
    """Capitulo 1.7 y decision D-9: separacion de perfiles."""

    def test_familiar_no_administra_usuarios(self, uow, familiar):
        with pytest.raises(PermisoDenegado):
            GestionarUsuarios(uow).registrar(
                familiar.id, "Nuevo", "nuevo@familia.test"
            )

    def test_administrador_registra_usuarios(self, uow, administrador):
        resultado = GestionarUsuarios(uow).registrar(
            administrador.id, "Nuevo", "nuevo@familia.test"
        )
        assert resultado.rol == "usuario_familiar"

    def test_no_se_repite_el_correo(self, uow, administrador, familiar):
        with pytest.raises(ConflictoDeDatos):
            GestionarUsuarios(uow).registrar(
                administrador.id, "Otra Ana", familiar.correo
            )

    def test_desactivar_conserva_el_usuario(self, uow, administrador, familiar):
        GestionarUsuarios(uow).desactivar(administrador.id, familiar.id)
        assert uow.usuarios.obtener(familiar.id) is not None
        assert not uow.usuarios.obtener(familiar.id).activo

    def test_administrador_no_se_autodesactiva(self, uow, administrador):
        with pytest.raises(ConflictoDeDatos):
            GestionarUsuarios(uow).desactivar(administrador.id, administrador.id)

    def test_familiar_crea_ingredientes(self, uow, familiar):
        """Decision D-19: cualquier usuario activo puede sumar un ingrediente."""
        identidad = GestionarCatalogoIngredientes(uow).crear(familiar.id, "Azucar")
        assert uow.ingredientes.obtener(identidad) is not None

    def test_administrador_crea_ingredientes(self, uow, administrador):
        identidad = GestionarCatalogoIngredientes(uow).crear(
            administrador.id, "Azucar"
        )
        assert uow.ingredientes.obtener(identidad) is not None

    def test_familiar_no_crea_categorias(self, uow, familiar):
        """Categorias, Etiquetas y Fuentes siguen reservadas al Administrador."""
        with pytest.raises(PermisoDenegado):
            GestionarCategorias(uow).crear(familiar.id, "Panaderia")

    def test_familiar_no_crea_fuentes(self, uow, familiar):
        with pytest.raises(PermisoDenegado):
            GestionarFuentes(uow).crear(familiar.id, "Internet")

    def test_no_se_duplican_ingredientes(self, uow, administrador, harina):
        with pytest.raises(ConflictoDeDatos):
            GestionarCatalogoIngredientes(uow).crear(administrador.id, "Harina 000")

    def test_familiar_edita_recetas_de_otros(self, uow, administrador, receta_creada):
        """El recetario es compartido (Capitulo 1.5)."""
        GestionarPreparaciones(uow).agregar(
            administrador.id,
            receta_creada.id,
            DatosPreparacion(nombre="Cobertura", pasos=("Pincelar.",)),
        )
        assert len(uow.recetas.obtener(receta_creada.id).preparaciones) == 2

    def test_cualquier_usuario_activo_consulta_el_catalogo(self, uow, familiar, harina):
        assert GestionarCatalogoIngredientes(uow).listar(familiar.id) != []


class TestGestionarPreparaciones:
    """CU-008: alta, baja y reordenamiento de Preparaciones."""

    def test_agregar_preparacion(self, uow, familiar, receta_creada):
        GestionarPreparaciones(uow).agregar(
            familiar.id,
            receta_creada.id,
            DatosPreparacion(nombre="Salsa", pasos=("Reducir.",)),
        )
        assert len(uow.recetas.obtener(receta_creada.id).preparaciones) == 2

    def test_no_se_elimina_la_ultima_preparacion(self, uow, familiar, receta_creada):
        """RN-003."""
        from sgrf.dominio.excepciones import ReglaDeNegocioViolada

        preparacion_id = receta_creada.preparaciones[0].id
        with pytest.raises(ReglaDeNegocioViolada):
            GestionarPreparaciones(uow).eliminar(
                familiar.id, receta_creada.id, preparacion_id
            )

    def test_reordenar_preparaciones(self, uow, familiar, receta_creada):
        nueva_id = GestionarPreparaciones(uow).agregar(
            familiar.id,
            receta_creada.id,
            DatosPreparacion(nombre="Salsa", pasos=("Reducir.",)),
        )
        masa_id = receta_creada.preparaciones[0].id
        GestionarPreparaciones(uow).reordenar(
            familiar.id, receta_creada.id, [nueva_id, masa_id]
        )
        almacenada = uow.recetas.obtener(receta_creada.id)
        assert almacenada.preparaciones_ordenadas[0].nombre == "Salsa"

    def test_preparacion_inexistente_falla(self, uow, familiar, receta_creada):
        from sgrf.dominio.excepciones import ElementoNoEncontrado

        with pytest.raises(ElementoNoEncontrado):
            GestionarPreparaciones(uow).renombrar(
                familiar.id, receta_creada.id, uuid4(), "Otro"
            )
