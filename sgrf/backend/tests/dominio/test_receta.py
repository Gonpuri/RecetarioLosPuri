"""Pruebas unitarias del agregado Receta y sus reglas de negocio."""

from uuid import uuid4

import pytest

from sgrf.dominio.entidades import (
    Fotografia,
    IngredientePreparacion,
    Nota,
    Preparacion,
    Receta,
    TipoFotografia,
)
from sgrf.dominio.excepciones import (
    ElementoNoEncontrado,
    RecetaArchivada,
    ReglaDeNegocioViolada,
    ValorInvalido,
)
from sgrf.dominio.objetos_valor import Cantidad, Rendimiento, TipoEscalado, Unidad


class TestCreacionDeReceta:
    """RN-001 y RN-002: rendimiento base y fuente obligatorios."""

    def test_receta_valida_se_crea(self, receta):
        assert receta.nombre == "Pan casero"
        assert receta.rendimiento_base.valor == 4
        assert len(receta.preparaciones) == 1

    def test_nombre_vacio_falla(self, fuente):
        with pytest.raises(ValorInvalido):
            Receta(
                nombre="   ",
                rendimiento_base=Rendimiento(4),
                fuente_id=fuente.id,
            )

    def test_sin_fuente_falla(self):
        with pytest.raises(ReglaDeNegocioViolada) as error:
            Receta(nombre="Sin fuente", rendimiento_base=Rendimiento(4), fuente_id=None)
        assert error.value.codigo_regla == "RN-002"

    def test_rendimiento_base_no_puede_ser_cero(self, fuente):
        with pytest.raises(ValorInvalido):
            Receta(nombre="Nada", rendimiento_base=Rendimiento(0), fuente_id=fuente.id)


class TestPreparaciones:
    """RN-003: toda receta conserva una o mas Preparaciones."""

    def test_agregar_preparacion_asigna_orden_correlativo(self, receta):
        receta.agregar_preparacion(Preparacion(nombre="Salsa"))
        receta.agregar_preparacion(Preparacion(nombre="Armado"))
        assert [p.orden for p in receta.preparaciones_ordenadas] == [1, 2, 3]

    def test_no_se_puede_quitar_la_ultima_preparacion(self, receta):
        with pytest.raises(ReglaDeNegocioViolada) as error:
            receta.quitar_preparacion(receta.preparaciones[0].id)
        assert error.value.codigo_regla == "RN-003"

    def test_quitar_preparacion_renumera_las_restantes(self, receta):
        salsa = Preparacion(nombre="Salsa")
        armado = Preparacion(nombre="Armado")
        receta.agregar_preparacion(salsa)
        receta.agregar_preparacion(armado)
        receta.quitar_preparacion(salsa.id)
        assert [p.orden for p in receta.preparaciones_ordenadas] == [1, 2]
        assert armado.orden == 2

    def test_reordenar_preparaciones(self, receta):
        salsa = Preparacion(nombre="Salsa")
        receta.agregar_preparacion(salsa)
        masa = receta.preparaciones[0]
        receta.reordenar_preparaciones([salsa.id, masa.id])
        assert receta.preparaciones_ordenadas[0].nombre == "Salsa"
        assert salsa.orden == 1

    def test_reordenar_con_identidades_desconocidas_falla(self, receta):
        with pytest.raises(ValorInvalido):
            receta.reordenar_preparaciones([uuid4()])

    def test_obtener_preparacion_inexistente_falla(self, receta):
        with pytest.raises(ElementoNoEncontrado):
            receta.obtener_preparacion(uuid4())


class TestFotografias:
    """RN-005: maximo dos fotografias de proceso y una final por receta."""

    def test_admite_dos_de_proceso_y_una_final(self, receta):
        preparacion_id = receta.preparaciones[0].id
        receta.agregar_fotografia(preparacion_id, Fotografia("p1.jpg", TipoFotografia.PROCESO))
        receta.agregar_fotografia(preparacion_id, Fotografia("p2.jpg", TipoFotografia.PROCESO))
        receta.agregar_fotografia(preparacion_id, Fotografia("f1.jpg", TipoFotografia.FINAL))
        assert receta.contar_fotografias() == 3

    def test_rechaza_la_tercera_fotografia_de_proceso(self, receta):
        preparacion_id = receta.preparaciones[0].id
        receta.agregar_fotografia(preparacion_id, Fotografia("p1.jpg", TipoFotografia.PROCESO))
        receta.agregar_fotografia(preparacion_id, Fotografia("p2.jpg", TipoFotografia.PROCESO))
        with pytest.raises(ReglaDeNegocioViolada) as error:
            receta.agregar_fotografia(
                preparacion_id, Fotografia("p3.jpg", TipoFotografia.PROCESO)
            )
        assert error.value.codigo_regla == "RN-005"

    def test_rechaza_la_segunda_fotografia_final(self, receta):
        preparacion_id = receta.preparaciones[0].id
        receta.agregar_fotografia(preparacion_id, Fotografia("f1.jpg", TipoFotografia.FINAL))
        with pytest.raises(ReglaDeNegocioViolada):
            receta.agregar_fotografia(
                preparacion_id, Fotografia("f2.jpg", TipoFotografia.FINAL)
            )

    def test_el_limite_es_por_receta_y_no_por_preparacion(self, receta):
        """Dos preparaciones distintas no pueden sumar tres fotos de proceso."""
        salsa = Preparacion(nombre="Salsa")
        receta.agregar_preparacion(salsa)
        masa_id = receta.preparaciones[0].id
        receta.agregar_fotografia(masa_id, Fotografia("p1.jpg", TipoFotografia.PROCESO))
        receta.agregar_fotografia(salsa.id, Fotografia("p2.jpg", TipoFotografia.PROCESO))
        with pytest.raises(ReglaDeNegocioViolada):
            receta.agregar_fotografia(salsa.id, Fotografia("p3.jpg", TipoFotografia.PROCESO))

    def test_quitar_fotografia_libera_el_cupo(self, receta):
        preparacion_id = receta.preparaciones[0].id
        foto = Fotografia("f1.jpg", TipoFotografia.FINAL)
        receta.agregar_fotografia(preparacion_id, foto)
        receta.quitar_fotografia(preparacion_id, foto.id)
        receta.agregar_fotografia(preparacion_id, Fotografia("f2.jpg", TipoFotografia.FINAL))
        assert receta.contar_fotografias(TipoFotografia.FINAL) == 1


class TestArchivado:
    """RF-008 y RF-009: archivar y restaurar sin eliminar."""

    def test_archivar_no_elimina_la_receta(self, receta):
        receta.archivar()
        assert receta.archivada
        assert receta.nombre == "Pan casero"

    def test_receta_archivada_no_se_modifica(self, receta):
        receta.archivar()
        with pytest.raises(RecetaArchivada):
            receta.actualizar_informacion(nombre="Otro nombre")

    def test_restaurar_habilita_la_edicion(self, receta):
        receta.archivar()
        receta.restaurar()
        receta.actualizar_informacion(nombre="Pan integral")
        assert receta.nombre == "Pan integral"


class TestOrganizacion:
    """RF-027 y RF-028: categorias y etiquetas."""

    def test_asignar_categoria_es_idempotente(self, receta):
        categoria_id = uuid4()
        receta.asignar_categoria(categoria_id)
        receta.asignar_categoria(categoria_id)
        assert len(receta.categorias_ids) == 1

    def test_quitar_etiqueta_inexistente_no_falla(self, receta):
        receta.quitar_etiqueta(uuid4())
        assert receta.etiquetas_ids == set()


class TestNotas:
    """RF-025 y RF-026: notas permanentes."""

    def test_agregar_y_editar_nota(self, receta):
        nota = Nota(texto="Queda mejor con harina integral.")
        receta.agregar_nota(nota)
        nota.editar("Usar harina integral y mas agua.")
        assert receta.notas[0].texto == "Usar harina integral y mas agua."

    def test_nota_vacia_falla(self):
        with pytest.raises(ValorInvalido):
            Nota(texto="   ")


class TestIngredientePreparacion:
    """Coherencia entre TipoEscalado y Cantidad."""

    def test_lineal_sin_cantidad_falla(self):
        with pytest.raises(ReglaDeNegocioViolada):
            IngredientePreparacion(
                ingrediente_id=uuid4(), tipo_escalado=TipoEscalado.LINEAL
            )

    def test_a_gusto_con_cantidad_falla(self):
        with pytest.raises(ReglaDeNegocioViolada):
            IngredientePreparacion(
                ingrediente_id=uuid4(),
                tipo_escalado=TipoEscalado.A_GUSTO,
                cantidad=Cantidad(5, Unidad.GRAMO),
            )

    def test_no_se_repite_el_mismo_ingrediente_en_una_preparacion(self, harina):
        preparacion = Preparacion(nombre="Masa")
        preparacion.agregar_ingrediente(
            IngredientePreparacion(
                ingrediente_id=harina.id, cantidad=Cantidad(100, Unidad.GRAMO)
            )
        )
        with pytest.raises(ValorInvalido):
            preparacion.agregar_ingrediente(
                IngredientePreparacion(
                    ingrediente_id=harina.id, cantidad=Cantidad(50, Unidad.GRAMO)
                )
            )


class TestPasos:
    """RF-019 a RF-022: gestion de pasos ordenados."""

    def test_los_pasos_se_numeran_automaticamente(self, preparacion_masa):
        assert [p.orden for p in preparacion_masa.pasos_ordenados] == [1, 2]

    def test_quitar_paso_renumera(self, preparacion_masa):
        primero = preparacion_masa.pasos[0]
        preparacion_masa.quitar_paso(primero.id)
        assert [p.orden for p in preparacion_masa.pasos_ordenados] == [1]

    def test_reordenar_pasos(self, preparacion_masa):
        primero, segundo = preparacion_masa.pasos
        preparacion_masa.reordenar_pasos([segundo.id, primero.id])
        assert preparacion_masa.pasos_ordenados[0].id == segundo.id


class TestConsultas:
    """Consultas del agregado utilizadas por los servicios de dominio."""

    def test_ingredientes_utilizados(self, receta, harina, sal, levadura):
        assert receta.ingredientes_utilizados() == {harina.id, sal.id, levadura.id}
