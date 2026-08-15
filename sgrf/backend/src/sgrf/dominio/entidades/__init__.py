"""Entidades del dominio del SGRF (ANALISIS.md, seccion 3.3)."""

from .catalogo import (
    Categoria,
    Etiqueta,
    Fuente,
    Ingrediente,
    RolUsuario,
    Usuario,
)
from .componentes import (
    Fotografia,
    IngredientePreparacion,
    Nota,
    Paso,
    TipoFotografia,
)
from .lista_compra import ItemCompra, ListaCompra
from .preparacion import Preparacion
from .receta import Receta

__all__ = [
    "Categoria",
    "Etiqueta",
    "Fotografia",
    "Fuente",
    "Ingrediente",
    "IngredientePreparacion",
    "ItemCompra",
    "ListaCompra",
    "Nota",
    "Paso",
    "Preparacion",
    "Receta",
    "RolUsuario",
    "TipoFotografia",
    "Usuario",
]
