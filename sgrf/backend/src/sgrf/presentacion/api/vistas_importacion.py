"""Importacion de recetas (Cap. 7.7, version 2.0).

Extrae el texto de un archivo -o recibe el texto ya transcripto de un
dictado- y le pide a algo que lo estructure. Nunca persiste una Receta:
devuelve un borrador para que la persona lo revise en el formulario antes
de guardarlo con el flujo normal de creacion (POST /api/recetas/).

PDF y dictado usan la API de Claude para estructurar (con costo). Foto usa
reglas simples sin IA, por decision explicita del usuario de no generar
costo en esa via.
"""

from __future__ import annotations

import logging

from django.conf import settings
from rest_framework.response import Response

from ...aplicacion.casos_uso import EstructurarRecetaDictada, ImportarRecetaDesdeArchivo
from ...aplicacion.excepciones import UsuarioInactivo
from ...aplicacion.servicios_externos import ServicioNoDisponible
from ...dominio.excepciones import ValorInvalido
from ...infraestructura.importacion import (
    AsistenteEstructuracionClaude,
    EstructuradorHeuristico,
    ExtractorTextoOcrSpace,
    ExtractorTextoPdf,
)
from . import serializadores as s
from .soporte import correcto
from .vistas_recetas import VistaBase

registro = logging.getLogger(__name__)


def _sin_anthropic() -> Response:
    """Respuesta uniforme cuando falta la clave de la API de Claude."""
    return Response(
        {
            "error": (
                "Esta importación no está configurada. "
                "Falta la variable ANTHROPIC_API_KEY en el servidor."
            )
        },
        status=503,
    )


class _VistaImportacionBase(VistaBase):
    """Comparte el manejo de errores entre las vistas de importacion.

    Cada subclase solo define el serializador de entrada y los adaptadores
    concretos (extractor de texto y estructurador) a usar.
    """

    def _ejecutar(
        self,
        caso_de_uso: ImportarRecetaDesdeArchivo,
        contenido: bytes,
        nombre_archivo: str,
    ):
        """Corre el caso de uso traduciendo cada excepcion a su codigo HTTP.

        422 para un archivo del que no se pudo sacar nada util, 403 si el
        usuario esta desactivado, 502 si el servicio externo fallo. Nunca
        un 500 opaco: siempre queda claro que fue lo que salio mal.
        """
        try:
            borrador = caso_de_uso.ejecutar(
                self.solicitante_id, contenido, nombre_archivo
            )
        except ValorInvalido as fallo:
            return Response({"error": str(fallo)}, status=422)
        except UsuarioInactivo as fallo:
            return Response({"error": str(fallo)}, status=403)
        except ServicioNoDisponible as fallo:
            registro.warning("Fallo la importacion: %s", fallo)
            return Response({"error": str(fallo)}, status=502)
        return correcto(borrador)


class ImportarPdfVista(_VistaImportacionBase):
    """Recibe un PDF y devuelve un borrador de Receta para revisar."""

    def post(self, peticion):
        """Extrae el texto del PDF y lo estructura con la API de Claude.

        Si `ANTHROPIC_API_KEY` no esta configurada responde 503, igual que
        con Cloudinary: una funcion opcional mal configurada no debe
        romper el resto del sistema.
        """
        if not settings.ANTHROPIC_API_KEY:
            return _sin_anthropic()

        datos = self.validar(s.ImportarPdfEntrada)
        archivo = datos["archivo"]
        caso_de_uso = ImportarRecetaDesdeArchivo(
            self.uow,
            extractor_texto=ExtractorTextoPdf(),
            asistente_ia=AsistenteEstructuracionClaude(settings.ANTHROPIC_API_KEY),
        )
        return self._ejecutar(caso_de_uso, archivo.read(), archivo.name)


class ImportarFotoVista(_VistaImportacionBase):
    """Recibe una foto y devuelve un borrador de Receta para revisar.

    Sin IA ni costo, por decision explicita del usuario: la lectura usa la
    capa gratuita de OCR.space y la separacion entre ingredientes y pasos
    se hace con reglas simples. Es menos precisa que la importacion desde
    PDF -el borrador siempre trae una advertencia que lo deja claro.
    """

    def post(self, peticion):
        """Extrae el texto de la foto con OCR y lo estructura sin IA."""
        if not settings.OCR_SPACE_API_KEY:
            return Response(
                {
                    "error": (
                        "La importación desde foto no está configurada. "
                        "Falta la variable OCR_SPACE_API_KEY en el servidor."
                    )
                },
                status=503,
            )

        datos = self.validar(s.ImportarFotoEntrada)
        archivo = datos["archivo"]
        caso_de_uso = ImportarRecetaDesdeArchivo(
            self.uow,
            extractor_texto=ExtractorTextoOcrSpace(settings.OCR_SPACE_API_KEY),
            asistente_ia=EstructuradorHeuristico(),
        )
        return self._ejecutar(caso_de_uso, archivo.read(), archivo.name)


class ImportarDictadoVista(VistaBase):
    """Recibe una receta dictada y devuelve un borrador para revisar.

    El navegador transcribe la voz gratis, con su propia funcion de
    reconocimiento de voz: aca solo llega texto plano, sin ningun archivo.
    Estructurar un dictado hablado de corrido -sin saltos de linea como
    los que tiene una receta escrita- no se puede resolver de forma
    confiable con reglas simples, asi que usa la misma API de Claude que
    el PDF, con el mismo costo por receta.
    """

    def post(self, peticion):
        """Estructura el texto ya transcripto con la API de Claude."""
        if not settings.ANTHROPIC_API_KEY:
            return _sin_anthropic()

        datos = self.validar(s.ImportarDictadoEntrada)
        caso_de_uso = EstructurarRecetaDictada(
            self.uow,
            asistente_ia=AsistenteEstructuracionClaude(settings.ANTHROPIC_API_KEY),
        )
        try:
            borrador = caso_de_uso.ejecutar(self.solicitante_id, datos["texto"])
        except ValorInvalido as fallo:
            return Response({"error": str(fallo)}, status=422)
        except UsuarioInactivo as fallo:
            return Response({"error": str(fallo)}, status=403)
        except ServicioNoDisponible as fallo:
            registro.warning("Fallo la estructuracion del dictado: %s", fallo)
            return Response({"error": str(fallo)}, status=502)
        return correcto(borrador)
