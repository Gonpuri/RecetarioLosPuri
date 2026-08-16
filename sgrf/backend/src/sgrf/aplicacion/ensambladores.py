"""Ensambladores entre el Dominio y los DTO.

Concentran la traduccion en un unico lugar para que ningun caso de uso
tenga que recorrer entidades armando diccionarios. La direccion es siempre
la misma: el Dominio no conoce los DTO.
"""

from __future__ import annotations

from uuid import UUID

from ..dominio.entidades import (
    ListaCompra,
    Preparacion,
    Receta,
    TipoFotografia,
    Usuario,
)
from ..dominio.servicios import RecetaEscalada
from .dto import (
    FotografiaResultado,
    IngredienteResultado,
    ItemCompraResultado,
    ListaCompraResultado,
    NotaResultado,
    PasoResultado,
    PreparacionResultado,
    RecetaEscaladaResultado,
    RecetaResultado,
    RecetaResumen,
    UsuarioResultado,
)


def _texto_cantidad(cantidad, tipo_escalado) -> str:
    """Devuelve el texto a mostrar, con o sin cantidad numerica."""
    return str(cantidad) if cantidad is not None else tipo_escalado.etiqueta


class EnsambladorRecetas:
    """Traduce Recetas y sus componentes a DTO."""

    def a_resultado(
        self,
        receta: Receta,
        nombres_ingredientes: dict[UUID, str],
        nombre_fuente: str = "",
    ) -> RecetaResultado:
        """Arma la vista completa de una Receta (RF-007)."""
        return RecetaResultado(
            id=receta.id,
            nombre=receta.nombre,
            descripcion=receta.descripcion,
            rendimiento_base=receta.rendimiento_base.valor,
            rendimiento_descripcion=receta.rendimiento_base.descripcion,
            fuente_id=receta.fuente_id,
            fuente_nombre=nombre_fuente,
            archivada=receta.archivada,
            favorita=receta.favorita,
            preparaciones=tuple(
                self._preparacion(p, nombres_ingredientes)
                for p in receta.preparaciones_ordenadas
            ),
            categorias_ids=tuple(receta.categorias_ids),
            etiquetas_ids=tuple(receta.etiquetas_ids),
            notas=tuple(
                NotaResultado(
                    id=nota.id,
                    texto=nota.texto,
                    fecha=nota.fecha,
                    autor_id=nota.autor_id,
                )
                for nota in receta.notas
            ),
        )

    def a_resumen(self, receta: Receta) -> RecetaResumen:
        """Arma la tarjeta de receta para listados (Capitulo 6.7)."""
        return RecetaResumen(
            id=receta.id,
            nombre=receta.nombre,
            rendimiento_base=receta.rendimiento_base.valor,
            rendimiento_descripcion=receta.rendimiento_base.descripcion,
            archivada=receta.archivada,
            favorita=receta.favorita,
            categorias_ids=tuple(receta.categorias_ids),
            fotografia_final=self._fotografia_portada(receta),
        )

    def a_resultado_escalado(
        self,
        receta: Receta,
        escalada: RecetaEscalada,
        nombres_ingredientes: dict[UUID, str],
    ) -> RecetaEscaladaResultado:
        """Traduce el calculo temporal del EscaladorRecetas.

        El escalado (Capitulo 3.8) solo recalcula cantidades: los pasos y
        las fotografias no dependen del rendimiento, asi que se copian tal
        cual desde la Receta original. Sin este paso quedarian vacios, ya
        que RecetaEscalada -el resultado del calculo del Dominio- solo
        transporta ingredientes.
        """
        pasos_y_fotos_por_preparacion = {
            p.id: p for p in receta.preparaciones
        }
        return RecetaEscaladaResultado(
            receta_id=escalada.receta_id,
            nombre=escalada.nombre,
            rendimiento_base=escalada.rendimiento_base.valor,
            rendimiento_solicitado=escalada.rendimiento_solicitado.valor,
            rendimiento_descripcion=escalada.rendimiento_solicitado.descripcion,
            factor=escalada.factor,
            preparaciones=tuple(
                self._preparacion_escalada(
                    preparacion,
                    pasos_y_fotos_por_preparacion.get(preparacion.preparacion_id),
                    nombres_ingredientes,
                )
                for preparacion in escalada.preparaciones
            ),
        )

    def _preparacion_escalada(
        self,
        preparacion,
        original: Preparacion | None,
        nombres_ingredientes: dict[UUID, str],
    ) -> PreparacionResultado:
        """Arma una preparacion escalada, con pasos y fotos del original."""
        return PreparacionResultado(
            id=preparacion.preparacion_id,
            nombre=preparacion.nombre,
            orden=preparacion.orden,
            ingredientes=tuple(
                IngredienteResultado(
                    ingrediente_preparacion_id=i.ingrediente_preparacion_id,
                    ingrediente_id=i.ingrediente_id,
                    nombre=nombres_ingredientes.get(i.ingrediente_id, ""),
                    texto_cantidad=i.texto_cantidad,
                    tipo_escalado=i.tipo_escalado.value,
                    cantidad=i.cantidad.valor if i.cantidad else None,
                    unidad=i.cantidad.unidad.simbolo if i.cantidad else None,
                    observacion=i.observacion,
                )
                for i in preparacion.ingredientes
            ),
            pasos=tuple(
                PasoResultado(id=p.id, orden=p.orden, descripcion=p.descripcion)
                for p in (original.pasos_ordenados if original else [])
            ),
            fotografias=tuple(
                FotografiaResultado(
                    id=f.id, ruta=f.ruta, tipo=f.tipo.value, descripcion=f.descripcion
                )
                for f in (original.fotografias if original else [])
            ),
        )

    def _preparacion(
        self, preparacion: Preparacion, nombres: dict[UUID, str]
    ) -> PreparacionResultado:
        """Traduce una Preparacion con ingredientes, pasos y fotografias."""
        return PreparacionResultado(
            id=preparacion.id,
            nombre=preparacion.nombre,
            orden=preparacion.orden,
            ingredientes=tuple(
                IngredienteResultado(
                    ingrediente_preparacion_id=i.id,
                    ingrediente_id=i.ingrediente_id,
                    nombre=nombres.get(i.ingrediente_id, ""),
                    texto_cantidad=_texto_cantidad(i.cantidad, i.tipo_escalado),
                    tipo_escalado=i.tipo_escalado.value,
                    cantidad=i.cantidad.valor if i.cantidad else None,
                    unidad=i.cantidad.unidad.simbolo if i.cantidad else None,
                    observacion=i.observacion,
                )
                for i in preparacion.ingredientes
            ),
            pasos=tuple(
                PasoResultado(id=p.id, orden=p.orden, descripcion=p.descripcion)
                for p in preparacion.pasos_ordenados
            ),
            fotografias=tuple(
                FotografiaResultado(
                    id=f.id,
                    ruta=f.ruta,
                    tipo=f.tipo.value,
                    descripcion=f.descripcion,
                )
                for f in preparacion.fotografias
            ),
        )

    def _fotografia_portada(self, receta: Receta) -> str | None:
        """Elige la foto que ilustra la tarjeta de receta.

        Prioriza la fotografia final, ya que muestra el resultado
        terminado. Si la receta todavia no tiene una -por ejemplo, recien
        se empezo a fotografiar el proceso-, usa la primera disponible en
        lugar de dejar la tarjeta sin imagen.
        """
        primera_de_proceso = None
        for preparacion in receta.preparaciones:
            for foto in preparacion.fotografias:
                if foto.tipo is TipoFotografia.FINAL:
                    return foto.ruta
                if primera_de_proceso is None:
                    primera_de_proceso = foto.ruta
        return primera_de_proceso


class EnsambladorListaCompras:
    """Traduce Listas de Compras a DTO."""

    def a_resultado(self, lista: ListaCompra) -> ListaCompraResultado:
        """Arma la vista de una Lista de Compras."""
        return ListaCompraResultado(
            id=lista.id,
            fecha=lista.fecha,
            usuario_id=lista.usuario_id,
            items=tuple(
                ItemCompraResultado(
                    id=item.id,
                    ingrediente_id=item.ingrediente_id,
                    nombre=item.nombre_ingrediente,
                    texto_cantidad=_texto_cantidad(item.cantidad, item.tipo_escalado),
                    comprado=item.comprado,
                )
                for item in lista.items
            ),
        )


class EnsambladorUsuarios:
    """Traduce Usuarios a DTO."""

    def a_resultado(self, usuario: Usuario) -> UsuarioResultado:
        """Arma la vista de un Usuario."""
        return UsuarioResultado(
            id=usuario.id,
            nombre=usuario.nombre,
            correo=usuario.correo,
            rol=usuario.rol.value,
            activo=usuario.activo,
        )
