"""Pruebas de integracion de los Casos de Uso de la Lista de Compras.

Reportado en producción: los productos de la lista no se podían marcar
como comprados ni sacar de la lista. La causa era que esos endpoints
nunca se habían construido.
"""

from uuid import uuid4

import pytest

from sgrf.aplicacion.casos_uso import MarcarItemComprado, QuitarItemDeLista
from sgrf.aplicacion.excepciones import PermisoDenegado, RecursoNoEncontrado
from sgrf.dominio.entidades import RolUsuario, Usuario


class TestMarcarItemComprado:
    """El marcado de comprado se persiste, a diferencia del de faltantes."""

    def test_marca_el_item_como_comprado(self, uow, familiar, lista_creada):
        item_id = lista_creada.items[0].id
        MarcarItemComprado(uow).ejecutar(familiar.id, lista_creada.id, item_id)
        recuperada = uow.listas_compra.obtener(lista_creada.id)
        assert recuperada.items[0].comprado

    def test_el_marcado_sobrevive_a_una_relectura(self, uow, familiar, lista_creada):
        """El punto central del bug: que no se pierda al recargar."""
        item_id = lista_creada.items[0].id
        MarcarItemComprado(uow).ejecutar(familiar.id, lista_creada.id, item_id, True)
        primera_lectura = uow.listas_compra.obtener(lista_creada.id)
        segunda_lectura = uow.listas_compra.obtener(lista_creada.id)
        assert primera_lectura.items[0].comprado
        assert segunda_lectura.items[0].comprado

    def test_se_puede_desmarcar(self, uow, familiar, lista_creada):
        item_id = lista_creada.items[0].id
        MarcarItemComprado(uow).ejecutar(familiar.id, lista_creada.id, item_id, True)
        MarcarItemComprado(uow).ejecutar(familiar.id, lista_creada.id, item_id, False)
        recuperada = uow.listas_compra.obtener(lista_creada.id)
        assert not recuperada.items[0].comprado

    def test_lista_inexistente_falla(self, uow, familiar):
        with pytest.raises(RecursoNoEncontrado):
            MarcarItemComprado(uow).ejecutar(familiar.id, uuid4(), uuid4())

    def test_item_inexistente_falla(self, uow, familiar, lista_creada):
        from sgrf.dominio.excepciones import ElementoNoEncontrado

        with pytest.raises(ElementoNoEncontrado):
            MarcarItemComprado(uow).ejecutar(familiar.id, lista_creada.id, uuid4())

    def test_no_se_puede_marcar_la_lista_de_otra_persona(self, uow, lista_creada):
        """Las listas son personales (decision D-18)."""
        otro = Usuario(nombre="Luis", correo="luis@familia.test")
        uow.usuarios.guardar(otro)
        item_id = lista_creada.items[0].id
        with pytest.raises(PermisoDenegado):
            MarcarItemComprado(uow).ejecutar(otro.id, lista_creada.id, item_id)


class TestQuitarItemDeLista:
    """Sacar un producto de la lista sin marcarlo como comprado."""

    def test_quita_el_item_de_la_lista(self, uow, familiar, lista_creada):
        item_id = lista_creada.items[0].id
        QuitarItemDeLista(uow).ejecutar(familiar.id, lista_creada.id, item_id)
        recuperada = uow.listas_compra.obtener(lista_creada.id)
        assert recuperada.items == []

    def test_la_eliminacion_se_persiste(self, uow, familiar, lista_creada):
        """No alcanza con sacarlo en memoria: debe desaparecer al releer."""
        item_id = lista_creada.items[0].id
        QuitarItemDeLista(uow).ejecutar(familiar.id, lista_creada.id, item_id)
        assert uow.listas_compra.obtener(lista_creada.id).items == []

    def test_no_se_puede_quitar_de_la_lista_de_otra_persona(
        self, uow, lista_creada
    ):
        otro = Usuario(nombre="Luis", correo="luis@familia.test")
        uow.usuarios.guardar(otro)
        item_id = lista_creada.items[0].id
        with pytest.raises(PermisoDenegado):
            QuitarItemDeLista(uow).ejecutar(otro.id, lista_creada.id, item_id)

    def test_lista_inexistente_falla(self, uow, familiar):
        with pytest.raises(RecursoNoEncontrado):
            QuitarItemDeLista(uow).ejecutar(familiar.id, uuid4(), uuid4())
