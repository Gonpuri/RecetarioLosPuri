"""Pruebas del estructurador heuristico (Cap. 7.7, version 2.0).

No requieren Django ni servicios externos: son pruebas puras de las
expresiones regulares y el parsing de cantidades. Corren junto con las de
dominio y aplicacion, sin base de datos.
"""

import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from sgrf.infraestructura.importacion.estructurador_heuristico import (  # noqa: E402
    EstructuradorHeuristico,
)


class TestEstructuradorHeuristico:
    """Separacion de ingredientes y pasos por reglas simples, sin IA."""

    def test_usa_la_primera_linea_como_nombre(self):
        borrador = EstructuradorHeuristico().estructurar_receta(
            "Pan casero\n500 g harina\nMezclar todo.", []
        )
        assert borrador.nombre == "Pan casero"

    def test_reconoce_una_linea_de_ingrediente_simple(self):
        borrador = EstructuradorHeuristico().estructurar_receta(
            "Pan casero\n500 g harina\nMezclar todo.", []
        )
        ingrediente = borrador.preparaciones[0].ingredientes[0]
        assert ingrediente.cantidad == Decimal("500")
        assert ingrediente.unidad == "g"
        assert ingrediente.texto == "harina"

    def test_reconoce_fracciones(self):
        borrador = EstructuradorHeuristico().estructurar_receta(
            "Torta\n1/2 taza azúcar\nMezclar.", []
        )
        ingrediente = borrador.preparaciones[0].ingredientes[0]
        assert ingrediente.cantidad == Decimal("0.5")
        assert ingrediente.unidad == "taza"

    def test_reconoce_decimales_con_coma(self):
        borrador = EstructuradorHeuristico().estructurar_receta(
            "Torta\n1,5 kg harina\nMezclar.", []
        )
        assert borrador.preparaciones[0].ingredientes[0].cantidad == Decimal("1.5")

    def test_numero_sin_unidad_reconocida_pasa_a_ser_parte_del_nombre(self):
        """'3 huevos' no tiene una unidad reconocida: 'huevos' es el nombre."""
        borrador = EstructuradorHeuristico().estructurar_receta(
            "Torta\n3 huevos\nMezclar.", []
        )
        ingrediente = borrador.preparaciones[0].ingredientes[0]
        assert ingrediente.texto == "huevos"
        assert ingrediente.cantidad is None
        assert ingrediente.tipo_escalado == "a_gusto"

    def test_linea_sin_numero_se_interpreta_como_paso(self):
        borrador = EstructuradorHeuristico().estructurar_receta(
            "Pan casero\n500 g harina\nMezclar los ingredientes secos.", []
        )
        assert borrador.preparaciones[0].pasos == (
            "Mezclar los ingredientes secos.",
        )

    def test_busca_el_rendimiento_en_el_texto(self):
        borrador = EstructuradorHeuristico().estructurar_receta(
            "Pan casero\nRinde 8 porciones\n500 g harina\nMezclar.", []
        )
        assert borrador.rendimiento_base == Decimal("8")
        assert borrador.rendimiento_descripcion == "porciones"

    def test_usa_rendimiento_por_defecto_si_no_encuentra_uno(self):
        borrador = EstructuradorHeuristico().estructurar_receta(
            "Pan casero\n500 g harina\nMezclar.", []
        )
        assert borrador.rendimiento_base == Decimal("4")
        assert borrador.rendimiento_descripcion == "porciones"

    def test_siempre_incluye_una_advertencia(self):
        """A diferencia del asistente de IA, esta via siempre avisa sus limites."""
        borrador = EstructuradorHeuristico().estructurar_receta(
            "Pan casero\n500 g harina\nMezclar.", []
        )
        assert borrador.advertencia is not None
        assert "revis" in borrador.advertencia.lower()

    def test_texto_vacio_no_rompe(self):
        borrador = EstructuradorHeuristico().estructurar_receta("   \n\n  ", [])
        assert borrador.nombre == "Receta importada"
        assert borrador.preparaciones == ()

    def test_ingrediente_a_gusto_sin_numero(self):
        """Una linea como 'Sal a gusto' no matchea el patron de cantidad."""
        borrador = EstructuradorHeuristico().estructurar_receta(
            "Pan casero\n500 g harina\nSal a gusto\nMezclar.", []
        )
        # "Sal a gusto" no empieza con un numero: se interpreta como paso,
        # no como ingrediente. Es la limitacion esperada de este metodo.
        assert "Sal a gusto" in borrador.preparaciones[0].pasos
