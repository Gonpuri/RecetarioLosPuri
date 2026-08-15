"""Casos de Uso de Busqueda (RF-038 a RF-043).

Criterio de aceptacion 4.12: las busquedas devuelven unicamente recetas
activas, salvo solicitud explicita. La regla vive en el servicio de dominio
BuscadorRecetas; este caso de uso solo traduce y orquesta.
"""

from __future__ import annotations

from uuid import UUID

from ...dominio.servicios import CriteriosBusqueda
from ..dto import ComandoBuscarRecetas, RecetaResumen
from ..ensambladores import EnsambladorRecetas
from .base import CasoDeUso


class BuscarRecetas(CasoDeUso):
    """CU-022: resuelve busquedas por los criterios del negocio."""

    def ejecutar(self, comando: ComandoBuscarRecetas) -> list[RecetaResumen]:
        """Devuelve los resumenes de las recetas que coinciden."""
        usuario = self._obtener_usuario(comando.solicitante_id)
        self.autorizacion.asegurar_activo(usuario)

        criterios = CriteriosBusqueda(
            texto=comando.texto,
            ingrediente_id=comando.ingrediente_id,
            categoria_id=comando.categoria_id,
            etiqueta_id=comando.etiqueta_id,
            fuente_id=comando.fuente_id,
            solo_favoritas=comando.solo_favoritas,
            incluir_archivadas=comando.incluir_archivadas,
        )

        ensamblador = EnsambladorRecetas()
        return [
            ensamblador.a_resumen(receta)
            for receta in self.uow.recetas.buscar(criterios)
        ]


class ListarRecetas(CasoDeUso):
    """CU-023: devuelve el recetario para la pantalla de listado."""

    def ejecutar(
        self, solicitante_id: UUID, incluir_archivadas: bool = False
    ) -> list[RecetaResumen]:
        """Lista las recetas ordenadas alfabeticamente."""
        usuario = self._obtener_usuario(solicitante_id)
        self.autorizacion.asegurar_activo(usuario)
        ensamblador = EnsambladorRecetas()
        recetas = self.uow.recetas.listar_todas(incluir_archivadas)
        return sorted(
            (ensamblador.a_resumen(receta) for receta in recetas),
            key=lambda resumen: resumen.nombre.lower(),
        )
