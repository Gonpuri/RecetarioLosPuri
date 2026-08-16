"""Pruebas unitarias de la entidad ListaCompra."""

from uuid import uuid4

import pytest

from sgrf.dominio.entidades import ItemCompra, ListaCompra
from sgrf.dominio.excepciones import ElementoNoEncontrado


@pytest.fixture
def item_harina():
    """Item de compra de ejemplo."""
    from decimal import Decimal

    from sgrf.dominio.objetos_valor import Cantidad, Unidad

    return ItemCompra(
        ingrediente_id=uuid4(),
        nombre_ingrediente="Harina 000",
        cantidad=Cantidad(Decimal("500"), Unidad.GRAMO),
    )


class TestMarcarComprado:
    """El marcado de comprado no saca el item de la lista, solo lo distingue."""

    def test_marcar_comprado_no_lo_elimina(self, item_harina):
        lista = ListaCompra(items=[item_harina])
        item_harina.marcar_comprado()
        assert item_harina.comprado
        assert item_harina in lista.items

    def test_items_pendientes_excluye_los_comprados(self, item_harina):
        lista = ListaCompra(items=[item_harina])
        assert lista.items_pendientes == [item_harina]
        item_harina.marcar_comprado()
        assert lista.items_pendientes == []

    def test_se_puede_desmarcar(self, item_harina):
        item_harina.marcar_comprado(True)
        item_harina.marcar_comprado(False)
        assert not item_harina.comprado


class TestQuitarItem:
    """Sacar un producto de la lista sin marcarlo como comprado."""

    def test_quitar_item_lo_elimina_de_la_lista(self, item_harina):
        lista = ListaCompra(items=[item_harina])
        lista.quitar_item(item_harina.id)
        assert lista.items == []

    def test_quitar_item_inexistente_falla(self, item_harina):
        lista = ListaCompra(items=[item_harina])
        with pytest.raises(ElementoNoEncontrado):
            lista.quitar_item(uuid4())

    def test_obtener_item_devuelve_el_correcto(self, item_harina):
        lista = ListaCompra(items=[item_harina])
        assert lista.obtener_item(item_harina.id) is item_harina
