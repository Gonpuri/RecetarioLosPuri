"""Casos de Uso de Escalado y Lista de Compras (RF-031 a RF-037).

Constituyen el nucleo funcional del sistema: el flujo del Capitulo 6.8
(abrir receta, elegir rendimiento, escalar, marcar faltantes, generar
lista) atraviesa estos dos casos de uso.

RN-004 y ADR-003: el escalado no persiste absolutamente nada. Se guarda la
Lista de Compras resultante, nunca la receta escalada que la origino.
"""

from __future__ import annotations

from uuid import UUID

from ...dominio.objetos_valor import Rendimiento
from ...dominio.servicios import EscaladorRecetas, GeneradorListaCompras
from ..dto import (
    ComandoEscalarReceta,
    ComandoGenerarListaCompras,
    ListaCompraResultado,
    RecetaEscaladaResultado,
)
from ..ensambladores import EnsambladorListaCompras, EnsambladorRecetas
from .base import CasoDeUso


class EscalarReceta(CasoDeUso):
    """CU-013: calcula las cantidades para un nuevo Rendimiento (RF-031).

    La Receta almacenada permanece intacta: este caso de uso solo lee del
    repositorio y jamas invoca `guardar` (RF-032).
    """

    def ejecutar(self, comando: ComandoEscalarReceta) -> RecetaEscaladaResultado:
        """Devuelve la representacion escalada, sin persistir nada."""
        usuario = self._obtener_usuario(comando.solicitante_id)
        self.autorizacion.asegurar_activo(usuario)
        receta = self._obtener_receta(comando.receta_id)

        objetivo = Rendimiento(
            comando.rendimiento_objetivo,
            comando.rendimiento_descripcion
            or receta.rendimiento_base.descripcion,
        )
        escalada = EscaladorRecetas().escalar(receta, objetivo)

        return EnsambladorRecetas().a_resultado_escalado(
            receta,
            escalada,
            self._nombres_de_ingredientes(receta.ingredientes_utilizados()),
        )


class GenerarListaCompras(CasoDeUso):
    """CU-014: construye la Lista de Compras consolidada (RF-034 y RF-035).

    RN-006: unicamente se incluyen los ingredientes que el usuario marco
    como faltantes. Si se indica un rendimiento objetivo, las cantidades
    corresponden a la receta escalada.
    """

    def ejecutar(
        self, comando: ComandoGenerarListaCompras
    ) -> ListaCompraResultado:
        """Genera la lista y, opcionalmente, la persiste."""
        usuario = self._obtener_usuario(comando.solicitante_id)
        self.autorizacion.asegurar_activo(usuario)
        receta = self._obtener_receta(comando.receta_id)

        objetivo = self._rendimiento_objetivo(comando, receta)
        escalada = EscaladorRecetas().escalar(receta, objetivo)
        nombres = self._nombres_de_ingredientes(receta.ingredientes_utilizados())

        lista = GeneradorListaCompras().generar(
            receta_escalada=escalada,
            ingredientes_seleccionados=set(comando.ingredientes_seleccionados),
            nombres_ingredientes=nombres,
            usuario_id=usuario.id,
        )

        if comando.persistir:
            with self.uow:
                self.uow.listas_compra.guardar(lista)
                self.uow.confirmar()

        return EnsambladorListaCompras().a_resultado(lista)

    def _rendimiento_objetivo(
        self, comando: ComandoGenerarListaCompras, receta
    ) -> Rendimiento:
        """Determina el rendimiento a usar; por defecto, el base de la receta."""
        if comando.rendimiento_objetivo is None:
            return receta.rendimiento_base
        return Rendimiento(
            comando.rendimiento_objetivo,
            comando.rendimiento_descripcion or receta.rendimiento_base.descripcion,
        )


class ListarListasCompras(CasoDeUso):
    """CU-016: devuelve las Listas de Compras guardadas por el usuario.

    Alimenta la pantalla de Lista de Compras, que reune lo pendiente de
    todas las recetas para las que se pidio una lista.
    """

    def ejecutar(self, solicitante_id: UUID) -> list[ListaCompraResultado]:
        """Lista las compras del propio usuario.

        Cada persona ve unicamente sus listas: son de uso personal, a
        diferencia del recetario, que es compartido.
        """
        usuario = self._obtener_usuario(solicitante_id)
        self.autorizacion.asegurar_activo(usuario)
        ensamblador = EnsambladorListaCompras()
        return [
            ensamblador.a_resultado(lista)
            for lista in self.uow.listas_compra.listar_por_usuario(usuario.id)
        ]


class CombinarListasCompras(CasoDeUso):
    """CU-015: une varias Listas de Compras en una sola.

    Permite planificar la compra de varias recetas a la vez consolidando
    los ingredientes repetidos.
    """

    def ejecutar(
        self, solicitante_id: UUID, listas_ids: list[UUID]
    ) -> ListaCompraResultado:
        """Combina las listas indicadas del usuario solicitante."""
        usuario = self._obtener_usuario(solicitante_id)
        self.autorizacion.asegurar_activo(usuario)

        listas = [
            lista
            for lista in (
                self.uow.listas_compra.obtener(identidad) for identidad in listas_ids
            )
            if lista is not None
        ]
        combinada = GeneradorListaCompras().combinar(listas)
        return EnsambladorListaCompras().a_resultado(combinada)


class MarcarItemComprado(CasoDeUso):
    """CU-024: marca o desmarca un item de la Lista de Compras (RF-036).

    A diferencia del marcado de faltantes al generar la lista (que solo
    vive en memoria hasta que se persiste), este marcado siempre se guarda:
    tachar un producto en el supermercado y que se pierda al recargar la
    pantalla no tendria sentido.
    """

    def ejecutar(
        self,
        solicitante_id: UUID,
        lista_id: UUID,
        item_id: UUID,
        comprado: bool = True,
    ) -> None:
        """Actualiza el estado de comprado y persiste la lista."""
        lista = self._obtener_lista_propia(solicitante_id, lista_id)
        lista.obtener_item(item_id).marcar_comprado(comprado)
        with self.uow:
            self.uow.listas_compra.guardar(lista)
            self.uow.confirmar()


class QuitarItemDeLista(CasoDeUso):
    """CU-025: saca un producto de la Lista de Compras (RF-037).

    Distinto de marcarlo como comprado: sirve para el caso de "esto ya no
    hace falta comprarlo", sin que quede tachado entre los comprados.
    """

    def ejecutar(self, solicitante_id: UUID, lista_id: UUID, item_id: UUID) -> None:
        """Elimina el item y persiste la lista resultante."""
        lista = self._obtener_lista_propia(solicitante_id, lista_id)
        lista.quitar_item(item_id)
        with self.uow:
            self.uow.listas_compra.guardar(lista)
            self.uow.confirmar()
