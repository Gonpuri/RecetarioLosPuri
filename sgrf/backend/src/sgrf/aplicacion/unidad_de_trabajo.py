"""Unidad de Trabajo (Unit of Work).

El Capitulo 5.4 asigna a la capa de Aplicacion la gestion de transacciones.
Esta interfaz agrupa los repositorios y delimita la transaccion, de modo que
un caso de uso que toca varios agregados confirme o revierta todo junto.

La implementacion concreta pertenece a Infraestructura (Etapa 3) y se
apoyara en las transacciones de Django.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..dominio.repositorios import (
    CategoriaRepositorio,
    EtiquetaRepositorio,
    FuenteRepositorio,
    IngredienteRepositorio,
    ListaCompraRepositorio,
    RecetaRepositorio,
    UsuarioRepositorio,
)


class UnidadDeTrabajo(ABC):
    """Agrupa los repositorios bajo una unica transaccion."""

    recetas: RecetaRepositorio
    ingredientes: IngredienteRepositorio
    usuarios: UsuarioRepositorio
    categorias: CategoriaRepositorio
    etiquetas: EtiquetaRepositorio
    fuentes: FuenteRepositorio
    listas_compra: ListaCompraRepositorio

    def __enter__(self) -> UnidadDeTrabajo:
        """Inicia la transaccion."""
        return self

    def __exit__(self, tipo_error, error, traza) -> None:
        """Revierte la transaccion si el bloque termino con error."""
        if error is not None:
            self.revertir()

    @abstractmethod
    def confirmar(self) -> None:
        """Confirma los cambios pendientes."""

    @abstractmethod
    def revertir(self) -> None:
        """Descarta los cambios pendientes."""
