"""Capa de Dominio del SGRF.

Nucleo del sistema (ANALISIS.md, seccion 5.5). No depende de Django, del
motor de base de datos ni de ninguna libreria externa: solo de la
biblioteca estandar de Python.
"""

from . import entidades, excepciones, objetos_valor, repositorios, servicios

__all__ = [
    "entidades",
    "excepciones",
    "objetos_valor",
    "repositorios",
    "servicios",
]
