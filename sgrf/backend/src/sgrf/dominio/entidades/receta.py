"""Entidad Receta: raiz del agregado (ADR-001).

Toda modificacion del recetario pasa por esta entidad, que custodia las
invariantes del negocio:

- RN-001: posee un unico Rendimiento Base.
- RN-002: posee exactamente una Fuente.
- RN-003: posee una o mas Preparaciones.
- RN-004: la receta base nunca se modifica al escalar.
- RN-005: maximo tres fotografias (dos de proceso y una final).

El escalado no vive aqui sino en el servicio EscaladorRecetas, y jamas
altera el estado de la Receta.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4

from ..excepciones import (
    ElementoNoEncontrado,
    RecetaArchivada,
    ReglaDeNegocioViolada,
    ValorInvalido,
)
from ..objetos_valor import Rendimiento
from .componentes import Fotografia, Nota, TipoFotografia
from .preparacion import Preparacion

MAXIMO_FOTOGRAFIAS_PROCESO = 2
MAXIMO_FOTOGRAFIAS_FINAL = 1


@dataclass
class Receta:
    """Elaboracion culinaria completa. Raiz del agregado."""

    nombre: str
    rendimiento_base: Rendimiento
    fuente_id: UUID
    descripcion: str = ""
    preparaciones: list[Preparacion] = field(default_factory=list)
    categorias_ids: set[UUID] = field(default_factory=set)
    etiquetas_ids: set[UUID] = field(default_factory=set)
    notas: list[Nota] = field(default_factory=list)
    archivada: bool = False
    favorita: bool = False
    autor_id: UUID | None = None
    fecha_creacion: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        nombre = (self.nombre or "").strip()
        if not nombre:
            raise ValorInvalido("La receta requiere un nombre.")
        self.nombre = nombre
        self.descripcion = (self.descripcion or "").strip()
        if self.fuente_id is None:
            raise ReglaDeNegocioViolada(
                "Toda receta debe indicar su fuente.", "RN-002"
            )

    # -- Guardas ----------------------------------------------------------

    def _asegurar_modificable(self) -> None:
        """Impide modificar una receta archivada.

        Una receta archivada se conserva como registro historico; para
        editarla primero debe restaurarse (RF-009).
        """
        if self.archivada:
            raise RecetaArchivada(
                "La receta esta archivada; restaurela antes de modificarla."
            )

    # -- Informacion general ----------------------------------------------

    def actualizar_informacion(
        self,
        nombre: str | None = None,
        descripcion: str | None = None,
        rendimiento_base: Rendimiento | None = None,
        fuente_id: UUID | None = None,
    ) -> None:
        """Edita los datos generales de la receta (RF-006)."""
        self._asegurar_modificable()
        if nombre is not None:
            limpio = nombre.strip()
            if not limpio:
                raise ValorInvalido("La receta requiere un nombre.")
            self.nombre = limpio
        if descripcion is not None:
            self.descripcion = descripcion.strip()
        if rendimiento_base is not None:
            self.rendimiento_base = rendimiento_base
        if fuente_id is not None:
            self.fuente_id = fuente_id

    # -- Preparaciones ----------------------------------------------------

    def agregar_preparacion(self, preparacion: Preparacion) -> None:
        """Incorpora una Preparacion a la receta (RF-011)."""
        self._asegurar_modificable()
        preparacion.orden = len(self.preparaciones) + 1
        self.preparaciones.append(preparacion)

    def quitar_preparacion(self, preparacion_id: UUID) -> None:
        """Elimina una Preparacion respetando RN-003 (RF-013)."""
        self._asegurar_modificable()
        if len(self.preparaciones) <= 1:
            raise ReglaDeNegocioViolada(
                "Toda receta debe conservar al menos una preparacion.", "RN-003"
            )
        objetivo = self.obtener_preparacion(preparacion_id)
        self.preparaciones.remove(objetivo)
        self._renumerar_preparaciones()

    def reordenar_preparaciones(self, ids_en_orden: list[UUID]) -> None:
        """Reordena las preparaciones segun las identidades recibidas (RF-014)."""
        self._asegurar_modificable()
        if len(ids_en_orden) != len(self.preparaciones):
            raise ValorInvalido(
                "El reordenamiento debe incluir todas las preparaciones."
            )
        indice = {preparacion.id: preparacion for preparacion in self.preparaciones}
        if set(ids_en_orden) != set(indice):
            raise ValorInvalido(
                "El reordenamiento contiene preparaciones desconocidas."
            )
        self.preparaciones = [indice[identidad] for identidad in ids_en_orden]
        self._renumerar_preparaciones()

    def obtener_preparacion(self, preparacion_id: UUID) -> Preparacion:
        """Devuelve una Preparacion del agregado por su identidad."""
        objetivo = next(
            (p for p in self.preparaciones if p.id == preparacion_id), None
        )
        if objetivo is None:
            raise ElementoNoEncontrado(
                f"La receta no contiene la preparacion {preparacion_id}."
            )
        return objetivo

    def _renumerar_preparaciones(self) -> None:
        """Reasigna el orden correlativo de las preparaciones desde 1."""
        for posicion, preparacion in enumerate(self.preparaciones, start=1):
            preparacion.orden = posicion

    @property
    def preparaciones_ordenadas(self) -> list[Preparacion]:
        """Devuelve las preparaciones segun su orden."""
        return sorted(self.preparaciones, key=lambda p: p.orden)

    # -- Fotografias (RN-005) ---------------------------------------------

    def agregar_fotografia(
        self, preparacion_id: UUID, fotografia: Fotografia
    ) -> None:
        """Agrega una fotografia validando el limite global de la receta.

        El limite de RN-005 se aplica al conjunto de la Receta, no a cada
        Preparacion: por eso la validacion reside en la raiz del agregado.
        """
        self._asegurar_modificable()
        preparacion = self.obtener_preparacion(preparacion_id)
        self._validar_limite_fotografias(fotografia.tipo)
        preparacion.agregar_fotografia(fotografia)

    def quitar_fotografia(self, preparacion_id: UUID, fotografia_id: UUID) -> None:
        """Elimina una fotografia de una preparacion (RF-024)."""
        self._asegurar_modificable()
        self.obtener_preparacion(preparacion_id).quitar_fotografia(fotografia_id)

    def _validar_limite_fotografias(self, tipo: TipoFotografia) -> None:
        """Verifica que no se supere el maximo permitido por RN-005."""
        maximos = {
            TipoFotografia.PROCESO: MAXIMO_FOTOGRAFIAS_PROCESO,
            TipoFotografia.FINAL: MAXIMO_FOTOGRAFIAS_FINAL,
        }
        if self.contar_fotografias(tipo) >= maximos[tipo]:
            raise ReglaDeNegocioViolada(
                f"La receta admite como maximo {maximos[tipo]} fotografia(s) "
                f"de tipo '{tipo.value}'.",
                "RN-005",
            )

    def contar_fotografias(self, tipo: TipoFotografia | None = None) -> int:
        """Cuenta las fotografias de la receta, opcionalmente por tipo."""
        return sum(
            1
            for preparacion in self.preparaciones
            for foto in preparacion.fotografias
            if tipo is None or foto.tipo is tipo
        )

    # -- Categorias y etiquetas -------------------------------------------

    def asignar_categoria(self, categoria_id: UUID) -> None:
        """Asocia una categoria a la receta (RF-027)."""
        self._asegurar_modificable()
        self.categorias_ids.add(categoria_id)

    def quitar_categoria(self, categoria_id: UUID) -> None:
        """Desasocia una categoria de la receta."""
        self._asegurar_modificable()
        self.categorias_ids.discard(categoria_id)

    def asignar_etiqueta(self, etiqueta_id: UUID) -> None:
        """Asocia una etiqueta a la receta (RF-028)."""
        self._asegurar_modificable()
        self.etiquetas_ids.add(etiqueta_id)

    def quitar_etiqueta(self, etiqueta_id: UUID) -> None:
        """Desasocia una etiqueta de la receta."""
        self._asegurar_modificable()
        self.etiquetas_ids.discard(etiqueta_id)

    # -- Notas ------------------------------------------------------------

    def agregar_nota(self, nota: Nota) -> None:
        """Registra una observacion permanente (RF-025)."""
        self._asegurar_modificable()
        self.notas.append(nota)

    def quitar_nota(self, nota_id: UUID) -> None:
        """Elimina una nota de la receta (RF-026)."""
        self._asegurar_modificable()
        objetivo = next((n for n in self.notas if n.id == nota_id), None)
        if objetivo is None:
            raise ElementoNoEncontrado(f"No existe la nota {nota_id}.")
        self.notas.remove(objetivo)

    # -- Ciclo de vida ----------------------------------------------------

    def archivar(self) -> None:
        """Archiva la receta sin eliminarla (RF-008)."""
        self.archivada = True

    def restaurar(self) -> None:
        """Devuelve la receta al estado activo (RF-009)."""
        self.archivada = False

    def marcar_favorita(self, favorita: bool = True) -> None:
        """Marca o desmarca la receta como favorita (RF-043)."""
        self.favorita = favorita

    # -- Consultas --------------------------------------------------------

    def ingredientes_utilizados(self) -> set[UUID]:
        """Devuelve las identidades de los Ingredientes usados en la receta.

        Sirve a BuscadorRecetas para resolver la busqueda por ingrediente
        (RF-039).
        """
        return {
            ingrediente.ingrediente_id
            for preparacion in self.preparaciones
            for ingrediente in preparacion.ingredientes
        }
