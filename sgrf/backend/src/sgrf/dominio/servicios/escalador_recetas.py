"""Servicio de dominio EscaladorRecetas.

Calcula las cantidades de una Receta para un Rendimiento distinto del base.

Reglas que sostiene:
- RN-004 / ADR-003: la Receta almacenada nunca se modifica y el resultado
  del calculo es temporal, jamas se persiste.
- RF-033: cada ingrediente se comporta segun su TipoEscalado.

El resultado se expresa mediante estructuras inmutables (RecetaEscalada)
que la capa de Presentacion consume para mostrar la receta escalada.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from ..entidades.receta import Receta
from ..objetos_valor import Cantidad, Rendimiento, TipoEscalado


@dataclass(frozen=True)
class IngredienteEscalado:
    """Ingrediente con su cantidad ya calculada. Estructura temporal."""

    ingrediente_id: UUID
    ingrediente_preparacion_id: UUID
    cantidad: Cantidad | None
    tipo_escalado: TipoEscalado
    observacion: str = ""

    @property
    def texto_cantidad(self) -> str:
        """Texto listo para mostrar, incluso sin cantidad numerica."""
        if self.cantidad is not None:
            return str(self.cantidad)
        return self.tipo_escalado.etiqueta


@dataclass(frozen=True)
class PreparacionEscalada:
    """Preparacion con sus ingredientes ya calculados. Estructura temporal."""

    preparacion_id: UUID
    nombre: str
    orden: int
    ingredientes: tuple[IngredienteEscalado, ...]


@dataclass(frozen=True)
class RecetaEscalada:
    """Representacion temporal de una Receta para un nuevo Rendimiento.

    Nunca se persiste (ADR-003). Solo referencia la receta de origen por su
    identidad, de modo que resulta imposible confundirla con la entidad.
    """

    receta_id: UUID
    nombre: str
    rendimiento_base: Rendimiento
    rendimiento_solicitado: Rendimiento
    factor: Decimal
    preparaciones: tuple[PreparacionEscalada, ...]

    @property
    def es_receta_base(self) -> bool:
        """Indica si el rendimiento solicitado coincide con el base."""
        return self.factor == Decimal(1)


class EscaladorRecetas:
    """Calcula cantidades para un nuevo Rendimiento sin alterar la Receta."""

    def escalar(self, receta: Receta, rendimiento_objetivo: Rendimiento) -> RecetaEscalada:
        """Devuelve la representacion escalada de la receta.

        La receta recibida no se modifica en ningun momento: todas las
        cantidades se calculan sobre copias inmutables.
        """
        factor = receta.rendimiento_base.factor_hacia(rendimiento_objetivo)
        preparaciones = tuple(
            self._escalar_preparacion(preparacion, factor)
            for preparacion in receta.preparaciones_ordenadas
        )
        return RecetaEscalada(
            receta_id=receta.id,
            nombre=receta.nombre,
            rendimiento_base=receta.rendimiento_base,
            rendimiento_solicitado=rendimiento_objetivo,
            factor=factor,
            preparaciones=preparaciones,
        )

    def _escalar_preparacion(self, preparacion, factor: Decimal) -> PreparacionEscalada:
        """Escala todos los ingredientes de una preparacion."""
        ingredientes = tuple(
            IngredienteEscalado(
                ingrediente_id=ingrediente.ingrediente_id,
                ingrediente_preparacion_id=ingrediente.id,
                cantidad=ingrediente.cantidad_escalada(factor),
                tipo_escalado=ingrediente.tipo_escalado,
                observacion=ingrediente.observacion,
            )
            for ingrediente in preparacion.ingredientes
        )
        return PreparacionEscalada(
            preparacion_id=preparacion.id,
            nombre=preparacion.nombre,
            orden=preparacion.orden,
            ingredientes=ingredientes,
        )
