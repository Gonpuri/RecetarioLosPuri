"""Entidades ListaCompra e ItemCompra.

La Lista de Compras se construye unicamente con los ingredientes que el
usuario marca como faltantes (RN-006). La consolidacion agrupa por
Ingrediente y Unidad, sin convertir entre unidades.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4

from ..excepciones import ValorInvalido
from ..objetos_valor import Cantidad, TipoEscalado


@dataclass
class ItemCompra:
    """Renglon consolidado de una Lista de Compras.

    Cuando el ingrediente no posee cantidad numerica (A gusto o Cantidad
    necesaria), `cantidad` queda en None y la interfaz muestra la etiqueta
    del TipoEscalado.
    """

    ingrediente_id: UUID
    nombre_ingrediente: str
    cantidad: Cantidad | None = None
    tipo_escalado: TipoEscalado = TipoEscalado.LINEAL
    comprado: bool = False
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        nombre = (self.nombre_ingrediente or "").strip()
        if not nombre:
            raise ValorInvalido("El item requiere el nombre del ingrediente.")
        self.nombre_ingrediente = nombre

    @property
    def clave_consolidacion(self) -> tuple:
        """Clave por la que se agrupan items equivalentes.

        Se agrupa por Ingrediente y Unidad porque el dominio no convierte
        entre unidades (PROMPT_CODEX.md: "Mantener unidades").
        """
        unidad = self.cantidad.unidad if self.cantidad else None
        return (self.ingrediente_id, unidad, self.tipo_escalado)

    def acumular(self, otro: ItemCompra) -> None:
        """Suma la cantidad de otro item equivalente a este."""
        if otro.clave_consolidacion != self.clave_consolidacion:
            raise ValorInvalido("Solo pueden acumularse items equivalentes.")
        if self.cantidad is not None and otro.cantidad is not None:
            self.cantidad = self.cantidad.sumar(otro.cantidad)

    def marcar_comprado(self, comprado: bool = True) -> None:
        """Marca el item como adquirido."""
        self.comprado = comprado

    def __str__(self) -> str:
        if self.cantidad is not None:
            return f"{self.nombre_ingrediente}: {self.cantidad}"
        return f"{self.nombre_ingrediente}: {self.tipo_escalado.etiqueta}"


@dataclass
class ListaCompra:
    """Conjunto consolidado de ingredientes faltantes."""

    items: list[ItemCompra] = field(default_factory=list)
    usuario_id: UUID | None = None
    fecha: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    id: UUID = field(default_factory=uuid4)

    @property
    def esta_vacia(self) -> bool:
        """Indica si la lista no contiene items."""
        return not self.items

    @property
    def items_pendientes(self) -> list[ItemCompra]:
        """Devuelve los items aun no comprados."""
        return [item for item in self.items if not item.comprado]

    def ordenar_por_nombre(self) -> None:
        """Ordena los items alfabeticamente para facilitar la compra."""
        self.items.sort(key=lambda item: item.nombre_ingrediente.lower())
