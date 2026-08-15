"""Casos de Uso del SGRF (Capitulo 5.4)."""

from .busqueda import BuscarRecetas, ListarRecetas
from .catalogo import (
    AsignarClasificacion,
    GestionarCatalogoIngredientes,
    GestionarCategorias,
    GestionarEtiquetas,
    GestionarFuentes,
    GestionarUsuarios,
)
from .escalado import (
    CombinarListasCompras,
    EscalarReceta,
    GenerarListaCompras,
    ListarListasCompras,
)
from .preparaciones import (
    GestionarFotografias,
    GestionarIngredientesDePreparacion,
    GestionarNotas,
    GestionarPasos,
    GestionarPreparaciones,
)
from .recetas import (
    ArchivarReceta,
    ConsultarReceta,
    CrearReceta,
    DuplicarReceta,
    EditarReceta,
    MarcarFavorita,
    RestaurarReceta,
)

__all__ = [
    "ArchivarReceta",
    "AsignarClasificacion",
    "BuscarRecetas",
    "CombinarListasCompras",
    "ConsultarReceta",
    "CrearReceta",
    "DuplicarReceta",
    "EditarReceta",
    "EscalarReceta",
    "GenerarListaCompras",
    "GestionarCatalogoIngredientes",
    "GestionarCategorias",
    "GestionarEtiquetas",
    "GestionarFotografias",
    "GestionarFuentes",
    "GestionarIngredientesDePreparacion",
    "GestionarNotas",
    "GestionarPasos",
    "GestionarPreparaciones",
    "GestionarUsuarios",
    "ListarListasCompras",
    "ListarRecetas",
    "MarcarFavorita",
    "RestaurarReceta",
]
