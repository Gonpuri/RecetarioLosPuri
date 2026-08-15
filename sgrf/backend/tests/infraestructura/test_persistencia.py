"""Pruebas de integracion de la capa de Persistencia.

Ejercitan los repositorios reales contra la base de datos, verificando que
el agregado sobreviva intacto al viaje de ida y vuelta.

Requieren base de datos, de modo que se ejecutan con pytest-django:

    cd backend && pytest tests/infraestructura

Las pruebas del Dominio y de la Aplicacion no la necesitan.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from sgrf.aplicacion.casos_uso import (
    CrearReceta,
    EscalarReceta,
    GenerarListaCompras,
)
from sgrf.aplicacion.dto import (
    ComandoCrearReceta,
    ComandoEscalarReceta,
    ComandoGenerarListaCompras,
    DatosIngrediente,
    DatosPreparacion,
)
from sgrf.dominio.entidades import (
    Fotografia,
    Fuente,
    Ingrediente,
    Nota,
    RolUsuario,
    TipoFotografia,
    Usuario,
)
from sgrf.dominio.objetos_valor import Cantidad, TipoEscalado, Unidad
from sgrf.infraestructura.persistencia import UnidadDeTrabajoDjango

pytestmark = pytest.mark.django_db


@pytest.fixture
def uow():
    """Unidad de Trabajo sobre PostgreSQL."""
    return UnidadDeTrabajoDjango()


@pytest.fixture
def catalogo(uow):
    """Catalogo minimo persistido: usuario, fuente e ingredientes."""
    usuario = Usuario(
        nombre="Gonza", correo="gonza@familia.test", rol=RolUsuario.ADMINISTRADOR
    )
    fuente = Fuente(nombre="Cuaderno de la abuela")
    harina = Ingrediente(nombre="Harina 000")
    sal = Ingrediente(nombre="Sal fina")
    levadura = Ingrediente(nombre="Levadura fresca")

    with uow:
        uow.usuarios.guardar(usuario)
        uow.fuentes.guardar(fuente)
        for ingrediente in (harina, sal, levadura):
            uow.ingredientes.guardar(ingrediente)
        uow.confirmar()

    return {
        "usuario": usuario,
        "fuente": fuente,
        "harina": harina,
        "sal": sal,
        "levadura": levadura,
    }


@pytest.fixture
def comando_pan(catalogo):
    """Comando de alta de una receta de pan casero."""
    return ComandoCrearReceta(
        solicitante_id=catalogo["usuario"].id,
        nombre="Pan casero",
        descripcion="Receta familiar.",
        rendimiento_base=Decimal("4"),
        fuente_id=catalogo["fuente"].id,
        preparaciones=(
            DatosPreparacion(
                nombre="Masa",
                ingredientes=(
                    DatosIngrediente(
                        ingrediente_id=catalogo["harina"].id,
                        cantidad=Decimal("500"),
                        unidad="g",
                        tipo_escalado="lineal",
                    ),
                    DatosIngrediente(
                        ingrediente_id=catalogo["levadura"].id,
                        cantidad=Decimal("10"),
                        unidad="g",
                        tipo_escalado="fijo",
                    ),
                    DatosIngrediente(
                        ingrediente_id=catalogo["sal"].id, tipo_escalado="a_gusto"
                    ),
                ),
                pasos=("Mezclar los secos.", "Amasar diez minutos."),
            ),
        ),
    )


class TestViajeDeIdaYVuelta:
    """El agregado debe sobrevivir intacto al guardado y la recuperacion."""

    def test_conserva_los_datos_generales(self, uow, comando_pan):
        creada = CrearReceta(uow).ejecutar(comando_pan)
        recuperada = uow.recetas.obtener(creada.id)
        assert recuperada.nombre == "Pan casero"
        assert recuperada.rendimiento_base.valor == Decimal("4")
        assert recuperada.rendimiento_base.descripcion == "porciones"

    def test_conserva_las_preparaciones_y_su_orden(self, uow, comando_pan):
        creada = CrearReceta(uow).ejecutar(comando_pan)
        recuperada = uow.recetas.obtener(creada.id)
        assert len(recuperada.preparaciones) == 1
        assert recuperada.preparaciones[0].nombre == "Masa"
        assert recuperada.preparaciones[0].orden == 1

    def test_conserva_las_cantidades_y_unidades(self, uow, comando_pan):
        creada = CrearReceta(uow).ejecutar(comando_pan)
        recuperada = uow.recetas.obtener(creada.id)
        harina = next(
            i
            for i in recuperada.preparaciones[0].ingredientes
            if i.tipo_escalado is TipoEscalado.LINEAL
        )
        assert harina.cantidad == Cantidad(500, Unidad.GRAMO)

    def test_conserva_los_ingredientes_sin_cantidad(self, uow, comando_pan):
        """A gusto y cantidad necesaria no llevan cantidad (decision D-1)."""
        creada = CrearReceta(uow).ejecutar(comando_pan)
        recuperada = uow.recetas.obtener(creada.id)
        sal = next(
            i
            for i in recuperada.preparaciones[0].ingredientes
            if i.tipo_escalado is TipoEscalado.A_GUSTO
        )
        assert sal.cantidad is None

    def test_conserva_los_pasos_ordenados(self, uow, comando_pan):
        creada = CrearReceta(uow).ejecutar(comando_pan)
        recuperada = uow.recetas.obtener(creada.id)
        ordenes = [p.orden for p in recuperada.preparaciones[0].pasos_ordenados]
        assert ordenes == [1, 2]

    def test_conserva_las_identidades(self, uow, comando_pan):
        """Las identidades no cambian al persistir."""
        creada = CrearReceta(uow).ejecutar(comando_pan)
        recuperada = uow.recetas.obtener(creada.id)
        assert recuperada.id == creada.id
        assert recuperada.preparaciones[0].id == creada.preparaciones[0].id


class TestActualizacion:
    """Guardar dos veces no debe duplicar componentes."""

    def test_no_duplica_preparaciones(self, uow, comando_pan):
        creada = CrearReceta(uow).ejecutar(comando_pan)
        receta = uow.recetas.obtener(creada.id)
        with uow:
            uow.recetas.guardar(receta)
            uow.confirmar()
        assert len(uow.recetas.obtener(creada.id).preparaciones) == 1

    def test_elimina_los_componentes_quitados(self, uow, comando_pan):
        creada = CrearReceta(uow).ejecutar(comando_pan)
        receta = uow.recetas.obtener(creada.id)
        paso = receta.preparaciones[0].pasos[0]
        receta.preparaciones[0].quitar_paso(paso.id)
        with uow:
            uow.recetas.guardar(receta)
            uow.confirmar()
        assert len(uow.recetas.obtener(creada.id).preparaciones[0].pasos) == 1

    def test_persiste_notas_y_fotografias(self, uow, comando_pan, catalogo):
        creada = CrearReceta(uow).ejecutar(comando_pan)
        receta = uow.recetas.obtener(creada.id)
        receta.agregar_nota(Nota(texto="Sale mejor con harina integral."))
        receta.agregar_fotografia(
            receta.preparaciones[0].id,
            Fotografia("https://cdn.test/final.jpg", TipoFotografia.FINAL),
        )
        with uow:
            uow.recetas.guardar(receta)
            uow.confirmar()

        recuperada = uow.recetas.obtener(creada.id)
        assert len(recuperada.notas) == 1
        assert recuperada.contar_fotografias(TipoFotografia.FINAL) == 1


class TestTransacciones:
    """La Unidad de Trabajo debe revertir ante un error."""

    def test_revierte_si_el_bloque_falla(self, uow, catalogo):
        fuente = Fuente(nombre="Fuente que no debe quedar")
        try:
            with uow:
                uow.fuentes.guardar(fuente)
                raise RuntimeError("fallo simulado")
        except RuntimeError:
            pass
        assert uow.fuentes.obtener(fuente.id) is None


class TestEscaladoContraLaBase:
    """RN-004 debe sostenerse tambien contra la base de datos."""

    def test_escalar_no_altera_lo_almacenado(self, uow, comando_pan, catalogo):
        creada = CrearReceta(uow).ejecutar(comando_pan)
        EscalarReceta(uow).ejecutar(
            ComandoEscalarReceta(
                solicitante_id=catalogo["usuario"].id,
                receta_id=creada.id,
                rendimiento_objetivo=Decimal("100"),
            )
        )
        recuperada = uow.recetas.obtener(creada.id)
        assert recuperada.rendimiento_base.valor == Decimal("4")
        harina = next(
            i
            for i in recuperada.preparaciones[0].ingredientes
            if i.tipo_escalado is TipoEscalado.LINEAL
        )
        assert harina.cantidad == Cantidad(500, Unidad.GRAMO)

    def test_la_lista_persistida_conserva_las_cantidades(
        self, uow, comando_pan, catalogo
    ):
        creada = CrearReceta(uow).ejecutar(comando_pan)
        harina = creada.preparaciones[0].ingredientes[0]
        lista = GenerarListaCompras(uow).ejecutar(
            ComandoGenerarListaCompras(
                solicitante_id=catalogo["usuario"].id,
                receta_id=creada.id,
                ingredientes_seleccionados=(harina.ingrediente_preparacion_id,),
                rendimiento_objetivo=Decimal("8"),
                persistir=True,
            )
        )
        recuperada = uow.listas_compra.obtener(lista.id)
        assert recuperada.items[0].cantidad == Cantidad(1000, Unidad.GRAMO)


class TestBusquedaSQL:
    """La busqueda traducida a SQL debe respetar el criterio 4.12."""

    def test_excluye_archivadas_por_defecto(self, uow, comando_pan):
        from sgrf.dominio.servicios import CriteriosBusqueda

        creada = CrearReceta(uow).ejecutar(comando_pan)
        receta = uow.recetas.obtener(creada.id)
        receta.archivar()
        with uow:
            uow.recetas.guardar(receta)
            uow.confirmar()
        assert uow.recetas.buscar(CriteriosBusqueda(texto="pan")) == []

    def test_busca_por_ingrediente(self, uow, comando_pan, catalogo):
        from sgrf.dominio.servicios import CriteriosBusqueda

        CrearReceta(uow).ejecutar(comando_pan)
        criterios = CriteriosBusqueda(ingrediente_id=catalogo["harina"].id)
        assert len(uow.recetas.buscar(criterios)) == 1

    def test_detecta_nombres_duplicados_sin_distinguir_mayusculas(
        self, uow, comando_pan
    ):
        CrearReceta(uow).ejecutar(comando_pan)
        assert uow.recetas.existe_con_nombre("PAN CASERO")
