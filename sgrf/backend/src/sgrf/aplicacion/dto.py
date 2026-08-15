"""Objetos de Transferencia de Datos (DTO) de la capa de Aplicacion.

Los Comandos representan la intencion del usuario y los Resultados, la
respuesta que consume la Presentacion. Su existencia impide que las
entidades del Dominio se filtren hacia la API: la Presentacion nunca
manipula un agregado directamente.

Todos son inmutables y estan expresados en tipos primitivos, de modo que
serializarlos a JSON resulte directo.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from uuid import UUID

# ---------------------------------------------------------------------------
# Comandos
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DatosIngrediente:
    """Ingrediente de una Preparacion tal como llega desde la interfaz."""

    ingrediente_id: UUID
    tipo_escalado: str = "lineal"
    cantidad: Decimal | None = None
    unidad: str | None = None
    observacion: str = ""


@dataclass(frozen=True)
class DatosPreparacion:
    """Preparacion completa recibida desde la interfaz."""

    nombre: str
    ingredientes: tuple[DatosIngrediente, ...] = ()
    pasos: tuple[str, ...] = ()


@dataclass(frozen=True)
class ComandoCrearReceta:
    """Solicitud de alta de una Receta (RF-005)."""

    solicitante_id: UUID
    nombre: str
    rendimiento_base: Decimal
    fuente_id: UUID
    descripcion: str = ""
    rendimiento_descripcion: str = "porciones"
    preparaciones: tuple[DatosPreparacion, ...] = ()
    categorias_ids: tuple[UUID, ...] = ()
    etiquetas_ids: tuple[UUID, ...] = ()


@dataclass(frozen=True)
class ComandoEditarReceta:
    """Solicitud de edicion de los datos generales (RF-006)."""

    solicitante_id: UUID
    receta_id: UUID
    nombre: str | None = None
    descripcion: str | None = None
    rendimiento_base: Decimal | None = None
    rendimiento_descripcion: str | None = None
    fuente_id: UUID | None = None


@dataclass(frozen=True)
class ComandoEscalarReceta:
    """Solicitud de escalado hacia un nuevo Rendimiento (RF-031)."""

    solicitante_id: UUID
    receta_id: UUID
    rendimiento_objetivo: Decimal
    rendimiento_descripcion: str | None = None


@dataclass(frozen=True)
class ComandoGenerarListaCompras:
    """Solicitud de Lista de Compras (RF-034 y RF-035)."""

    solicitante_id: UUID
    receta_id: UUID
    ingredientes_seleccionados: tuple[UUID, ...]
    rendimiento_objetivo: Decimal | None = None
    rendimiento_descripcion: str | None = None
    persistir: bool = False


@dataclass(frozen=True)
class ComandoBuscarRecetas:
    """Solicitud de busqueda (RF-038 a RF-043)."""

    solicitante_id: UUID
    texto: str | None = None
    ingrediente_id: UUID | None = None
    categoria_id: UUID | None = None
    etiqueta_id: UUID | None = None
    fuente_id: UUID | None = None
    solo_favoritas: bool = False
    incluir_archivadas: bool = False


# ---------------------------------------------------------------------------
# Resultados
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class IngredienteResultado:
    """Ingrediente listo para mostrarse en la interfaz."""

    ingrediente_preparacion_id: UUID
    ingrediente_id: UUID
    nombre: str
    texto_cantidad: str
    tipo_escalado: str
    cantidad: Decimal | None = None
    unidad: str | None = None
    observacion: str = ""


@dataclass(frozen=True)
class PasoResultado:
    """Paso de una Preparacion."""

    id: UUID
    orden: int
    descripcion: str


@dataclass(frozen=True)
class FotografiaResultado:
    """Fotografia asociada a una Preparacion."""

    id: UUID
    ruta: str
    tipo: str
    descripcion: str = ""


@dataclass(frozen=True)
class PreparacionResultado:
    """Preparacion completa lista para mostrarse."""

    id: UUID
    nombre: str
    orden: int
    ingredientes: tuple[IngredienteResultado, ...] = ()
    pasos: tuple[PasoResultado, ...] = ()
    fotografias: tuple[FotografiaResultado, ...] = ()


@dataclass(frozen=True)
class NotaResultado:
    """Nota permanente de una Receta."""

    id: UUID
    texto: str
    fecha: datetime
    autor_id: UUID | None = None


@dataclass(frozen=True)
class RecetaResultado:
    """Receta completa lista para mostrarse (RF-007)."""

    id: UUID
    nombre: str
    descripcion: str
    rendimiento_base: Decimal
    rendimiento_descripcion: str
    fuente_id: UUID
    fuente_nombre: str
    archivada: bool
    favorita: bool
    preparaciones: tuple[PreparacionResultado, ...] = ()
    categorias_ids: tuple[UUID, ...] = ()
    etiquetas_ids: tuple[UUID, ...] = ()
    notas: tuple[NotaResultado, ...] = ()


@dataclass(frozen=True)
class RecetaResumen:
    """Version reducida para listados y resultados de busqueda.

    Corresponde a la tarjeta de receta descrita en el Capitulo 6.7.
    """

    id: UUID
    nombre: str
    rendimiento_base: Decimal
    rendimiento_descripcion: str
    archivada: bool
    favorita: bool
    categorias_ids: tuple[UUID, ...] = ()
    fotografia_final: str | None = None


@dataclass(frozen=True)
class RecetaEscaladaResultado:
    """Receta escalada. Representacion temporal, jamas se persiste (ADR-003)."""

    receta_id: UUID
    nombre: str
    rendimiento_base: Decimal
    rendimiento_solicitado: Decimal
    rendimiento_descripcion: str
    factor: Decimal
    preparaciones: tuple[PreparacionResultado, ...] = ()


@dataclass(frozen=True)
class ItemCompraResultado:
    """Renglon de una Lista de Compras."""

    id: UUID
    ingrediente_id: UUID
    nombre: str
    texto_cantidad: str
    comprado: bool = False


@dataclass(frozen=True)
class ListaCompraResultado:
    """Lista de Compras consolidada (RF-035)."""

    id: UUID
    items: tuple[ItemCompraResultado, ...]
    fecha: datetime
    usuario_id: UUID | None = None


@dataclass(frozen=True)
class UsuarioResultado:
    """Usuario del sistema."""

    id: UUID
    nombre: str
    correo: str
    rol: str
    activo: bool
