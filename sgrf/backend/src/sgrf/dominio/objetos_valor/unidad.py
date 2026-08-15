"""Objeto de Valor Unidad.

Representa la unidad de medida en la que se expresa una Cantidad.

El analisis (PROMPT_CODEX.md, seccion Lista de compras) indica
"Mantener unidades": el sistema NO convierte entre unidades. La
consolidacion de la Lista de Compras agrupa por (Ingrediente, Unidad).
El atributo `sistema` existe unicamente para clasificar y ordenar, nunca
para convertir.
"""

from __future__ import annotations

from enum import Enum


class SistemaDeMedida(Enum):
    """Naturaleza fisica de una Unidad."""

    MASA = "masa"
    VOLUMEN = "volumen"
    CONTEO = "conteo"


class Unidad(Enum):
    """Unidades de medida admitidas por el dominio.

    El valor de cada miembro es el simbolo que se muestra al usuario.
    """

    GRAMO = ("g", SistemaDeMedida.MASA)
    KILOGRAMO = ("kg", SistemaDeMedida.MASA)
    MILILITRO = ("ml", SistemaDeMedida.VOLUMEN)
    LITRO = ("l", SistemaDeMedida.VOLUMEN)
    CUCHARADA = ("cda", SistemaDeMedida.VOLUMEN)
    CUCHARADITA = ("cdita", SistemaDeMedida.VOLUMEN)
    TAZA = ("taza", SistemaDeMedida.VOLUMEN)
    PIZCA = ("pizca", SistemaDeMedida.VOLUMEN)
    UNIDAD = ("u", SistemaDeMedida.CONTEO)

    def __init__(self, simbolo: str, sistema: SistemaDeMedida) -> None:
        self.simbolo = simbolo
        self.sistema = sistema

    @classmethod
    def desde_simbolo(cls, simbolo: str) -> Unidad:
        """Devuelve la Unidad cuyo simbolo coincide con el recibido."""
        for unidad in cls:
            if unidad.simbolo == simbolo:
                return unidad
        raise ValueError(f"Unidad desconocida: {simbolo!r}")

    def __str__(self) -> str:
        return self.simbolo
