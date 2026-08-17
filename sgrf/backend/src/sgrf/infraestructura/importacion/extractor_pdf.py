"""Extraccion de texto de PDF (Cap. 7.7, version 2.0).

Implementa el puerto ExtractorTexto usando pdfplumber. Solo funciona con
PDF que ya contienen texto seleccionable -la mayoria de las recetas
copiadas de una pagina web o escritas en un procesador de texto-. Un PDF
que es una foto o un escaneo sin capa de texto devuelve una cadena vacia;
el caso de uso lo detecta y sugiere la importacion desde foto en su lugar.
"""

from __future__ import annotations

import io
import logging

from ...aplicacion.servicios_externos import ExtractorTexto, ServicioNoDisponible

registro = logging.getLogger(__name__)

TAMANIO_MAXIMO_BYTES = 15 * 1024 * 1024
MAXIMO_PAGINAS = 30


class ExtractorTextoPdf(ExtractorTexto):
    """Extrae el texto de un PDF pagina por pagina."""

    def extraer(self, contenido: bytes, nombre_archivo: str = "archivo.pdf") -> str:
        """Devuelve el texto de todas las paginas, separado por saltos de linea.

        `nombre_archivo` no se usa: un PDF siempre se abre igual sin
        importar como se llame. Esta implementacion lo acepta solo para
        cumplir la interfaz compartida con el extractor de fotos.
        """
        if len(contenido) > TAMANIO_MAXIMO_BYTES:
            raise ServicioNoDisponible(
                "El PDF supera los 15 MB. Probá con un archivo más liviano."
            )

        try:
            import pdfplumber
        except ImportError as error:
            raise ServicioNoDisponible(
                "Falta instalar la biblioteca de lectura de PDF en el servidor."
            ) from error

        try:
            with pdfplumber.open(io.BytesIO(contenido)) as documento:
                paginas = documento.pages[:MAXIMO_PAGINAS]
                textos = [pagina.extract_text() or "" for pagina in paginas]
        except Exception as error:
            registro.warning("No se pudo abrir el PDF.", exc_info=error)
            raise ServicioNoDisponible(
                "No se pudo abrir el archivo. Verificá que sea un PDF válido."
            ) from error

        return "\n".join(textos).strip()
