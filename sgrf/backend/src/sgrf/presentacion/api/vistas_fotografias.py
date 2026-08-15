"""Firma de subida de fotografias a Cloudinary.

El navegador sube la imagen directamente a Cloudinary; el backend solo
firma la operacion. Asi el archivo no atraviesa Render (cuyo plan gratuito
tiene poca memoria) y, sobre todo, el secreto de la cuenta jamas llega al
navegador.

La firma caduca a la hora y limita la carpeta y el formato, de modo que no
pueda reutilizarse para subir cualquier cosa a la cuenta.
"""

from __future__ import annotations

import time

from django.conf import settings
from rest_framework.response import Response

from .vistas_recetas import VistaBase

CARPETA = "sgrf/recetas"
FORMATOS_ADMITIDOS = "jpg,jpeg,png,webp"
VIGENCIA_SEGUNDOS = 3600


class FirmaFotografiaVista(VistaBase):
    """Entrega los datos necesarios para subir una imagen a Cloudinary."""

    def post(self, peticion):
        """Devuelve la firma de una subida.

        Si Cloudinary no esta configurado responde 503 con una indicacion
        concreta, en lugar de fallar de forma opaca al subir.
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

        configuracion = cloudinary.config()
        marca_temporal = int(time.time())

        parametros = {
            "timestamp": marca_temporal,
            "folder": CARPETA,
            "allowed_formats": FORMATOS_ADMITIDOS,
        }

        firma = cloudinary.utils.api_sign_request(
            parametros, configuracion.api_secret
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
