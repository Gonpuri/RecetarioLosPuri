"""Normalizacion de decimales legibles, compartida por Cantidad y Rendimiento.

PostgreSQL devuelve siempre la precision completa de la columna: un
Rendimiento guardado como 50 vuelve de la base como Decimal('50.000'). Ese
'.000' final es inofensivo para el calculo, pero no para la lectura: en
formato argentino el punto es separador de miles, asi que "50.000" se lee
como cincuenta mil.

`Decimal.normalize()` por si solo tampoco alcanza: convierte los enteros
grandes a notacion cientifica (1000 se transforma en 1E+3), igual de
ilegible.

Este modulo resuelve ambos problemas en un unico lugar para que ninguna de
las dos clases pueda arreglarlo de una manera y la otra lo deje sin
corregir.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

PRECISION_DECIMAL = Decimal("0.001")


def normalizar_decimal_legible(valor: Decimal) -> Decimal:
    """Redondea a la precision del dominio y devuelve el texto mas legible.

    Sin ceros sobrantes ('50.000' se convierte en '50') y sin notacion
    cientifica (1000 nunca se expresa como '1E+3').
    """
    redondeado = valor.quantize(PRECISION_DECIMAL, rounding=ROUND_HALF_UP)
    sin_ceros = redondeado.normalize()
    if sin_ceros == sin_ceros.to_integral_value():
        return sin_ceros.quantize(Decimal(1))
    return sin_ceros
