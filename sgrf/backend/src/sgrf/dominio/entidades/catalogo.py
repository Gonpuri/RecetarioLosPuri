"""Entidades de catalogo del SGRF.

Reune las entidades que viven fuera del agregado Receta y que esta
referencia por identidad: Usuario, Fuente, Categoria, Etiqueta e
Ingrediente. Todas poseen ciclo de vida propio y son reutilizables.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from uuid import UUID, uuid4

from ..excepciones import ValorInvalido


class RolUsuario(Enum):
    """Perfiles definidos en ANALISIS.md, seccion 1.7."""

    ADMINISTRADOR = "administrador"
    USUARIO_FAMILIAR = "usuario_familiar"


def _texto_obligatorio(valor: str, campo: str) -> str:
    """Valida y normaliza un texto que no puede quedar vacio."""
    limpio = (valor or "").strip()
    if not limpio:
        raise ValorInvalido(f"El campo {campo} es obligatorio.")
    return limpio


@dataclass
class Usuario:
    """Integrante de la familia con acceso al recetario.

    RF-003: los usuarios se desactivan, nunca se eliminan, para preservar
    el historial.
    """

    nombre: str
    correo: str
    rol: RolUsuario = RolUsuario.USUARIO_FAMILIAR
    activo: bool = True
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        self.nombre = _texto_obligatorio(self.nombre, "nombre")
        self.correo = _texto_obligatorio(self.correo, "correo").lower()
        if "@" not in self.correo:
            raise ValorInvalido("El correo indicado no es valido.")

    @property
    def es_administrador(self) -> bool:
        """Indica si el usuario puede administrar usuarios y catalogos."""
        return self.rol is RolUsuario.ADMINISTRADOR

    def desactivar(self) -> None:
        """Quita el acceso conservando el historial (RF-003)."""
        self.activo = False

    def activar(self) -> None:
        """Restituye el acceso del usuario."""
        self.activo = True


@dataclass
class Fuente:
    """Origen de una Receta (RN-002: toda receta posee exactamente una)."""

    nombre: str
    detalle: str = ""
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        self.nombre = _texto_obligatorio(self.nombre, "nombre de la fuente")
        self.detalle = (self.detalle or "").strip()


@dataclass
class Categoria:
    """Clasificacion jerarquica de Recetas (ANALISIS.md, seccion 3.3).

    La jerarquia se modela con `categoria_padre_id`: una Categoria sin padre
    es de primer nivel y una con padre es una subcategoria.
    """

    nombre: str
    categoria_padre_id: UUID | None = None
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        self.nombre = _texto_obligatorio(self.nombre, "nombre de la categoria")
        if self.categoria_padre_id == self.id:
            raise ValorInvalido("Una categoria no puede ser su propia padre.")

    @property
    def es_subcategoria(self) -> bool:
        """Indica si la categoria depende de otra."""
        return self.categoria_padre_id is not None


@dataclass
class Etiqueta:
    """Clasificacion transversal de Recetas (ANALISIS.md, seccion 3.3)."""

    nombre: str
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        self.nombre = _texto_obligatorio(self.nombre, "nombre de la etiqueta").lower()


@dataclass
class Ingrediente:
    """Elemento del catalogo unico reutilizable (ANALISIS.md, seccion 3.6).

    El Ingrediente jamas almacena cantidades: estas pertenecen
    exclusivamente a IngredientePreparacion.
    """

    nombre: str
    descripcion: str = ""
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        self.nombre = _texto_obligatorio(self.nombre, "nombre del ingrediente")
        self.descripcion = (self.descripcion or "").strip()
