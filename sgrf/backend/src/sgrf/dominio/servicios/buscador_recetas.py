"""Servicio de dominio BuscadorRecetas.

Expresa los criterios de busqueda del negocio (RF-038 a RF-043) como un
Objeto de Valor. La resolucion eficiente corresponde a la Infraestructura,
que traduce estos criterios a consultas del motor de base de datos; aqui se
define el significado del negocio y una evaluacion en memoria util para las
pruebas y para colecciones pequenias.

Criterio de aceptacion (ANALISIS.md, 4.12): las busquedas devuelven
unicamente recetas activas, salvo solicitud explicita.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID

from ..entidades.receta import Receta


@dataclass(frozen=True)
class CriteriosBusqueda:
    """Conjunto de filtros aplicables a una busqueda de Recetas."""

    texto: str | None = None
    ingrediente_id: UUID | None = None
    categoria_id: UUID | None = None
    etiqueta_id: UUID | None = None
    fuente_id: UUID | None = None
    solo_favoritas: bool = False
    incluir_archivadas: bool = False

    @property
    def esta_vacio(self) -> bool:
        """Indica si no se especifico ningun filtro."""
        return not any(
            [
                self.texto,
                self.ingrediente_id,
                self.categoria_id,
                self.etiqueta_id,
                self.fuente_id,
                self.solo_favoritas,
            ]
        )


@dataclass
class BuscadorRecetas:
    """Resuelve busquedas de Recetas segun los criterios del negocio."""

    def buscar(
        self, recetas: list[Receta], criterios: CriteriosBusqueda
    ) -> list[Receta]:
        """Filtra la coleccion recibida aplicando todos los criterios."""
        return [
            receta for receta in recetas if self.cumple(receta, criterios)
        ]

    def cumple(self, receta: Receta, criterios: CriteriosBusqueda) -> bool:
        """Determina si una Receta satisface los criterios indicados."""
        if receta.archivada and not criterios.incluir_archivadas:
            return False
        if criterios.solo_favoritas and not receta.favorita:
            return False
        if criterios.fuente_id and receta.fuente_id != criterios.fuente_id:
            return False
        if criterios.categoria_id and criterios.categoria_id not in receta.categorias_ids:
            return False
        if criterios.etiqueta_id and criterios.etiqueta_id not in receta.etiquetas_ids:
            return False
        if (
            criterios.ingrediente_id
            and criterios.ingrediente_id not in receta.ingredientes_utilizados()
        ):
            return False
        if criterios.texto and not self._coincide_texto(receta, criterios.texto):
            return False
        return True

    def _coincide_texto(self, receta: Receta, texto: str) -> bool:
        """Busca el texto en el nombre y la descripcion de la receta (RF-038)."""
        buscado = texto.strip().lower()
        if not buscado:
            return True
        return buscado in receta.nombre.lower() or buscado in receta.descripcion.lower()
