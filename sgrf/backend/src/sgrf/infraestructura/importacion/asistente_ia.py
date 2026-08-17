"""Estructuracion de recetas con IA (Cap. 7.7, version 2.0).

Implementa el puerto AsistenteEstructuracion llamando a la API de Claude.
Es, a proposito, la unica pieza del sistema que depende de un servicio de
pago: por eso queda aislada en un unico adaptador, facil de reemplazar o
apagar sin tocar el resto del sistema (ADR-005: independencia de la
tecnologia).

Si `ANTHROPIC_API_KEY` no esta configurada, el adaptador nunca se
instancia: la vista lo detecta antes y responde 503, igual que con
Cloudinary.
"""

from __future__ import annotations

import json
import logging
from decimal import Decimal, InvalidOperation

from ...aplicacion.dto import IngredienteImportado, PreparacionImportada, RecetaImportada
from ...aplicacion.servicios_externos import AsistenteEstructuracion, ServicioNoDisponible

registro = logging.getLogger(__name__)

MODELO = "claude-sonnet-4-6"
MAXIMO_CARACTERES_TEXTO = 20000

UNIDADES_VALIDAS = {"g", "kg", "ml", "l", "cda", "cdita", "taza", "pizca", "u"}
TIPOS_ESCALADO_VALIDOS = {"lineal", "fijo", "a_gusto", "cantidad_necesaria"}

INSTRUCCIONES = """Sos un asistente que transcribe recetas de cocina a una estructura de datos.

Se te va a dar el texto de una receta, extraido de un PDF, y una lista de \
ingredientes que ya existen en el catalogo del usuario. Tu tarea es devolver \
UNICAMENTE un objeto JSON (sin texto antes ni despues, sin backticks) con \
esta forma exacta:

{
  "nombre": "string, el nombre del plato",
  "descripcion": "string, una oracion breve o vacio si no hay",
  "rendimiento_base": numero, cuanto rinde la receta,
  "rendimiento_descripcion": "string, ej. 'porciones', 'unidades', 'tortas'",
  "fuente_sugerida": "string, de donde parece venir la receta, o vacio",
  "preparaciones": [
    {
      "nombre": "string, ej. 'Masa', 'Relleno', o el nombre del plato si no hay etapas",
      "ingredientes": [
        {
          "texto": "string, el nombre del ingrediente TAL COMO aparece en el \
catalogo si hay coincidencia, o como lo dice la receta si no la hay",
          "cantidad": numero o null,
          "unidad": "una de g, kg, ml, l, cda, cdita, taza, pizca, u -o null-",
          "tipo_escalado": "lineal" si la cantidad crece con las porciones, \
"fijo" si no cambia (ej. una pizca de levadura), "a_gusto" o \
"cantidad_necesaria" si la receta no da una cantidad numerica,
          "observacion": "string, aclaraciones como 'a temperatura ambiente', o vacio"
        }
      ],
      "pasos": ["string, un paso por elemento, en orden"]
    }
  ],
  "advertencia": "string si algo del texto quedo ambiguo o incompleto, o null"
}

Reglas importantes:
- Si un ingrediente coincide (aunque sea de forma aproximada) con uno del \
catalogo que te paso, usa EXACTAMENTE ese nombre de catalogo en "texto".
- cantidad y unidad van juntos: los dos con numero, o los dos null. Nunca uno \
solo.
- Si la receta no separa en etapas, poné todo en una unica preparacion.
- Si no podes determinar el rendimiento con confianza, poné 4 y usa \
"advertencia" para avisarlo.
- No inventes ingredientes ni pasos que no esten en el texto.
"""


class AsistenteEstructuracionClaude(AsistenteEstructuracion):
    """Le pide a la API de Claude que estructure el texto de una receta."""

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    def estructurar_receta(
        self, texto: str, nombres_ingredientes_catalogo: list[str]
    ) -> RecetaImportada:
        """Llama a la API y traduce la respuesta al DTO del dominio de la app."""
        try:
            import anthropic
        except ImportError as error:
            raise ServicioNoDisponible(
                "Falta instalar la biblioteca de Anthropic en el servidor."
            ) from error

        cliente = anthropic.Anthropic(api_key=self._api_key)
        texto_recortado = texto[:MAXIMO_CARACTERES_TEXTO]
        catalogo_texto = ", ".join(nombres_ingredientes_catalogo) or "(vacío)"

        try:
            respuesta = cliente.messages.create(
                model=MODELO,
                max_tokens=4000,
                system=INSTRUCCIONES,
                messages=[
                    {
                        "role": "user",
                        "content": (
                            f"Ingredientes ya existentes en el catálogo: "
                            f"{catalogo_texto}\n\n"
                            f"Texto de la receta:\n{texto_recortado}"
                        ),
                    }
                ],
            )
        except Exception as error:
            registro.error("Fallo la llamada a la API de Claude.", exc_info=error)
            raise ServicioNoDisponible(
                "No se pudo procesar la receta con el asistente de IA. "
                "Probá de nuevo en un momento."
            ) from error

        texto_respuesta = "".join(
            bloque.text for bloque in respuesta.content if bloque.type == "text"
        )
        return self._parsear(texto_respuesta)

    def _parsear(self, texto_json: str) -> RecetaImportada:
        """Convierte la respuesta cruda de la IA en el DTO tipado."""
        limpio = texto_json.strip().removeprefix("```json").removesuffix("```").strip()
        try:
            datos = json.loads(limpio)
        except json.JSONDecodeError as error:
            registro.error(
                "La respuesta de la IA no fue JSON valido: %s", texto_json[:500]
            )
            raise ServicioNoDisponible(
                "El asistente de IA no pudo interpretar esta receta con claridad. "
                "Probá revisarla manualmente."
            ) from error

        return RecetaImportada(
            nombre=str(datos.get("nombre") or "Receta sin nombre").strip(),
            descripcion=str(datos.get("descripcion") or "").strip(),
            rendimiento_base=self._decimal_seguro(datos.get("rendimiento_base"), 4),
            rendimiento_descripcion=(
                str(datos.get("rendimiento_descripcion") or "porciones").strip()
            ),
            fuente_sugerida=str(datos.get("fuente_sugerida") or "").strip(),
            preparaciones=tuple(
                self._preparacion(p) for p in datos.get("preparaciones") or []
            ),
            advertencia=(
                str(datos["advertencia"]).strip()
                if datos.get("advertencia")
                else None
            ),
        )

    def _preparacion(self, datos: dict) -> PreparacionImportada:
        """Traduce una preparacion del JSON crudo, tolerando campos ausentes."""
        return PreparacionImportada(
            nombre=str(datos.get("nombre") or "Preparación").strip(),
            ingredientes=tuple(
                self._ingrediente(i) for i in datos.get("ingredientes") or []
            ),
            pasos=tuple(
                str(paso).strip() for paso in datos.get("pasos") or [] if str(paso).strip()
            ),
        )

    def _ingrediente(self, datos: dict) -> IngredienteImportado:
        """Traduce un ingrediente del JSON crudo, saneando tipo y unidad."""
        tipo = str(datos.get("tipo_escalado") or "lineal").strip()
        if tipo not in TIPOS_ESCALADO_VALIDOS:
            tipo = "lineal"

        cantidad = self._decimal_o_none(datos.get("cantidad"))
        unidad = datos.get("unidad")
        unidad = unidad.strip() if isinstance(unidad, str) and unidad.strip() else None
        if unidad not in UNIDADES_VALIDAS:
            unidad = None

        # cantidad y unidad van juntos: si falta cualquiera de los dos, no
        # hay cantidad utilizable (evita que el Dominio rechace el borrador
        # al intentar reconstruir la Cantidad).
        if cantidad is None or unidad is None:
            cantidad, unidad = None, None
            if tipo in ("lineal", "fijo"):
                tipo = "a_gusto"

        return IngredienteImportado(
            texto=str(datos.get("texto") or "").strip() or "Ingrediente sin nombre",
            ingrediente_id=None,
            cantidad=cantidad,
            unidad=unidad,
            tipo_escalado=tipo,
            observacion=str(datos.get("observacion") or "").strip(),
        )

    def _decimal_seguro(self, valor, por_defecto) -> Decimal:
        """Convierte a Decimal tolerando texto invalido, sin nunca fallar."""
        resultado = self._decimal_o_none(valor)
        return resultado if resultado is not None else Decimal(por_defecto)

    def _decimal_o_none(self, valor) -> Decimal | None:
        """Convierte a Decimal o devuelve None si no es un numero valido."""
        if valor is None:
            return None
        try:
            return Decimal(str(valor))
        except (InvalidOperation, ValueError):
            return None
