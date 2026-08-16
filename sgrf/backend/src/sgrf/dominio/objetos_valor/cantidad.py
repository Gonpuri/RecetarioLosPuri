"""Objeto de Valor Cantidad.

Representa un valor numerico acompaniado de su Unidad. Es inmutable: toda
operacion devuelve una nueva Cantidad y jamas altera la original, lo que
sostiene la regla RN-004 (la receta base nunca se modifica).
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from ..excepciones import UnidadesIncompatibles, ValorInvalido
from ._decimal import normalizar_decimal_legible
from .unidad import Unidad


@dataclass(frozen=True)
class Cantidad:
    """Valor numerico no negativo expresado en una Unidad."""

    valor: Decimal
    unidad: Unidad

    def __post_init__(self) -> None:
        if not isinstance(self.valor, Decimal):
            object.__setattr__(self, "valor", Decimal(str(self.valor)))
        if self.valor < 0:
            raise ValorInvalido("La cantidad no puede ser negativa.")
        object.__setattr__(self, "valor", normalizar_decimal_legible(self.valor))

    def escalar(self, factor: Decimal) -> Cantidad:
        """Devuelve una nueva Cantidad multiplicada por el factor indicado."""
        if factor < 0:
            raise ValorInvalido("El factor de escalado no puede ser negativo.")
        return Cantidad(self.valor * Decimal(str(factor)), self.unidad)

    def sumar(self, otra: Cantidad) -> Cantidad:
        """Suma dos Cantidades de la misma Unidad.

        El dominio no realiza conversiones entre unidades: sumar gramos con
        mililitros carece de sentido sin conocer la densidad del ingrediente.
        """
        if self.unidad is not otra.unidad:
            raise UnidadesIncompatibles(
                f"No se pueden sumar {self.unidad.simbolo} y {otra.unidad.simbolo}."
            )
        return Cantidad(self.valor + otra.valor, self.unidad)

    def es_cero(self) -> bool:
        """Indica si la Cantidad carece de valor."""
        return self.valor == 0

    def __str__(self) -> str:
        return f"{self.valor} {self.unidad.simbolo}"
