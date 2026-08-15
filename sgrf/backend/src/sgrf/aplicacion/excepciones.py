"""Excepciones de la capa de Aplicacion.

Se distinguen de las del Dominio: aquellas expresan reglas del negocio;
estas expresan problemas de orquestacion (autorizacion, existencia del
recurso solicitado, conflictos de datos).
"""


class ErrorDeAplicacion(Exception):
    """Excepcion base de la capa de Aplicacion."""


class PermisoDenegado(ErrorDeAplicacion):
    """El usuario carece de permisos para ejecutar el caso de uso."""


class RecursoNoEncontrado(ErrorDeAplicacion):
    """No existe el recurso solicitado."""

    def __init__(self, tipo: str, identidad) -> None:
        super().__init__(f"No se encontro {tipo} con identidad {identidad}.")
        self.tipo = tipo
        self.identidad = identidad


class ConflictoDeDatos(ErrorDeAplicacion):
    """La operacion colisiona con informacion ya existente."""


class UsuarioInactivo(ErrorDeAplicacion):
    """El usuario que solicita la operacion se encuentra desactivado."""
