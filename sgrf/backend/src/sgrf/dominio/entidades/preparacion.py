"""Entidad Preparacion.

La Preparacion es la unidad funcional del dominio (ADR-002): representa una
etapa independiente de la Receta, como Masa, Salsa, Cobertura o Armado.
Posee ingredientes, pasos y fotografias propios y mantiene un orden dentro
de la Receta.

Pertenece al agregado Receta: se manipula siempre a traves de la raiz.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID, uuid4

from ..excepciones import ElementoNoEncontrado, ValorInvalido
from .componentes import Fotografia, IngredientePreparacion, Paso, TipoFotografia


@dataclass
class Preparacion:
    """Etapa independiente de una Receta."""

    nombre: str
    orden: int = 1
    ingredientes: list[IngredientePreparacion] = field(default_factory=list)
    pasos: list[Paso] = field(default_factory=list)
    fotografias: list[Fotografia] = field(default_factory=list)
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        nombre = (self.nombre or "").strip()
        if not nombre:
            raise ValorInvalido("La preparacion requiere un nombre.")
        self.nombre = nombre
        if self.orden < 1:
            raise ValorInvalido("El orden de una preparacion comienza en 1.")

    # -- Ingredientes -----------------------------------------------------

    def agregar_ingrediente(self, ingrediente: IngredientePreparacion) -> None:
        """Incorpora un ingrediente a la preparacion (RF-016)."""
        if self._buscar_ingrediente(ingrediente.ingrediente_id) is not None:
            raise ValorInvalido(
                "El ingrediente ya figura en esta preparacion; "
                "modifique la cantidad existente."
            )
        self.ingredientes.append(ingrediente)

    def quitar_ingrediente(self, ingrediente_preparacion_id: UUID) -> None:
        """Elimina un ingrediente de la preparacion (RF-018)."""
        objetivo = self._obtener_ingrediente_por_id(ingrediente_preparacion_id)
        self.ingredientes.remove(objetivo)

    def obtener_ingrediente(
        self, ingrediente_preparacion_id: UUID
    ) -> IngredientePreparacion:
        """Devuelve un ingrediente de la preparacion por su identidad."""
        return self._obtener_ingrediente_por_id(ingrediente_preparacion_id)

    def _buscar_ingrediente(
        self, ingrediente_id: UUID
    ) -> IngredientePreparacion | None:
        """Busca por identidad del Ingrediente del catalogo."""
        return next(
            (i for i in self.ingredientes if i.ingrediente_id == ingrediente_id),
            None,
        )

    def _obtener_ingrediente_por_id(
        self, ingrediente_preparacion_id: UUID
    ) -> IngredientePreparacion:
        """Busca por identidad de la relacion IngredientePreparacion."""
        objetivo = next(
            (i for i in self.ingredientes if i.id == ingrediente_preparacion_id),
            None,
        )
        if objetivo is None:
            raise ElementoNoEncontrado(
                f"La preparacion no contiene el ingrediente {ingrediente_preparacion_id}."
            )
        return objetivo

    # -- Pasos ------------------------------------------------------------

    def agregar_paso(self, descripcion: str) -> Paso:
        """Agrega un paso al final de la secuencia (RF-019)."""
        paso = Paso(descripcion=descripcion, orden=len(self.pasos) + 1)
        self.pasos.append(paso)
        return paso

    def quitar_paso(self, paso_id: UUID) -> None:
        """Elimina un paso y renumera los restantes (RF-021)."""
        objetivo = next((p for p in self.pasos if p.id == paso_id), None)
        if objetivo is None:
            raise ElementoNoEncontrado(f"No existe el paso {paso_id}.")
        self.pasos.remove(objetivo)
        self._renumerar_pasos()

    def reordenar_pasos(self, ids_en_orden: list[UUID]) -> None:
        """Reordena los pasos segun la secuencia de identidades recibida (RF-022)."""
        if len(ids_en_orden) != len(self.pasos):
            raise ValorInvalido(
                "El reordenamiento debe incluir todos los pasos de la preparacion."
            )
        indice = {paso.id: paso for paso in self.pasos}
        if set(ids_en_orden) != set(indice):
            raise ValorInvalido("El reordenamiento contiene pasos desconocidos.")
        self.pasos = [indice[paso_id] for paso_id in ids_en_orden]
        self._renumerar_pasos()

    def _renumerar_pasos(self) -> None:
        """Reasigna el orden correlativo de los pasos comenzando en 1."""
        for posicion, paso in enumerate(self.pasos, start=1):
            paso.orden = posicion

    # -- Fotografias ------------------------------------------------------

    def agregar_fotografia(self, fotografia: Fotografia) -> None:
        """Agrega una fotografia.

        El limite de RN-005 se valida en la Receta, que conoce todas las
        preparaciones.
        """
        self.fotografias.append(fotografia)

    def quitar_fotografia(self, fotografia_id: UUID) -> None:
        """Elimina una fotografia de la preparacion (RF-024)."""
        objetivo = next((f for f in self.fotografias if f.id == fotografia_id), None)
        if objetivo is None:
            raise ElementoNoEncontrado(f"No existe la fotografia {fotografia_id}.")
        self.fotografias.remove(objetivo)

    def contar_fotografias(self, tipo: TipoFotografia) -> int:
        """Cuenta las fotografias de un tipo dado."""
        return sum(1 for f in self.fotografias if f.tipo is tipo)

    # -- Consultas --------------------------------------------------------

    @property
    def pasos_ordenados(self) -> list[Paso]:
        """Devuelve los pasos ordenados por su numero de orden."""
        return sorted(self.pasos, key=lambda paso: paso.orden)
