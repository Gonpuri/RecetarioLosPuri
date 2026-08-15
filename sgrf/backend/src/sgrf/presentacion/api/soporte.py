"""Soporte comun de la API.

Reune la serializacion de los DTO y la traduccion de excepciones a codigos
HTTP. Ambas tareas se repiten en todas las vistas y no pertenecen a
ninguna en particular.
"""

from __future__ import annotations

import dataclasses
import logging
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler as manejador_drf

from ...aplicacion.excepciones import (
    ConflictoDeDatos,
    PermisoDenegado,
    RecursoNoEncontrado,
    UsuarioInactivo,
)
from ...dominio.excepciones import (
    ElementoNoEncontrado,
    RecetaArchivada,
    ReglaDeNegocioViolada,
    UnidadesIncompatibles,
    ValorInvalido,
)

registro = logging.getLogger(__name__)


def serializar(valor):
    """Convierte un DTO del dominio a estructuras admitidas por JSON.

    Los DTO son dataclasses inmutables con UUID, Decimal y datetime. Esta
    funcion los recorre en profundidad sin que cada vista deba repetir la
    conversion.
    """
    if dataclasses.is_dataclass(valor) and not isinstance(valor, type):
        return {
            campo.name: serializar(getattr(valor, campo.name))
            for campo in dataclasses.fields(valor)
        }
    if isinstance(valor, (list, tuple, set)):
        return [serializar(item) for item in valor]
    if isinstance(valor, dict):
        return {str(clave): serializar(item) for clave, item in valor.items()}
    if isinstance(valor, Enum):
        return valor.value
    if isinstance(valor, UUID):
        return str(valor)
    if isinstance(valor, Decimal):
        # Se envia como texto para que el front no pierda precision al
        # convertirlo a numero de coma flotante.
        return str(valor)
    if isinstance(valor, (datetime, date)):
        return valor.isoformat()
    return valor


# Cada excepcion del negocio tiene un unico codigo HTTP correcto. Reunirlos
# aqui evita que cada vista invente el suyo.
CODIGOS_HTTP = {
    RecursoNoEncontrado: status.HTTP_404_NOT_FOUND,
    ElementoNoEncontrado: status.HTTP_404_NOT_FOUND,
    PermisoDenegado: status.HTTP_403_FORBIDDEN,
    UsuarioInactivo: status.HTTP_403_FORBIDDEN,
    ConflictoDeDatos: status.HTTP_409_CONFLICT,
    RecetaArchivada: status.HTTP_409_CONFLICT,
    ReglaDeNegocioViolada: status.HTTP_422_UNPROCESSABLE_ENTITY,
    ValorInvalido: status.HTTP_400_BAD_REQUEST,
    UnidadesIncompatibles: status.HTTP_400_BAD_REQUEST,
}


def manejar_excepciones(excepcion, contexto):
    """Traduce las excepciones del Dominio y la Aplicacion a respuestas HTTP.

    El mensaje del negocio llega tal cual al usuario, ya que fue redactado
    para ser leido (Capitulo 6.12: los errores deben ser claros y
    accionables).
    """
    for tipo, codigo in CODIGOS_HTTP.items():
        if isinstance(excepcion, tipo):
            cuerpo = {"error": str(excepcion)}
            if isinstance(excepcion, ReglaDeNegocioViolada) and excepcion.codigo_regla:
                cuerpo["regla"] = excepcion.codigo_regla
            return Response(cuerpo, status=codigo)

    respuesta = manejador_drf(excepcion, contexto)
    if respuesta is None:
        registro.exception("Error no contemplado en la API", exc_info=excepcion)
    return respuesta


def creado(dto) -> Response:
    """Respuesta 201 con el recurso serializado."""
    return Response(serializar(dto), status=status.HTTP_201_CREATED)


def correcto(dto=None) -> Response:
    """Respuesta 200, con cuerpo o vacia."""
    if dto is None:
        return Response(status=status.HTTP_204_NO_CONTENT)
    return Response(serializar(dto), status=status.HTTP_200_OK)
