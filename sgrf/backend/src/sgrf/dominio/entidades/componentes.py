"""Componentes internos del agregado Receta.

Reune las entidades que solo existen dentro de una Receta y que no poseen
ciclo de vida propio: IngredientePreparacion, Paso, Fotografia y Nota.
Se manipulan siempre a traves de la raiz del agregado.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from ..excepciones import ReglaDeNegocioViolada, ValorInvalido
from ..objetos_valor import Cantidad, TipoEscalado


@dataclass
class IngredientePreparacion:
    """Relacion entre un Ingrediente del catalogo y una Preparacion.

    Aqui residen las cantidades: el Ingrediente nunca las almacena
    (ANALISIS.md, seccion 3.6). El TipoEscalado determina como se comporta
    la cantidad al escalar la Receta.
    """

    ingrediente_id: UUID
    tipo_escalado: TipoEscalado = TipoEscalado.LINEAL
    cantidad: Cantidad | None = None
    observacion: str = ""
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        self.observacion = (self.observacion or "").strip()
        self._validar_coherencia_cantidad()

    def _validar_coherencia_cantidad(self) -> None:
        """Verifica que la presencia de Cantidad concuerde con el TipoEscalado."""
        if self.tipo_escalado.requiere_cantidad and self.cantidad is None:
            raise ReglaDeNegocioViolada(
                f"El tipo de escalado '{self.tipo_escalado.value}' exige una cantidad.",
                "RN-007",
            )
        if not self.tipo_escalado.admite_cantidad and self.cantidad is not None:
            raise ReglaDeNegocioViolada(
                f"El tipo de escalado '{self.tipo_escalado.value}' no admite cantidad.",
                "RN-007",
            )

    def cantidad_escalada(self, factor) -> Cantidad | None:
        """Devuelve la cantidad resultante para un factor de escalado.

        No modifica el ingrediente original: el escalado siempre produce un
        valor nuevo y temporal (RN-004, ADR-003).
        """
        if self.cantidad is None:
            return None
        if not self.tipo_escalado.se_multiplica:
            return self.cantidad
        return self.cantidad.escalar(factor)


@dataclass
class Paso:
    """Instruccion ordenada dentro de una Preparacion."""

    descripcion: str
    orden: int
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        descripcion = (self.descripcion or "").strip()
        if not descripcion:
            raise ValorInvalido("El paso requiere una descripcion.")
        self.descripcion = descripcion
        if self.orden < 1:
            raise ValorInvalido("El orden de un paso comienza en 1.")


class TipoFotografia(Enum):
    """Clasificacion de fotografias segun RN-005."""

    PROCESO = "proceso"
    FINAL = "final"


@dataclass
class Fotografia:
    """Imagen asociada a una Preparacion.

    El limite de RN-005 (dos de proceso y una final) se controla en la
    Receta, ya que se aplica al conjunto de todas sus Preparaciones.
    """

    ruta: str
    tipo: TipoFotografia = TipoFotografia.PROCESO
    descripcion: str = ""
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        ruta = (self.ruta or "").strip()
        if not ruta:
            raise ValorInvalido("La fotografia requiere una ruta.")
        self.ruta = ruta
        self.descripcion = (self.descripcion or "").strip()


@dataclass
class Nota:
    """Observacion permanente asociada a una Receta (RF-025)."""

    texto: str
    autor_id: UUID | None = None
    fecha: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        texto = (self.texto or "").strip()
        if not texto:
            raise ValorInvalido("La nota no puede estar vacia.")
        self.texto = texto

    def editar(self, nuevo_texto: str) -> None:
        """Reemplaza el contenido de la nota (RF-026)."""
        texto = (nuevo_texto or "").strip()
        if not texto:
            raise ValorInvalido("La nota no puede estar vacia.")
        self.texto = texto
