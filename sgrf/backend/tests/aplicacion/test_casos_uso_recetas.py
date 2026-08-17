"""Pruebas de integracion de los Casos de Uso de Recetas."""

from decimal import Decimal
from uuid import uuid4

import pytest

from sgrf.aplicacion.casos_uso import (
    ArchivarReceta,
    ConsultarReceta,
    CrearReceta,
    DuplicarReceta,
    EditarReceta,
    MarcarFavorita,
    RestaurarReceta,
)
from sgrf.aplicacion.dto import (
    ComandoCrearReceta,
    ComandoEditarReceta,
    DatosIngrediente,
    DatosPreparacion,
)
from sgrf.aplicacion.excepciones import (
    ConflictoDeDatos,
    PermisoDenegado,
    RecursoNoEncontrado,
    UsuarioInactivo,
)
from sgrf.dominio.excepciones import RecetaArchivada, ReglaDeNegocioViolada


class TestCrearReceta:
    """CU-001: alta de Recetas (RF-005)."""

    def test_crea_receta_con_preparaciones_e_ingredientes(self, uow, comando_pan):
        resultado = CrearReceta(uow).ejecutar(comando_pan)
        assert resultado.nombre == "Pan casero"
        assert len(resultado.preparaciones) == 1
        assert len(resultado.preparaciones[0].ingredientes) == 3

    def test_persiste_la_receta(self, uow, comando_pan):
        resultado = CrearReceta(uow).ejecutar(comando_pan)
        assert uow.recetas.obtener(resultado.id) is not None

    def test_confirma_la_transaccion(self, uow, comando_pan):
        CrearReceta(uow).ejecutar(comando_pan)
        assert uow.confirmaciones == 1

    def test_resuelve_los_nombres_del_catalogo(self, uow, comando_pan):
        resultado = CrearReceta(uow).ejecutar(comando_pan)
        nombres = {i.nombre for i in resultado.preparaciones[0].ingredientes}
        assert "Harina 000" in nombres

    def test_muestra_texto_para_ingredientes_a_gusto(self, uow, comando_pan):
        resultado = CrearReceta(uow).ejecutar(comando_pan)
        sal = next(
            i
            for i in resultado.preparaciones[0].ingredientes
            if i.tipo_escalado == "a_gusto"
        )
        assert sal.texto_cantidad == "a gusto"
        assert sal.cantidad is None

    def test_rechaza_fuente_inexistente(self, uow, comando_pan):
        comando = ComandoCrearReceta(
            solicitante_id=comando_pan.solicitante_id,
            nombre="Otra receta",
            rendimiento_base=Decimal("4"),
            fuente_id=uuid4(),
            preparaciones=comando_pan.preparaciones,
        )
        with pytest.raises(RecursoNoEncontrado):
            CrearReceta(uow).ejecutar(comando)

    def test_rechaza_nombre_duplicado(self, uow, comando_pan):
        CrearReceta(uow).ejecutar(comando_pan)
        with pytest.raises(ConflictoDeDatos):
            CrearReceta(uow).ejecutar(comando_pan)

    def test_rechaza_receta_sin_preparaciones(self, uow, familiar, fuente):
        """RN-003 se verifica antes de persistir."""
        comando = ComandoCrearReceta(
            solicitante_id=familiar.id,
            nombre="Receta vacia",
            rendimiento_base=Decimal("4"),
            fuente_id=fuente.id,
        )
        with pytest.raises(ReglaDeNegocioViolada):
            CrearReceta(uow).ejecutar(comando)

    def test_no_persiste_si_la_validacion_falla(self, uow, familiar, fuente):
        comando = ComandoCrearReceta(
            solicitante_id=familiar.id,
            nombre="Receta vacia",
            rendimiento_base=Decimal("4"),
            fuente_id=fuente.id,
        )
        with pytest.raises(ReglaDeNegocioViolada):
            CrearReceta(uow).ejecutar(comando)
        assert uow.recetas.listar_todas() == []
        assert uow.confirmaciones == 0

    def test_usuario_inactivo_no_puede_crear(
        self, uow, familiar_inactivo, fuente, harina
    ):
        comando = ComandoCrearReceta(
            solicitante_id=familiar_inactivo.id,
            nombre="Prohibida",
            rendimiento_base=Decimal("4"),
            fuente_id=fuente.id,
            preparaciones=(
                DatosPreparacion(
                    nombre="Masa",
                    ingredientes=(
                        DatosIngrediente(
                            ingrediente_id=harina.id,
                            cantidad=Decimal("100"),
                            unidad="g",
                        ),
                    ),
                    pasos=("Mezclar.",),
                ),
            ),
        )
        with pytest.raises(UsuarioInactivo):
            CrearReceta(uow).ejecutar(comando)

    def test_solicitante_inexistente_falla(self, uow, comando_pan):
        comando = ComandoCrearReceta(
            solicitante_id=uuid4(),
            nombre=comando_pan.nombre,
            rendimiento_base=comando_pan.rendimiento_base,
            fuente_id=comando_pan.fuente_id,
            preparaciones=comando_pan.preparaciones,
        )
        with pytest.raises(RecursoNoEncontrado):
            CrearReceta(uow).ejecutar(comando)


class TestConsultarReceta:
    """CU-002: consulta de una Receta completa (RF-007)."""

    def test_devuelve_la_receta_con_su_fuente(self, uow, familiar, receta_creada, fuente):
        resultado = ConsultarReceta(uow).ejecutar(familiar.id, receta_creada.id)
        assert resultado.fuente_nombre == fuente.nombre

    def test_receta_inexistente_falla(self, uow, familiar):
        with pytest.raises(RecursoNoEncontrado):
            ConsultarReceta(uow).ejecutar(familiar.id, uuid4())

    def test_los_pasos_llegan_ordenados(self, uow, familiar, receta_creada):
        resultado = ConsultarReceta(uow).ejecutar(familiar.id, receta_creada.id)
        ordenes = [p.orden for p in resultado.preparaciones[0].pasos]
        assert ordenes == [1, 2]


class TestEditarReceta:
    """CU-003: edicion de datos generales (RF-006). Requiere Administrador (D-20)."""

    def test_cambia_el_nombre(self, uow, administrador, receta_creada):
        comando = ComandoEditarReceta(
            solicitante_id=administrador.id,
            receta_id=receta_creada.id,
            nombre="Pan integral",
        )
        assert EditarReceta(uow).ejecutar(comando).nombre == "Pan integral"

    def test_cambia_el_rendimiento_base(self, uow, administrador, receta_creada):
        comando = ComandoEditarReceta(
            solicitante_id=administrador.id,
            receta_id=receta_creada.id,
            rendimiento_base=Decimal("6"),
        )
        resultado = EditarReceta(uow).ejecutar(comando)
        assert resultado.rendimiento_base == Decimal("6")
        assert resultado.rendimiento_descripcion == "porciones"

    def test_rechaza_nombre_de_otra_receta(
        self, uow, administrador, receta_creada, comando_pan
    ):
        segunda = ComandoCrearReceta(
            solicitante_id=administrador.id,
            nombre="Focaccia",
            rendimiento_base=Decimal("4"),
            fuente_id=comando_pan.fuente_id,
            preparaciones=comando_pan.preparaciones,
        )
        creada = CrearReceta(uow).ejecutar(segunda)
        comando = ComandoEditarReceta(
            solicitante_id=administrador.id,
            receta_id=creada.id,
            nombre="Pan casero",
        )
        with pytest.raises(ConflictoDeDatos):
            EditarReceta(uow).ejecutar(comando)

    def test_permite_conservar_su_propio_nombre(self, uow, administrador, receta_creada):
        comando = ComandoEditarReceta(
            solicitante_id=administrador.id,
            receta_id=receta_creada.id,
            nombre="Pan casero",
            descripcion="Actualizada.",
        )
        assert EditarReceta(uow).ejecutar(comando).descripcion == "Actualizada."

    def test_familiar_no_puede_editar(self, uow, familiar, receta_creada):
        """Decision D-20: editar una receta existente es solo del Administrador."""
        comando = ComandoEditarReceta(
            solicitante_id=familiar.id,
            receta_id=receta_creada.id,
            nombre="Intento no autorizado",
        )
        with pytest.raises(PermisoDenegado):
            EditarReceta(uow).ejecutar(comando)

    def test_administrador_edita_receta_de_otro_usuario(
        self, uow, administrador, familiar, comando_pan
    ):
        """El recetario es compartido: el admin no necesita ser el autor."""
        comando_familiar = ComandoCrearReceta(
            solicitante_id=familiar.id,
            nombre=comando_pan.nombre,
            rendimiento_base=comando_pan.rendimiento_base,
            fuente_id=comando_pan.fuente_id,
            preparaciones=comando_pan.preparaciones,
        )
        creada = CrearReceta(uow).ejecutar(comando_familiar)
        comando = ComandoEditarReceta(
            solicitante_id=administrador.id,
            receta_id=creada.id,
            nombre="Corregido por el administrador",
        )
        assert (
            EditarReceta(uow).ejecutar(comando).nombre
            == "Corregido por el administrador"
        )


class TestArchivadoYRestauracion:
    """CU-004 y CU-005: archivado logico (RF-008 y RF-009). Solo Administrador."""

    def test_archivar_no_elimina(self, uow, administrador, receta_creada):
        ArchivarReceta(uow).ejecutar(administrador.id, receta_creada.id)
        assert uow.recetas.obtener(receta_creada.id).archivada

    def test_receta_archivada_no_se_edita(self, uow, administrador, receta_creada):
        ArchivarReceta(uow).ejecutar(administrador.id, receta_creada.id)
        comando = ComandoEditarReceta(
            solicitante_id=administrador.id,
            receta_id=receta_creada.id,
            nombre="Nuevo nombre",
        )
        with pytest.raises(RecetaArchivada):
            EditarReceta(uow).ejecutar(comando)

    def test_restaurar_habilita_la_edicion(self, uow, administrador, receta_creada):
        ArchivarReceta(uow).ejecutar(administrador.id, receta_creada.id)
        RestaurarReceta(uow).ejecutar(administrador.id, receta_creada.id)
        comando = ComandoEditarReceta(
            solicitante_id=administrador.id,
            receta_id=receta_creada.id,
            nombre="Pan de campo",
        )
        assert EditarReceta(uow).ejecutar(comando).nombre == "Pan de campo"

    def test_familiar_no_archiva(self, uow, familiar, receta_creada):
        with pytest.raises(PermisoDenegado):
            ArchivarReceta(uow).ejecutar(familiar.id, receta_creada.id)

    def test_familiar_no_restaura(self, uow, administrador, familiar, receta_creada):
        ArchivarReceta(uow).ejecutar(administrador.id, receta_creada.id)
        with pytest.raises(PermisoDenegado):
            RestaurarReceta(uow).ejecutar(familiar.id, receta_creada.id)


class TestDuplicarReceta:
    """CU-006: variantes de una Receta (RF-010)."""

    def test_crea_una_receta_independiente(self, uow, familiar, receta_creada):
        variante = DuplicarReceta(uow).ejecutar(
            familiar.id, receta_creada.id, "Pan de centeno"
        )
        assert variante.id != receta_creada.id
        assert variante.nombre == "Pan de centeno"

    def test_copia_preparaciones_e_ingredientes(self, uow, familiar, receta_creada):
        variante = DuplicarReceta(uow).ejecutar(
            familiar.id, receta_creada.id, "Pan de centeno"
        )
        assert len(variante.preparaciones) == 1
        assert len(variante.preparaciones[0].ingredientes) == 3

    def test_la_copia_no_comparte_identidades(self, uow, familiar, receta_creada):
        """RN-004: editar la variante no puede afectar el original."""
        variante = DuplicarReceta(uow).ejecutar(
            familiar.id, receta_creada.id, "Pan de centeno"
        )
        ids_original = {p.id for p in receta_creada.preparaciones}
        ids_variante = {p.id for p in variante.preparaciones}
        assert ids_original.isdisjoint(ids_variante)

    def test_editar_la_variante_no_altera_el_original(
        self, uow, familiar, receta_creada
    ):
        variante = DuplicarReceta(uow).ejecutar(
            familiar.id, receta_creada.id, "Pan de centeno"
        )
        original = uow.recetas.obtener(receta_creada.id)
        copia = uow.recetas.obtener(variante.id)
        copia.preparaciones[0].agregar_paso("Paso extra de la variante.")
        assert len(original.preparaciones[0].pasos) == 2
        assert len(copia.preparaciones[0].pasos) == 3

    def test_rechaza_nombre_duplicado(self, uow, familiar, receta_creada):
        with pytest.raises(ConflictoDeDatos):
            DuplicarReceta(uow).ejecutar(
                familiar.id, receta_creada.id, "Pan casero"
            )


class TestFavoritas:
    """CU-007: marcado de favoritas (RF-043)."""

    def test_marcar_y_desmarcar(self, uow, familiar, receta_creada):
        MarcarFavorita(uow).ejecutar(familiar.id, receta_creada.id, True)
        assert uow.recetas.obtener(receta_creada.id).favorita
        MarcarFavorita(uow).ejecutar(familiar.id, receta_creada.id, False)
        assert not uow.recetas.obtener(receta_creada.id).favorita
