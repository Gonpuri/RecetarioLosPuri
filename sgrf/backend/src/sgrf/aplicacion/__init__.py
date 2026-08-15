"""Capa de Aplicacion del SGRF.

Coordina los Casos de Uso: orquesta operaciones, valida permisos, gestiona
transacciones e invoca los Servicios del Dominio (Capitulo 5.4). No
contiene reglas de negocio.
"""

from . import casos_uso, dto, excepciones
from .autorizacion import Autorizacion
from .unidad_de_trabajo import UnidadDeTrabajo

__all__ = ["Autorizacion", "UnidadDeTrabajo", "casos_uso", "dto", "excepciones"]
