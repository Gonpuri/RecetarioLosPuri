"""Pruebas de la validacion de CLOUDINARY_URL.

No requieren Django: verifican unicamente la funcion pura, para poder
correr junto con las pruebas de dominio y aplicacion, sin base de datos.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from config.validacion_cloudinary import es_url_cloudinary_valida  # noqa: E402


class TestValidacionCloudinaryUrl:
    """Detecta el formato correcto y los errores mas frecuentes."""

    def test_url_bien_formada_es_valida(self):
        assert es_url_cloudinary_valida(
            "cloudinary://958447466323555:secreto-de-16-caracteres@dxyzab12"
        )

    def test_rechaza_valor_sin_el_prefijo_del_esquema(self):
        assert not es_url_cloudinary_valida(
            "958447466323555:secreto-de-16-caracteres@dxyzab12"
        )

    def test_rechaza_un_correo_pegado_como_nombre_de_cuenta(self):
        """Caso reportado: pegar el email en vez del 'Cloud name'.

        El '@' de mas hace que la biblioteca tome 'gmail.com' como si fuera
        el nombre de cuenta, y las subidas terminan apuntando a
        api.cloudinary.com/v1_1/gmail.com/..., que no existe.
        """
        assert not es_url_cloudinary_valida(
            "cloudinary://958447466323555:secreto@usuario@gmail.com"
        )

    def test_rechaza_el_dominio_del_correo_pegado_al_secreto(self):
        """Segundo caso reportado: el nombre de cuenta real quedo pegado al
        secreto sin el '@' que los separa, y 'gmail.com' -sin punto no
        seria un nombre de cuenta valido de Cloudinary- termino ocupando
        el lugar del nombre de cuenta.
        """
        assert not es_url_cloudinary_valida(
            "cloudinary://958447466323555:"
            "rktJ111I4FCsMGWuq2D-Btab_UYgonpuri@gmail.com"
        )

    def test_acepta_el_mismo_caso_una_vez_corregido(self):
        assert es_url_cloudinary_valida(
            "cloudinary://958447466323555:rktJ111I4FCsMGWuq2D-Btab_UY@gonpuri"
        )

    def test_rechaza_valor_vacio(self):
        assert not es_url_cloudinary_valida("")

    def test_rechaza_sin_separador_de_clave_y_secreto(self):
        assert not es_url_cloudinary_valida("cloudinary://solo-un-valor@dxyzab12")
