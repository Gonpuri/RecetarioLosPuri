"""Objeto de Valor Rendimiento.

Expresa cuanto produce una Receta (por ejemplo "8 porciones" o "1 torta").
El Rendimiento Base es el registrado junto a la receta original y, segun
RN-001, es unico por Receta.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from ..excepciones import ValorInvalido

DESCRIPCION_POR_DEFECTO = "porciones"


@dataclass(frozen=True)
class Rendimiento:
    """Cantidad producida por una Receta, con su descripcion."""

    valor: Decimal
    descripcion: str = DESCRIPCION_POR_DEFECTO

    def __post_init__(self) -> None:
        if not isinstance(self.valor, Decimal):
            object.__setattr__(self, "valor", Decimal(str(self.valor)))
        if self.valor <= 0:
            raise ValorInvalido("El rendimiento debe ser mayor que cero.")
        descripcion = self.descripcion.strip()
        if not descripcion:
            raise ValorInvalido("El rendimiento requiere una descripcion.")
        object.__setattr__(self, "descripcion", descripcion)

    def factor_hacia(self, objetivo: Rendimiento) -> Decimal:
        """Calcula el factor de escalado necesario para alcanzar el objetivo.

        Solo tiene sentido comparar rendimientos que miden lo mismo; por eso
        se exige que ambas descripciones coincidan.
        """
        if self.descripcion.lower() != objetivo.descripcion.lower():
            raise ValorInvalido(
                "No se pueden comparar rendimientos de distinta naturaleza: "
                f"{self.descripcion!r} y {objetivo.descripcion!r}."
            )
        return objetivo.valor / self.valor

    def __str__(self) -> str:
        return f"{self.valor} {self.descripcion}"
