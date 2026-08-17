"""Puertos hacia servicios externos de extraccion e IA (Cap. 7.7, version 2.0).

Igual que los Repositorios invierten la dependencia hacia la persistencia,
estas interfaces invierten la dependencia hacia los servicios externos que
usa la importacion de recetas: la capa de Aplicacion declara que necesita,
la Infraestructura decide con que biblioteca o API lo resuelve.

Ningun caso de uso de importacion sabe que existe pdfplumber ni la API de
Anthropic: solo conoce estas dos interfaces.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from .dto import RecetaImportada


class ServicioNoDisponible(Exception):
    """El servicio externo no esta configurado o no pudo completarse.

    Cubre tanto la falta de configuracion (variable de entorno ausente)
    como fallas de la biblioteca o la API externa en tiempo de ejecucion.
    """


class ExtractorTexto(ABC):
    """Obtiene el texto plano de un documento (PDF, imagen, pagina web)."""

    @abstractmethod
    def extraer(self, contenido: bytes, nombre_archivo: str = "archivo") -> str:
        """Devuelve el texto extraido. Cadena vacia si no se encontro texto.

        `nombre_archivo` es el nombre original tal como lo subio la
        persona. Algunos extractores lo necesitan para inferir el formato
        (por ejemplo, distinguir JPEG de PNG); otros lo ignoran.
        """


class AsistenteEstructuracion(ABC):
    """Traduce texto libre a la estructura de una Receta."""

    @abstractmethod
    def estructurar_receta(
        self, texto: str, nombres_ingredientes_catalogo: list[str]
    ) -> RecetaImportada:
        """Interpreta el texto y arma un borrador de Receta.

        `nombres_ingredientes_catalogo` se le pasa al asistente para que
        prefiera reutilizar nombres ya existentes en el catalogo en lugar
        de inventar variantes ("Harina 000" en vez de "harina de trigo").
        """
