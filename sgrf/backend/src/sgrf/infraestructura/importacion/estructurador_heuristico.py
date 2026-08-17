"""Estructuracion de recetas sin IA, por reglas simples (Cap. 7.7, version 2.0).

Implementa el puerto AsistenteEstructuracion sin llamar a ningun servicio
de pago: usa expresiones regulares para distinguir una linea de
ingrediente ("500 g harina") de una linea de paso ("Mezclar los secos").

Es deliberadamente menos preciso que el asistente de IA usado para PDF: la
importacion desde foto se eligio sin costo (decision del usuario), y el
precio de eso es una separacion mas tosca entre ingredientes y pasos. El
borrador siempre incluye una advertencia explicita para que la persona
sepa que tiene que revisarlo con cuidado, no lo esconde.
"""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from fractions import Fraction

from ...aplicacion.dto import IngredienteImportado, PreparacionImportada, RecetaImportada
from ...aplicacion.servicios_externos import AsistenteEstructuracion

# Mapea las palabras que puede traer el texto a los simbolos que reconoce
# el Dominio (Unidad.desde_simbolo). El orden importa: se prueban en orden
# y "gr"/"gramos" deben resolverse antes que una coincidencia mas corta.
UNIDADES_RECONOCIDAS = [
    (r"kilogramos?|kilos?|kg\.?", "kg"),
    (r"gramos?|grs?\.?|g\.?", "g"),
    (r"mililitros?|ml\.?", "ml"),
    (r"litros?|l\.?", "l"),
    (r"cucharaditas?|cditas?\.?", "cdita"),
    (r"cucharadas?|cdas?\.?", "cda"),
    (r"tazas?", "taza"),
    (r"pizcas?", "pizca"),
    (r"unidades?|u\.?", "u"),
]

PATRON_CANTIDAD = re.compile(
    r"^\s*[-•*]?\s*"
    r"(?P<cantidad>\d+[.,]?\d*|\d+\s*/\s*\d+)"
    r"\s*(?P<unidad>[a-záéíóúñ]+\.?)?"
    r"\s+(?P<resto>.+)$",
    re.IGNORECASE,
)

PATRON_RENDIMIENTO = re.compile(
    r"(?:rinde|para|alcanza para)?\s*(\d+)\s*"
    r"(porciones|personas|raciones|unidades)",
    re.IGNORECASE,
)

MENSAJE_ADVERTENCIA = (
    "Esta importación no usa inteligencia artificial: separa ingredientes "
    "de pasos con reglas simples, así que puede haberse equivocado. "
    "Revisá con cuidado antes de guardar, sobre todo el nombre y qué es "
    "ingrediente y qué es paso."
)


class EstructuradorHeuristico(AsistenteEstructuracion):
    """Separa ingredientes de pasos con expresiones regulares, sin costo."""

    def estructurar_receta(
        self, texto: str, nombres_ingredientes_catalogo: list[str]
    ) -> RecetaImportada:
        """Arma un borrador de Receta a partir del texto plano, sin IA."""
        lineas = [linea.strip() for linea in texto.splitlines() if linea.strip()]
        if not lineas:
            return RecetaImportada(
                nombre="Receta importada",
                descripcion="",
                rendimiento_base=Decimal(4),
                rendimiento_descripcion="porciones",
                fuente_sugerida="",
                preparaciones=(),
                advertencia=MENSAJE_ADVERTENCIA,
            )

        nombre = lineas[0]
        resto = lineas[1:]

        rendimiento_valor, rendimiento_descripcion = self._buscar_rendimiento(resto)

        ingredientes = []
        pasos = []
        for linea in resto:
            coincidencia = PATRON_CANTIDAD.match(linea)
            if coincidencia:
                ingredientes.append(self._a_ingrediente(coincidencia))
            else:
                pasos.append(linea)

        preparacion = PreparacionImportada(
            nombre="Preparación",
            ingredientes=tuple(ingredientes),
            pasos=tuple(pasos),
        )

        return RecetaImportada(
            nombre=nombre,
            descripcion="",
            rendimiento_base=rendimiento_valor,
            rendimiento_descripcion=rendimiento_descripcion,
            fuente_sugerida="",
            preparaciones=(preparacion,),
            advertencia=MENSAJE_ADVERTENCIA,
        )

    def _a_ingrediente(self, coincidencia: re.Match) -> IngredienteImportado:
        """Traduce una linea que matcheo el patron de cantidad."""
        cantidad = self._a_decimal(coincidencia.group("cantidad"))
        unidad_texto = coincidencia.group("unidad")
        unidad = self._normalizar_unidad(unidad_texto) if unidad_texto else None
        resto = coincidencia.group("resto").strip()

        # Si la palabra despues del numero no era una unidad reconocida
        # (por ejemplo "3 huevos"), en realidad es parte del nombre.
        if unidad_texto and unidad is None:
            resto = f"{unidad_texto} {resto}".strip()

        if cantidad is None or unidad is None:
            return IngredienteImportado(
                texto=resto or "Ingrediente sin identificar",
                ingrediente_id=None,
                cantidad=None,
                unidad=None,
                tipo_escalado="a_gusto",
            )

        return IngredienteImportado(
            texto=resto or "Ingrediente sin identificar",
            ingrediente_id=None,
            cantidad=cantidad,
            unidad=unidad,
            tipo_escalado="lineal",
        )

    def _normalizar_unidad(self, palabra: str) -> str | None:
        """Mapea una palabra en espanol al simbolo que reconoce el Dominio."""
        limpia = palabra.strip().lower()
        for patron, simbolo in UNIDADES_RECONOCIDAS:
            if re.fullmatch(patron, limpia, re.IGNORECASE):
                return simbolo
        return None

    def _buscar_rendimiento(self, lineas: list[str]) -> tuple[Decimal, str]:
        """Busca un patron tipo '4 porciones' en el texto; si no, usa un valor por defecto."""
        for linea in lineas:
            coincidencia = PATRON_RENDIMIENTO.search(linea)
            if coincidencia:
                return Decimal(coincidencia.group(1)), coincidencia.group(2).lower()
        return Decimal(4), "porciones"

    def _a_decimal(self, texto: str) -> Decimal | None:
        """Convierte '2', '1.5' o '1/2' a Decimal."""
        limpio = texto.strip().replace(",", ".")
        if "/" in limpio:
            try:
                return Decimal(str(float(Fraction(limpio.replace(" ", "")))))
            except (ValueError, ZeroDivisionError):
                return None
        try:
            return Decimal(limpio)
        except InvalidOperation:
            return None
