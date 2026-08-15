"""Objeto de Valor TipoEscalado.

Define como se comporta un IngredientePreparacion cuando la Receta se
escala hacia un nuevo Rendimiento (RF-033).

- LINEAL: la cantidad se multiplica por el factor de escalado.
- FIJO: la cantidad permanece invariable (por ejemplo, el molde o la
  levadura de una masa, que no acompanian proporcionalmente).
- A_GUSTO: no posee cantidad numerica; se ajusta al criterio de quien cocina.
- CANTIDAD_NECESARIA: no posee cantidad numerica; se emplea la que la
  preparacion requiera (por ejemplo, harina para estirar).
"""

from __future__ import annotations

from enum import Enum


class TipoEscalado(Enum):
    """Comportamiento de un ingrediente frente al escalado."""

    LINEAL = "lineal"
    FIJO = "fijo"
    A_GUSTO = "a_gusto"
    CANTIDAD_NECESARIA = "cantidad_necesaria"

    @property
    def requiere_cantidad(self) -> bool:
        """Indica si el tipo exige que el ingrediente tenga una Cantidad."""
        return self in (TipoEscalado.LINEAL, TipoEscalado.FIJO)

    @property
    def admite_cantidad(self) -> bool:
        """Indica si el tipo puede llevar una Cantidad asociada.

        A_GUSTO y CANTIDAD_NECESARIA se definen justamente por la ausencia
        de una cantidad determinada.
        """
        return self.requiere_cantidad

    @property
    def se_multiplica(self) -> bool:
        """Indica si la cantidad debe multiplicarse al escalar."""
        return self is TipoEscalado.LINEAL

    @property
    def etiqueta(self) -> str:
        """Texto que la interfaz muestra cuando no hay cantidad numerica."""
        textos = {
            TipoEscalado.A_GUSTO: "a gusto",
            TipoEscalado.CANTIDAD_NECESARIA: "cantidad necesaria",
        }
        return textos.get(self, "")
