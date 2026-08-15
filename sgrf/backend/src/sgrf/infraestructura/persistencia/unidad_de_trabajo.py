"""Unidad de Trabajo sobre Django.

Implementa el contrato de la capa de Aplicacion apoyandose en las
transacciones de Django. Un caso de uso que toca varios agregados confirma
o revierte todo junto.

`transaction.atomic` se abre al entrar en el bloque `with` y se cierra al
salir. Si el bloque termina con excepcion, se revierte por completo: por
eso una receta invalida nunca queda a medio guardar.
"""

from __future__ import annotations

from django.db import transaction

from ...aplicacion.unidad_de_trabajo import UnidadDeTrabajo
from .repositorios import (
    CategoriaRepositorioDjango,
    EtiquetaRepositorioDjango,
    FuenteRepositorioDjango,
    IngredienteRepositorioDjango,
    ListaCompraRepositorioDjango,
    RecetaRepositorioDjango,
    UsuarioRepositorioDjango,
)


class UnidadDeTrabajoDjango(UnidadDeTrabajo):
    """Agrupa los repositorios de PostgreSQL bajo una unica transaccion."""

    def __init__(self) -> None:
        self.recetas = RecetaRepositorioDjango()
        self.ingredientes = IngredienteRepositorioDjango()
        self.usuarios = UsuarioRepositorioDjango()
        self.categorias = CategoriaRepositorioDjango()
        self.etiquetas = EtiquetaRepositorioDjango()
        self.fuentes = FuenteRepositorioDjango()
        self.listas_compra = ListaCompraRepositorioDjango()
        self._atomico = None

    def __enter__(self) -> UnidadDeTrabajoDjango:
        """Abre la transaccion."""
        self._atomico = transaction.atomic()
        self._atomico.__enter__()
        return self

    def __exit__(self, tipo_error, error, traza) -> None:
        """Cierra la transaccion, revirtiendo si hubo error."""
        if self._atomico is None:
            return
        self._atomico.__exit__(tipo_error, error, traza)
        self._atomico = None

    def confirmar(self) -> None:
        """Confirma los cambios.

        Django confirma al cerrarse el bloque atomico sin excepciones, de
        modo que aqui no hace falta accion adicional. El metodo se conserva
        porque forma parte del contrato y otras implementaciones si lo
        necesitan.
        """

    def revertir(self) -> None:
        """Marca la transaccion para revertirse."""
        transaction.set_rollback(True)
