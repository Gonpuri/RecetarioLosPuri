"""Validacion del formato de CLOUDINARY_URL.

Separada de settings.py para poder probarla sin cargar Django completo, y
para que la logica de deteccion no vuelva a duplicarse ni a olvidarse en
un lugar mientras se corrige en otro.
"""

from __future__ import annotations


def es_url_cloudinary_valida(valor: str) -> bool:
    """Indica si el valor tiene la forma esperada por la biblioteca de Cloudinary.

    El formato correcto lleva un unico '@':

        cloudinary://API_KEY:API_SECRET@NOMBRE_DE_CUENTA

    Dos errores frecuentes, ambos vistos en produccion:

    1. Pegar el correo completo de la cuenta en el lugar del "Cloud name"
       del Dashboard. Eso agrega un '@' de mas
       (.../API_SECRET@usuario@dominio.com) y hace que la biblioteca tome
       todo lo posterior al ultimo '@' como si fuera el nombre de cuenta.
    2. Que el nombre de cuenta real quede pegado al secreto sin el '@' que
       los separa, y el dominio del correo (por ejemplo 'gmail.com') quede
       como si fuera el nombre de cuenta. Los nombres de cuenta de
       Cloudinary nunca llevan un punto, asi que ese caso se detecta
       exigiendo que esa porcion no contenga uno.
    """
    if not valor.startswith("cloudinary://"):
        return False
    resto = valor.removeprefix("cloudinary://")
    if resto.count("@") != 1 or ":" not in resto:
        return False
    _, nombre_cuenta = resto.rsplit("@", 1)
    if not nombre_cuenta or "." in nombre_cuenta or " " in nombre_cuenta:
        return False
    return True
