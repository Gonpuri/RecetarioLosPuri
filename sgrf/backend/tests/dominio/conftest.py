"""Fixtures compartidas por las pruebas del dominio."""

from uuid import uuid4

import pytest

from sgrf.dominio.entidades import (
    Fuente,
    Ingrediente,
    IngredientePreparacion,
    Preparacion,
    Receta,
)
from sgrf.dominio.objetos_valor import Cantidad, Rendimiento, TipoEscalado, Unidad


@pytest.fixture
def fuente():
    """Fuente de ejemplo."""
    return Fuente(nombre="Cuaderno de la abuela")


@pytest.fixture
def harina():
    """Ingrediente de catalogo: harina."""
    return Ingrediente(nombre="Harina 000")


@pytest.fixture
def sal():
    """Ingrediente de catalogo: sal."""
    return Ingrediente(nombre="Sal fina")


@pytest.fixture
def levadura():
    """Ingrediente de catalogo: levadura."""
    return Ingrediente(nombre="Levadura fresca")


@pytest.fixture
def preparacion_masa(harina, sal, levadura):
    """Preparacion 'Masa' con los tres tipos de escalado mas frecuentes."""
    preparacion = Preparacion(nombre="Masa")
    preparacion.agregar_ingrediente(
        IngredientePreparacion(
            ingrediente_id=harina.id,
            cantidad=Cantidad(500, Unidad.GRAMO),
            tipo_escalado=TipoEscalado.LINEAL,
        )
    )
    preparacion.agregar_ingrediente(
        IngredientePreparacion(
            ingrediente_id=levadura.id,
            cantidad=Cantidad(10, Unidad.GRAMO),
            tipo_escalado=TipoEscalado.FIJO,
        )
    )
    preparacion.agregar_ingrediente(
        IngredientePreparacion(
            ingrediente_id=sal.id,
            tipo_escalado=TipoEscalado.A_GUSTO,
        )
    )
    preparacion.agregar_paso("Mezclar los ingredientes secos.")
    preparacion.agregar_paso("Amasar durante diez minutos.")
    return preparacion


@pytest.fixture
def receta(fuente, preparacion_masa):
    """Receta valida con una preparacion y rendimiento base de 4 porciones."""
    receta = Receta(
        nombre="Pan casero",
        descripcion="Receta familiar de pan.",
        rendimiento_base=Rendimiento(4, "porciones"),
        fuente_id=fuente.id,
    )
    receta.agregar_preparacion(preparacion_masa)
    return receta


@pytest.fixture
def nombres_ingredientes(harina, sal, levadura):
    """Indice de nombres del catalogo para la Lista de Compras."""
    return {
        harina.id: harina.nombre,
        sal.id: sal.nombre,
        levadura.id: levadura.nombre,
    }
