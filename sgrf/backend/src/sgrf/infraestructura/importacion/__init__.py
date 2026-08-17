"""Adaptadores de infraestructura para la importacion de recetas.

Implementan los puertos declarados en `aplicacion.servicios_externos`:
extraer texto de un documento y pedirle a algo que lo estructure. El
Dominio no conoce ninguno de los dos.

PDF usa pdfplumber (extraccion) y la API de Claude (estructuracion, con
costo). Foto usa la API gratuita de OCR.space (extraccion) y un
estructurador por reglas simples, sin IA (decision del usuario: la
importacion desde foto no debe tener costo).
"""

from .asistente_ia import AsistenteEstructuracionClaude
from .estructurador_heuristico import EstructuradorHeuristico
from .extractor_foto import ExtractorTextoOcrSpace
from .extractor_pdf import ExtractorTextoPdf

__all__ = [
    "AsistenteEstructuracionClaude",
    "EstructuradorHeuristico",
    "ExtractorTextoOcrSpace",
    "ExtractorTextoPdf",
]
