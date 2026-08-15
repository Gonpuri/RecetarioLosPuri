"""Servicio de dominio ValidadorRecetas.

Verifica de forma explicita el cumplimiento de las reglas de negocio
resumidas en ANALISIS.md, seccion 7.2.

Las entidades ya impiden alcanzar estados invalidos; este servicio existe
para auditar una Receta completa antes de publicarla o guardarla y para
producir un informe legible de los incumplimientos, en lugar de detenerse
en el primero.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..entidades.componentes import TipoFotografia
from ..entidades.receta import (
    MAXIMO_FOTOGRAFIAS_FINAL,
    MAXIMO_FOTOGRAFIAS_PROCESO,
    Receta,
)
from ..excepciones import ReglaDeNegocioViolada


@dataclass(frozen=True)
class Incumplimiento:
    """Descripcion de una regla de negocio incumplida."""

    codigo_regla: str
    mensaje: str

    def __str__(self) -> str:
        return f"[{self.codigo_regla}] {self.mensaje}"


@dataclass
class ResultadoValidacion:
    """Informe del estado de una Receta frente a las reglas del negocio."""

    incumplimientos: list[Incumplimiento] = field(default_factory=list)

    @property
    def es_valida(self) -> bool:
        """Indica si la receta no presenta incumplimientos."""
        return not self.incumplimientos

    def registrar(self, codigo_regla: str, mensaje: str) -> None:
        """Agrega un incumplimiento al informe."""
        self.incumplimientos.append(Incumplimiento(codigo_regla, mensaje))

    def elevar_si_invalida(self) -> None:
        """Lanza una excepcion si existe al menos un incumplimiento."""
        if not self.es_valida:
            detalle = "; ".join(str(i) for i in self.incumplimientos)
            raise ReglaDeNegocioViolada(f"La receta no es valida: {detalle}")


class ValidadorRecetas:
    """Audita el cumplimiento de las reglas de negocio de una Receta."""

    def validar(self, receta: Receta) -> ResultadoValidacion:
        """Revisa la receta completa y devuelve el informe de validacion."""
        resultado = ResultadoValidacion()
        self._validar_rendimiento_base(receta, resultado)
        self._validar_fuente(receta, resultado)
        self._validar_preparaciones(receta, resultado)
        self._validar_fotografias(receta, resultado)
        return resultado

    def _validar_rendimiento_base(
        self, receta: Receta, resultado: ResultadoValidacion
    ) -> None:
        """RN-001: toda receta posee un unico Rendimiento Base."""
        if receta.rendimiento_base is None:
            resultado.registrar(
                "RN-001", "La receta debe declarar un rendimiento base."
            )

    def _validar_fuente(
        self, receta: Receta, resultado: ResultadoValidacion
    ) -> None:
        """RN-002: toda receta posee exactamente una Fuente."""
        if receta.fuente_id is None:
            resultado.registrar("RN-002", "La receta debe declarar una fuente.")

    def _validar_preparaciones(
        self, receta: Receta, resultado: ResultadoValidacion
    ) -> None:
        """RN-003: toda receta posee una o mas Preparaciones con contenido."""
        if not receta.preparaciones:
            resultado.registrar(
                "RN-003", "La receta debe poseer al menos una preparacion."
            )
            return
        for preparacion in receta.preparaciones:
            if not preparacion.ingredientes:
                resultado.registrar(
                    "RN-003",
                    f"La preparacion '{preparacion.nombre}' no posee ingredientes.",
                )
            if not preparacion.pasos:
                resultado.registrar(
                    "RN-003",
                    f"La preparacion '{preparacion.nombre}' no posee pasos.",
                )

    def _validar_fotografias(
        self, receta: Receta, resultado: ResultadoValidacion
    ) -> None:
        """RN-005: maximo dos fotografias de proceso y una final por receta."""
        limites = {
            TipoFotografia.PROCESO: MAXIMO_FOTOGRAFIAS_PROCESO,
            TipoFotografia.FINAL: MAXIMO_FOTOGRAFIAS_FINAL,
        }
        for tipo, maximo in limites.items():
            cantidad = receta.contar_fotografias(tipo)
            if cantidad > maximo:
                resultado.registrar(
                    "RN-005",
                    f"La receta posee {cantidad} fotografias de tipo "
                    f"'{tipo.value}' y el maximo es {maximo}.",
                )
