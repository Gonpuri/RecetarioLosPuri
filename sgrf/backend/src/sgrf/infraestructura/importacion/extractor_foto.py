"""Extraccion de texto de fotos via OCR.space (Cap. 7.7, version 2.0).

Implementa el puerto ExtractorTexto llamando a la API gratuita de
OCR.space (25.000 lecturas por mes, sin tarjeta). Se eligio una API
externa en lugar de Tesseract porque el entorno nativo de Render no
permite instalar programas a nivel de sistema operativo, y Tesseract no es
una libreria de Python: es un programa aparte.

Como cualquier OCR tradicional, funciona bien con texto impreso y se
degrada bastante con letra manuscrita -la limitacion se le muestra a la
persona en el borrador, no se oculta.
"""

from __future__ import annotations

import logging

from ...aplicacion.servicios_externos import ExtractorTexto, ServicioNoDisponible

registro = logging.getLogger(__name__)

URL_API = "https://api.ocr.space/parse/image"
TAMANIO_MAXIMO_BYTES = 5 * 1024 * 1024  # tope conservador; OCR.space valida el resto


class ExtractorTextoOcrSpace(ExtractorTexto):
    """Extrae texto de una imagen usando la API gratuita de OCR.space."""

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    def extraer(self, contenido: bytes) -> str:
        """Sube la imagen a OCR.space y devuelve el texto reconocido."""
        if len(contenido) > TAMANIO_MAXIMO_BYTES:
            raise ServicioNoDisponible(
                "La foto es demasiado pesada para el servicio de OCR gratuito. "
                "Probá con una imagen más liviana o recortada."
            )

        try:
            import requests
        except ImportError as error:
            raise ServicioNoDisponible(
                "Falta instalar la biblioteca de red en el servidor."
            ) from error

        try:
            respuesta = requests.post(
                URL_API,
                files={"file": ("receta.jpg", contenido)},
                data={
                    "apikey": self._api_key,
                    "language": "spa",
                    "OCREngine": "2",
                    "isOverlayRequired": "false",
                },
                timeout=30,
            )
            respuesta.raise_for_status()
            datos = respuesta.json()
        except Exception as error:
            registro.error("Fallo la llamada a OCR.space.", exc_info=error)
            raise ServicioNoDisponible(
                "No se pudo leer el texto de la foto. Probá de nuevo en un momento."
            ) from error

        if datos.get("IsErroredOnProcessing"):
            mensaje = datos.get("ErrorMessage") or "Error desconocido del servicio de OCR."
            mensaje = mensaje[0] if isinstance(mensaje, list) else mensaje
            raise ServicioNoDisponible(f"No se pudo leer la foto: {mensaje}")

        resultados = datos.get("ParsedResults") or []
        return "\n".join(r.get("ParsedText", "") for r in resultados).strip()
