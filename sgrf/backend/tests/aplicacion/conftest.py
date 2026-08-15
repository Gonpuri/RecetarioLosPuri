"""Fixtures de las pruebas de la capa de Aplicacion."""

from decimal import Decimal

import pytest

from sgrf.aplicacion.casos_uso import CrearReceta
from sgrf.aplicacion.dto import (
    ComandoCrearReceta,
    DatosIngrediente,
    DatosPreparacion,
)
from sgrf.dominio.entidades import (
    Categoria,
    Etiqueta,
    Fuente,
    Ingrediente,
    RolUsuario,
    Usuario,
)

from dobles import UnidadDeTrabajoEnMemoria


@pytest.fixture
def uow():
    """Unidad de Trabajo en memoria, ya poblada con catalogos basicos."""
    unidad = UnidadDeTrabajoEnMemoria()
    return unidad


@pytest.fixture
def administrador(uow):
    """Usuario con perfil Administrador."""
    usuario = Usuario(
        nombre="Gonza",
        correo="gonza@familia.test",
        rol=RolUsuario.ADMINISTRADOR,
    )
    uow.usuarios.guardar(usuario)
    return usuario


@pytest.fixture
def familiar(uow):
    """Usuario con perfil Usuario Familiar."""
    usuario = Usuario(nombre="Ana", correo="ana@familia.test")
    uow.usuarios.guardar(usuario)
    return usuario


@pytest.fixture
def familiar_inactivo(uow):
    """Usuario desactivado (RF-003)."""
    usuario = Usuario(nombre="Luis", correo="luis@familia.test")
    usuario.desactivar()
    uow.usuarios.guardar(usuario)
    return usuario


@pytest.fixture
def fuente(uow):
    """Fuente registrada en el catalogo."""
    entidad = Fuente(nombre="Cuaderno de la abuela")
    uow.fuentes.guardar(entidad)
    return entidad


@pytest.fixture
def harina(uow):
    """Ingrediente de catalogo: harina."""
    entidad = Ingrediente(nombre="Harina 000")
    uow.ingredientes.guardar(entidad)
    return entidad


@pytest.fixture
def sal(uow):
    """Ingrediente de catalogo: sal."""
    entidad = Ingrediente(nombre="Sal fina")
    uow.ingredientes.guardar(entidad)
    return entidad


@pytest.fixture
def levadura(uow):
    """Ingrediente de catalogo: levadura."""
    entidad = Ingrediente(nombre="Levadura fresca")
    uow.ingredientes.guardar(entidad)
    return entidad


@pytest.fixture
def categoria(uow):
    """Categoria registrada en el catalogo."""
    entidad = Categoria(nombre="Panaderia")
    uow.categorias.guardar(entidad)
    return entidad


@pytest.fixture
def etiqueta(uow):
    """Etiqueta registrada en el catalogo."""
    entidad = Etiqueta(nombre="casero")
    uow.etiquetas.guardar(entidad)
    return entidad


@pytest.fixture
def comando_pan(familiar, fuente, harina, sal, levadura):
    """Comando de alta de una receta valida de pan casero."""
    return ComandoCrearReceta(
        solicitante_id=familiar.id,
        nombre="Pan casero",
        descripcion="Receta familiar de pan.",
        rendimiento_base=Decimal("4"),
        rendimiento_descripcion="porciones",
        fuente_id=fuente.id,
        preparaciones=(
            DatosPreparacion(
                nombre="Masa",
                ingredientes=(
                    DatosIngrediente(
                        ingrediente_id=harina.id,
                        cantidad=Decimal("500"),
                        unidad="g",
                        tipo_escalado="lineal",
                    ),
                    DatosIngrediente(
                        ingrediente_id=levadura.id,
                        cantidad=Decimal("10"),
                        unidad="g",
                        tipo_escalado="fijo",
                    ),
                    DatosIngrediente(
                        ingrediente_id=sal.id,
                        tipo_escalado="a_gusto",
                    ),
                ),
                pasos=("Mezclar los secos.", "Amasar diez minutos."),
            ),
        ),
    )


@pytest.fixture
def receta_creada(uow, comando_pan):
    """Receta de pan ya persistida en el repositorio."""
    return CrearReceta(uow).ejecutar(comando_pan)
