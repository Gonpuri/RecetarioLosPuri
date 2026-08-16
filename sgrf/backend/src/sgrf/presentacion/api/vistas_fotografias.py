"""Firma de subida de fotografias a Cloudinary.

El navegador sube la imagen directamente a Cloudinary; el backend solo
firma la operacion. Asi el archivo no atraviesa Render (cuyo plan gratuito
tiene poca memoria) y, sobre todo, el secreto de la cuenta jamas llega al
navegador.

La firma caduca a la hora y limita la carpeta y el formato, de modo que no
pueda reutilizarse para subir cualquier cosa a la cuenta.
"""

from __future__ import annotations

import logging
import time

from django.conf import settings
from rest_framework.response import Response

from .vistas_recetas import VistaBase

CARPETA = "sgrf/recetas"
FORMATOS_ADMITIDOS = "jpg,jpeg,png,webp"
VIGENCIA_SEGUNDOS = 3600

registro = logging.getLogger(__name__)


class FirmaFotografiaVista(VistaBase):
    """Entrega los datos necesarios para subir una imagen a Cloudinary."""

    def post(self, peticion):
        """Devuelve la firma de una subida.

        Si Cloudinary no esta configurado responde 503 con una indicacion
        concreta. Si la configuracion esta cargada pero la biblioteca de
        Cloudinary falla al usarla (credenciales invalidas, cuenta
        inexistente), responde 502 con el motivo en lugar de un 500 opaco:
        un problema de una integracion externa se distingue de un error
        interno del sistema.
        """
        import cloudinary
        import cloudinary.utils

        if not settings.CLOUDINARY_URL:
            return Response(
                {
                    "error": (
                        "El almacenamiento de fotografías no está configurado. "
                        "Falta la variable CLOUDINARY_URL en el servidor."
                    )
                },
                status=503,
            )

        try:
            configuracion = cloudinary.config()
            if not (
                configuracion.cloud_name
                and configuracion.api_key
                and configuracion.api_secret
            ):
                raise ValueError(
                    "La configuracion de Cloudinary quedo incompleta al "
                    "iniciar el servidor."
                )

            marca_temporal = int(time.time())
            parametros = {
                "timestamp": marca_temporal,
                "folder": CARPETA,
                "allowed_formats": FORMATOS_ADMITIDOS,
            }
            firma = cloudinary.utils.api_sign_request(
                parametros, configuracion.api_secret
            )
        except Exception as fallo:
            registro.error("No se pudo generar la firma de Cloudinary.", exc_info=fallo)
            return Response(
                {
                    "error": (
                        "No se pudo preparar la subida de la fotografía. "
                        "Revisá que CLOUDINARY_URL tenga las credenciales "
                        "correctas en el servidor."
                    )
                },
                status=502,
            )

        return Response(
            {
                **parametros,
                "signature": firma,
                "api_key": configuracion.api_key,
                "cloud_name": configuracion.cloud_name,
                "url_subida": (
                    f"https://api.cloudinary.com/v1_1/{configuracion.cloud_name}"
                    "/image/upload"
                ),
                "vigencia_segundos": VIGENCIA_SEGUNDOS,
            }
        )
