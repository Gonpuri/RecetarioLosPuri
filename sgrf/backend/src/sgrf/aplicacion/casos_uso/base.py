"""Infraestructura comun a todos los Casos de Uso.

Reune las dependencias y las verificaciones que se repiten en cada caso de
uso: la Unidad de Trabajo, la autorizacion y la resolucion de entidades
referenciadas por identidad.
"""

from __future__ import annotations

from uuid import UUID

from ...dominio.entidades import Receta, Usuario
from ..autorizacion import Autorizacion
from ..excepciones import RecursoNoEncontrado
from ..unidad_de_trabajo import UnidadDeTrabajo


class CasoDeUso:
    """Base de los casos de uso: dependencias y utilidades compartidas."""

    def __init__(
        self,
        unidad_de_trabajo: UnidadDeTrabajo,
        autorizacion: Autorizacion | None = None,
    ) -> None:
        self.uow = unidad_de_trabajo
        self.autorizacion = autorizacion or Autorizacion()

    def _obtener_usuario(self, usuario_id: UUID) -> Usuario:
        """Recupera el usuario solicitante o falla si no existe."""
        usuario = self.uow.usuarios.obtener(usuario_id)
        if usuario is None:
            raise RecursoNoEncontrado("Usuario", usuario_id)
        return usuario

    def _obtener_receta(self, receta_id: UUID) -> Receta:
        """Recupera una receta o falla si no existe."""
        receta = self.uow.recetas.obtener(receta_id)
        if receta is None:
            raise RecursoNoEncontrado("Receta", receta_id)
        return receta

    def _nombres_de_ingredientes(self, ids: set[UUID]) -> dict[UUID, str]:
        """Resuelve los nombres del catalogo para un conjunto de ingredientes."""
        if not ids:
            return {}
        catalogo = self.uow.ingredientes.obtener_varios(ids)
        return {
            identidad: ingrediente.nombre
            for identidad, ingrediente in catalogo.items()
        }

    def _nombre_de_fuente(self, fuente_id: UUID) -> str:
        """Resuelve el nombre de una fuente, tolerando su ausencia."""
        fuente = self.uow.fuentes.obtener(fuente_id)
        return fuente.nombre if fuente else ""
