"""Excepciones del dominio del SGRF.

Toda violacion de una regla de negocio se expresa mediante una excepcion
de este modulo. La capa de Aplicacion las traduce a respuestas HTTP.
"""


class ErrorDeDominio(Exception):
    """Excepcion base de todas las violaciones de reglas del negocio."""


class ReglaDeNegocioViolada(ErrorDeDominio):
    """Se incumplio una regla de negocio documentada en ANALISIS.md."""

    def __init__(self, mensaje: str, codigo_regla: str | None = None) -> None:
        self.codigo_regla = codigo_regla
        super().__init__(
            f"[{codigo_regla}] {mensaje}" if codigo_regla else mensaje
        )


class ValorInvalido(ErrorDeDominio):
    """Un Objeto de Valor recibio datos que no puede representar."""


class UnidadesIncompatibles(ErrorDeDominio):
    """Se intento operar con dos Cantidades expresadas en distinta Unidad."""


class ElementoNoEncontrado(ErrorDeDominio):
    """Se referencio un elemento inexistente dentro del agregado."""


class RecetaArchivada(ErrorDeDominio):
    """Se intento modificar una Receta que se encuentra archivada."""
