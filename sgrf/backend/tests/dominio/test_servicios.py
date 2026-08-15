"""Pruebas unitarias de los Servicios del Dominio."""

from decimal import Decimal
from uuid import uuid4

import pytest

from sgrf.dominio.entidades import (
    Fotografia,
    IngredientePreparacion,
    Preparacion,
    Receta,
    TipoFotografia,
)
from sgrf.dominio.excepciones import ValorInvalido
from sgrf.dominio.objetos_valor import Cantidad, Rendimiento, TipoEscalado, Unidad
from sgrf.dominio.servicios import (
    BuscadorRecetas,
    CriteriosBusqueda,
    EscaladorRecetas,
    GeneradorListaCompras,
    ValidadorRecetas,
)


class TestEscaladorRecetas:
    """RN-004 y RF-031 a RF-033: escalado sin modificar la receta base."""

    def test_escalado_lineal_al_doble(self, receta, harina):
        resultado = EscaladorRecetas().escalar(receta, Rendimiento(8, "porciones"))
        ingrediente = self._buscar(resultado, harina.id)
        assert resultado.factor == Decimal("2")
        assert ingrediente.cantidad == Cantidad(1000, Unidad.GRAMO)

    def test_escalado_lineal_a_la_mitad(self, receta, harina):
        resultado = EscaladorRecetas().escalar(receta, Rendimiento(2, "porciones"))
        assert self._buscar(resultado, harina.id).cantidad == Cantidad(250, Unidad.GRAMO)

    def test_el_ingrediente_fijo_no_cambia(self, receta, levadura):
        resultado = EscaladorRecetas().escalar(receta, Rendimiento(8, "porciones"))
        assert self._buscar(resultado, levadura.id).cantidad == Cantidad(10, Unidad.GRAMO)

    def test_a_gusto_no_tiene_cantidad(self, receta, sal):
        resultado = EscaladorRecetas().escalar(receta, Rendimiento(8, "porciones"))
        ingrediente = self._buscar(resultado, sal.id)
        assert ingrediente.cantidad is None
        assert ingrediente.texto_cantidad == "a gusto"

    def test_la_receta_base_nunca_se_modifica(self, receta, harina):
        """RN-004: la entidad conserva su estado tras escalar."""
        original = receta.preparaciones[0].ingredientes[0].cantidad
        EscaladorRecetas().escalar(receta, Rendimiento(100, "porciones"))
        assert receta.preparaciones[0].ingredientes[0].cantidad == original
        assert receta.rendimiento_base == Rendimiento(4, "porciones")

    def test_escalar_al_mismo_rendimiento_devuelve_factor_uno(self, receta):
        resultado = EscaladorRecetas().escalar(receta, Rendimiento(4, "porciones"))
        assert resultado.es_receta_base

    def test_el_resultado_es_inmutable(self, receta):
        resultado = EscaladorRecetas().escalar(receta, Rendimiento(8, "porciones"))
        with pytest.raises(Exception):
            resultado.factor = Decimal("3")

    def test_no_escala_entre_rendimientos_incompatibles(self, receta):
        with pytest.raises(ValorInvalido):
            EscaladorRecetas().escalar(receta, Rendimiento(2, "tortas"))

    def test_conserva_el_orden_de_las_preparaciones(self, receta):
        salsa = Preparacion(nombre="Salsa")
        salsa.agregar_ingrediente(
            IngredientePreparacion(
                ingrediente_id=uuid4(), cantidad=Cantidad(1, Unidad.LITRO)
            )
        )
        receta.agregar_preparacion(salsa)
        resultado = EscaladorRecetas().escalar(receta, Rendimiento(8, "porciones"))
        assert [p.nombre for p in resultado.preparaciones] == ["Masa", "Salsa"]

    @staticmethod
    def _buscar(receta_escalada, ingrediente_id):
        """Localiza un ingrediente escalado por la identidad del catalogo."""
        return next(
            ingrediente
            for preparacion in receta_escalada.preparaciones
            for ingrediente in preparacion.ingredientes
            if ingrediente.ingrediente_id == ingrediente_id
        )


class TestGeneradorListaCompras:
    """RN-006: la lista se arma solo con lo que el usuario selecciona."""

    def test_incluye_unicamente_los_ingredientes_seleccionados(
        self, receta, nombres_ingredientes, harina
    ):
        escalada = EscaladorRecetas().escalar(receta, Rendimiento(4, "porciones"))
        seleccion = {receta.preparaciones[0].ingredientes[0].id}
        lista = GeneradorListaCompras().generar(escalada, seleccion, nombres_ingredientes)
        assert len(lista.items) == 1
        assert lista.items[0].ingrediente_id == harina.id

    def test_sin_seleccion_la_lista_queda_vacia(self, receta, nombres_ingredientes):
        escalada = EscaladorRecetas().escalar(receta, Rendimiento(4, "porciones"))
        lista = GeneradorListaCompras().generar(escalada, set(), nombres_ingredientes)
        assert lista.esta_vacia

    def test_consolida_el_mismo_ingrediente_en_distintas_preparaciones(
        self, fuente, harina, nombres_ingredientes
    ):
        receta = Receta(
            nombre="Tarta",
            rendimiento_base=Rendimiento(4, "porciones"),
            fuente_id=fuente.id,
        )
        masa = Preparacion(nombre="Masa")
        masa.agregar_ingrediente(
            IngredientePreparacion(
                ingrediente_id=harina.id, cantidad=Cantidad(200, Unidad.GRAMO)
            )
        )
        relleno = Preparacion(nombre="Relleno")
        relleno.agregar_ingrediente(
            IngredientePreparacion(
                ingrediente_id=harina.id, cantidad=Cantidad(50, Unidad.GRAMO)
            )
        )
        receta.agregar_preparacion(masa)
        receta.agregar_preparacion(relleno)

        escalada = EscaladorRecetas().escalar(receta, Rendimiento(4, "porciones"))
        seleccion = {
            masa.ingredientes[0].id,
            relleno.ingredientes[0].id,
        }
        lista = GeneradorListaCompras().generar(escalada, seleccion, nombres_ingredientes)

        assert len(lista.items) == 1
        assert lista.items[0].cantidad == Cantidad(250, Unidad.GRAMO)

    def test_no_consolida_unidades_distintas(self, fuente, harina, nombres_ingredientes):
        """El dominio mantiene unidades: gramos y mililitros no se mezclan."""
        receta = Receta(
            nombre="Mezcla",
            rendimiento_base=Rendimiento(4, "porciones"),
            fuente_id=fuente.id,
        )
        masa = Preparacion(nombre="Masa")
        masa.agregar_ingrediente(
            IngredientePreparacion(
                ingrediente_id=harina.id, cantidad=Cantidad(200, Unidad.GRAMO)
            )
        )
        salsa = Preparacion(nombre="Salsa")
        salsa.agregar_ingrediente(
            IngredientePreparacion(
                ingrediente_id=harina.id, cantidad=Cantidad(100, Unidad.MILILITRO)
            )
        )
        receta.agregar_preparacion(masa)
        receta.agregar_preparacion(salsa)

        escalada = EscaladorRecetas().escalar(receta, Rendimiento(4, "porciones"))
        seleccion = {masa.ingredientes[0].id, salsa.ingredientes[0].id}
        lista = GeneradorListaCompras().generar(escalada, seleccion, nombres_ingredientes)

        assert len(lista.items) == 2

    def test_usa_las_cantidades_escaladas(self, receta, nombres_ingredientes):
        escalada = EscaladorRecetas().escalar(receta, Rendimiento(8, "porciones"))
        seleccion = {receta.preparaciones[0].ingredientes[0].id}
        lista = GeneradorListaCompras().generar(escalada, seleccion, nombres_ingredientes)
        assert lista.items[0].cantidad == Cantidad(1000, Unidad.GRAMO)

    def test_los_items_se_ordenan_alfabeticamente(self, receta, nombres_ingredientes):
        escalada = EscaladorRecetas().escalar(receta, Rendimiento(4, "porciones"))
        seleccion = {i.id for i in receta.preparaciones[0].ingredientes}
        lista = GeneradorListaCompras().generar(escalada, seleccion, nombres_ingredientes)
        nombres = [item.nombre_ingrediente for item in lista.items]
        assert nombres == sorted(nombres, key=str.lower)


class TestValidadorRecetas:
    """Auditoria de las reglas de negocio sobre una Receta completa."""

    def test_receta_completa_es_valida(self, receta):
        assert ValidadorRecetas().validar(receta).es_valida

    def test_detecta_preparacion_sin_pasos(self, receta, harina):
        salsa = Preparacion(nombre="Salsa")
        salsa.agregar_ingrediente(
            IngredientePreparacion(
                ingrediente_id=harina.id, cantidad=Cantidad(1, Unidad.LITRO)
            )
        )
        receta.agregar_preparacion(salsa)
        resultado = ValidadorRecetas().validar(receta)
        assert not resultado.es_valida
        assert any(i.codigo_regla == "RN-003" for i in resultado.incumplimientos)

    def test_detecta_preparacion_sin_ingredientes(self, receta):
        vacia = Preparacion(nombre="Armado")
        vacia.agregar_paso("Montar la preparacion.")
        receta.agregar_preparacion(vacia)
        resultado = ValidadorRecetas().validar(receta)
        assert not resultado.es_valida

    def test_elevar_si_invalida_lanza_excepcion(self, receta):
        receta.agregar_preparacion(Preparacion(nombre="Vacia"))
        with pytest.raises(Exception):
            ValidadorRecetas().validar(receta).elevar_si_invalida()

    def test_receta_valida_no_lanza_excepcion(self, receta):
        ValidadorRecetas().validar(receta).elevar_si_invalida()


class TestBuscadorRecetas:
    """RF-038 a RF-043 y criterio de aceptacion 4.12."""

    def test_excluye_archivadas_por_defecto(self, receta):
        receta.archivar()
        resultado = BuscadorRecetas().buscar([receta], CriteriosBusqueda())
        assert resultado == []

    def test_incluye_archivadas_si_se_solicita(self, receta):
        receta.archivar()
        criterios = CriteriosBusqueda(incluir_archivadas=True)
        assert BuscadorRecetas().buscar([receta], criterios) == [receta]

    def test_busca_por_nombre_sin_distinguir_mayusculas(self, receta):
        criterios = CriteriosBusqueda(texto="PAN")
        assert BuscadorRecetas().buscar([receta], criterios) == [receta]

    def test_busca_por_ingrediente(self, receta, harina):
        criterios = CriteriosBusqueda(ingrediente_id=harina.id)
        assert BuscadorRecetas().buscar([receta], criterios) == [receta]

    def test_ingrediente_ausente_no_coincide(self, receta):
        criterios = CriteriosBusqueda(ingrediente_id=uuid4())
        assert BuscadorRecetas().buscar([receta], criterios) == []

    def test_busca_por_categoria(self, receta):
        categoria_id = uuid4()
        receta.asignar_categoria(categoria_id)
        criterios = CriteriosBusqueda(categoria_id=categoria_id)
        assert BuscadorRecetas().buscar([receta], criterios) == [receta]

    def test_filtra_favoritas(self, receta):
        criterios = CriteriosBusqueda(solo_favoritas=True)
        assert BuscadorRecetas().buscar([receta], criterios) == []
        receta.marcar_favorita()
        assert BuscadorRecetas().buscar([receta], criterios) == [receta]

    def test_combina_varios_criterios(self, receta, harina):
        receta.marcar_favorita()
        criterios = CriteriosBusqueda(
            texto="pan", ingrediente_id=harina.id, solo_favoritas=True
        )
        assert BuscadorRecetas().buscar([receta], criterios) == [receta]
