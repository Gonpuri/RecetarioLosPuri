"""Servicio de dominio GeneradorListaCompras.

Consolida en una unica Lista de Compras los ingredientes que el usuario
marco como faltantes.

Reglas que sostiene:
- RN-006: la lista se construye unicamente con los ingredientes
  seleccionados por el usuario.
- PROMPT_CODEX.md: consolidar ingredientes repetidos manteniendo unidades.
"""

from __future__ import annotations

from uuid import UUID

from ..entidades.lista_compra import ItemCompra, ListaCompra
from .escalador_recetas import RecetaEscalada


class GeneradorListaCompras:
    """Construye Listas de Compras consolidadas."""

    def generar(
        self,
        receta_escalada: RecetaEscalada,
        ingredientes_seleccionados: set[UUID],
        nombres_ingredientes: dict[UUID, str],
        usuario_id: UUID | None = None,
    ) -> ListaCompra:
        """Genera la lista a partir de una receta escalada.

        Args:
            receta_escalada: resultado temporal del EscaladorRecetas.
            ingredientes_seleccionados: identidades de IngredientePreparacion
                que el usuario marco como faltantes (RN-006).
            nombres_ingredientes: nombres del catalogo, indexados por la
                identidad del Ingrediente.
            usuario_id: autor de la lista, si corresponde.
        """
        items = [
            self._construir_item(ingrediente, nombres_ingredientes)
            for preparacion in receta_escalada.preparaciones
            for ingrediente in preparacion.ingredientes
            if ingrediente.ingrediente_preparacion_id in ingredientes_seleccionados
        ]
        lista = ListaCompra(items=self._consolidar(items), usuario_id=usuario_id)
        lista.ordenar_por_nombre()
        return lista

    def combinar(self, listas: list[ListaCompra]) -> ListaCompra:
        """Une varias listas en una sola, consolidando los items repetidos.

        Permite planificar la compra de varias recetas a la vez.
        """
        items = [item for lista in listas for item in lista.items]
        combinada = ListaCompra(items=self._consolidar(items))
        combinada.ordenar_por_nombre()
        return combinada

    def _construir_item(self, ingrediente, nombres: dict[UUID, str]) -> ItemCompra:
        """Traduce un ingrediente escalado a un renglon de la lista."""
        return ItemCompra(
            ingrediente_id=ingrediente.ingrediente_id,
            nombre_ingrediente=nombres.get(
                ingrediente.ingrediente_id, "Ingrediente sin nombre"
            ),
            cantidad=ingrediente.cantidad,
            tipo_escalado=ingrediente.tipo_escalado,
        )

    def _consolidar(self, items: list[ItemCompra]) -> list[ItemCompra]:
        """Agrupa los items equivalentes sumando sus cantidades.

        Dos items se consideran equivalentes cuando comparten Ingrediente,
        Unidad y TipoEscalado. No se convierten unidades entre si.
        """
        consolidados: dict[tuple, ItemCompra] = {}
        for item in items:
            clave = item.clave_consolidacion
            existente = consolidados.get(clave)
            if existente is None:
                consolidados[clave] = ItemCompra(
                    ingrediente_id=item.ingrediente_id,
                    nombre_ingrediente=item.nombre_ingrediente,
                    cantidad=item.cantidad,
                    tipo_escalado=item.tipo_escalado,
                )
            else:
                existente.acumular(item)
        return list(consolidados.values())
