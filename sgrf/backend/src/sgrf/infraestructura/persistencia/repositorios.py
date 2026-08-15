"""Repositorios sobre PostgreSQL (Django ORM).

Implementan los contratos definidos por el Dominio. Los Casos de Uso no
cambian una sola linea al pasar de los repositorios en memoria de las
pruebas a estos: esa es la finalidad de la inversion de dependencias del
Capitulo 5.
"""

from __future__ import annotations

from uuid import UUID

from django.db.models import Prefetch, Q

from ...dominio.entidades import (
    Categoria,
    Etiqueta,
    Fuente,
    Ingrediente,
    ListaCompra,
    Receta,
    Usuario,
)
from ...dominio.repositorios import (
    CategoriaRepositorio,
    EtiquetaRepositorio,
    FuenteRepositorio,
    IngredienteRepositorio,
    ListaCompraRepositorio,
    RecetaRepositorio,
    UsuarioRepositorio,
)
from ...dominio.servicios import CriteriosBusqueda
from ..recetario import models as m
from .mapeadores import (
    MapeadorCatalogo,
    MapeadorListasCompra,
    MapeadorRecetas,
    MapeadorUsuarios,
)


class RecetaRepositorioDjango(RecetaRepositorio):
    """Persistencia del agregado Receta.

    Guardar reescribe las Preparaciones completas. Es la estrategia mas
    simple y segura para un agregado de este tamanio: evita rastrear que
    componente cambio y garantiza que lo almacenado coincida exactamente
    con el estado del agregado en memoria. Siempre ocurre dentro de la
    transaccion abierta por la Unidad de Trabajo.
    """

    def __init__(self) -> None:
        self.mapeador = MapeadorRecetas()

    def _consulta_base(self):
        """Precarga el agregado completo para evitar el problema N+1."""
        return m.RecetaModelo.objects.prefetch_related(
            Prefetch(
                "preparaciones",
                queryset=m.PreparacionModelo.objects.order_by("orden").prefetch_related(
                    "ingredientes", "pasos", "fotografias"
                ),
            ),
            "categorias",
            "etiquetas",
            "notas",
        ).select_related("fuente")

    def obtener(self, receta_id: UUID) -> Receta | None:
        """Recupera una Receta completa."""
        fila = self._consulta_base().filter(id=receta_id).first()
        return self.mapeador.a_dominio(fila) if fila else None

    def guardar(self, receta: Receta) -> None:
        """Persiste el agregado completo."""
        fila = m.RecetaModelo.objects.filter(id=receta.id).first() or m.RecetaModelo()
        self.mapeador.volcar_cabecera(receta, fila)
        fila.save()

        fila.categorias.set(list(receta.categorias_ids))
        fila.etiquetas.set(list(receta.etiquetas_ids))

        self._reescribir_preparaciones(receta, fila)
        self._reescribir_notas(receta, fila)

    def _reescribir_preparaciones(self, receta: Receta, fila: m.RecetaModelo) -> None:
        """Reemplaza las Preparaciones almacenadas por las del agregado."""
        vigentes = [p.id for p in receta.preparaciones]
        fila.preparaciones.exclude(id__in=vigentes).delete()

        for preparacion in receta.preparaciones:
            fila_preparacion, _ = m.PreparacionModelo.objects.update_or_create(
                id=preparacion.id,
                defaults={
                    "receta": fila,
                    "nombre": preparacion.nombre,
                    "orden": preparacion.orden,
                },
            )
            self._reescribir_ingredientes(preparacion, fila_preparacion)
            self._reescribir_pasos(preparacion, fila_preparacion)
            self._reescribir_fotografias(preparacion, fila_preparacion)

    def _reescribir_ingredientes(self, preparacion, fila_preparacion) -> None:
        """Sincroniza los ingredientes de una Preparacion."""
        vigentes = [i.id for i in preparacion.ingredientes]
        fila_preparacion.ingredientes.exclude(id__in=vigentes).delete()
        for ingrediente in preparacion.ingredientes:
            m.IngredientePreparacionModelo.objects.update_or_create(
                id=ingrediente.id,
                defaults={
                    "preparacion": fila_preparacion,
                    "ingrediente_id": ingrediente.ingrediente_id,
                    "cantidad_valor": (
                        ingrediente.cantidad.valor if ingrediente.cantidad else None
                    ),
                    "cantidad_unidad": (
                        ingrediente.cantidad.unidad.simbolo
                        if ingrediente.cantidad
                        else None
                    ),
                    "tipo_escalado": ingrediente.tipo_escalado.value,
                    "observacion": ingrediente.observacion,
                },
            )

    def _reescribir_pasos(self, preparacion, fila_preparacion) -> None:
        """Sincroniza los pasos de una Preparacion."""
        vigentes = [p.id for p in preparacion.pasos]
        fila_preparacion.pasos.exclude(id__in=vigentes).delete()
        for paso in preparacion.pasos:
            m.PasoModelo.objects.update_or_create(
                id=paso.id,
                defaults={
                    "preparacion": fila_preparacion,
                    "descripcion": paso.descripcion,
                    "orden": paso.orden,
                },
            )

    def _reescribir_fotografias(self, preparacion, fila_preparacion) -> None:
        """Sincroniza las fotografias de una Preparacion."""
        vigentes = [f.id for f in preparacion.fotografias]
        fila_preparacion.fotografias.exclude(id__in=vigentes).delete()
        for foto in preparacion.fotografias:
            m.FotografiaModelo.objects.update_or_create(
                id=foto.id,
                defaults={
                    "preparacion": fila_preparacion,
                    "ruta": foto.ruta,
                    "tipo": foto.tipo.value,
                    "descripcion": foto.descripcion,
                },
            )

    def _reescribir_notas(self, receta: Receta, fila: m.RecetaModelo) -> None:
        """Sincroniza las notas de la Receta."""
        vigentes = [n.id for n in receta.notas]
        fila.notas.exclude(id__in=vigentes).delete()
        for nota in receta.notas:
            m.NotaModelo.objects.update_or_create(
                id=nota.id,
                defaults={
                    "receta": fila,
                    "texto": nota.texto,
                    "autor_id": nota.autor_id,
                    "fecha": nota.fecha,
                },
            )

    def eliminar(self, receta_id: UUID) -> None:
        """Elimina fisicamente una Receta. El flujo habitual es archivar."""
        m.RecetaModelo.objects.filter(id=receta_id).delete()

    def buscar(self, criterios: CriteriosBusqueda) -> list[Receta]:
        """Traduce los criterios del negocio a una consulta SQL.

        La regla vive en el Dominio; aqui solo se la expresa en el lenguaje
        del motor para no traer el recetario completo a memoria.
        """
        consulta = self._consulta_base()

        if not criterios.incluir_archivadas:
            consulta = consulta.filter(archivada=False)
        if criterios.solo_favoritas:
            consulta = consulta.filter(favorita=True)
        if criterios.fuente_id:
            consulta = consulta.filter(fuente_id=criterios.fuente_id)
        if criterios.categoria_id:
            consulta = consulta.filter(categorias__id=criterios.categoria_id)
        if criterios.etiqueta_id:
            consulta = consulta.filter(etiquetas__id=criterios.etiqueta_id)
        if criterios.ingrediente_id:
            consulta = consulta.filter(
                preparaciones__ingredientes__ingrediente_id=criterios.ingrediente_id
            )
        if criterios.texto:
            consulta = consulta.filter(
                Q(nombre__icontains=criterios.texto)
                | Q(descripcion__icontains=criterios.texto)
            )

        return [self.mapeador.a_dominio(fila) for fila in consulta.distinct()]

    def listar_todas(self, incluir_archivadas: bool = False) -> list[Receta]:
        """Devuelve el recetario."""
        consulta = self._consulta_base()
        if not incluir_archivadas:
            consulta = consulta.filter(archivada=False)
        return [self.mapeador.a_dominio(fila) for fila in consulta]

    def existe_con_nombre(self, nombre: str, excluir_id: UUID | None = None) -> bool:
        """Detecta duplicados sin distinguir mayusculas."""
        consulta = m.RecetaModelo.objects.filter(nombre__iexact=nombre.strip())
        if excluir_id:
            consulta = consulta.exclude(id=excluir_id)
        return consulta.exists()


class IngredienteRepositorioDjango(IngredienteRepositorio):
    """Persistencia del catalogo de Ingredientes."""

    def __init__(self) -> None:
        self.mapeador = MapeadorCatalogo()

    def obtener(self, ingrediente_id: UUID) -> Ingrediente | None:
        """Recupera un Ingrediente."""
        fila = m.IngredienteModelo.objects.filter(id=ingrediente_id).first()
        return self.mapeador.ingrediente(fila) if fila else None

    def obtener_varios(self, ids: set[UUID]) -> dict[UUID, Ingrediente]:
        """Recupera varios Ingredientes en una unica consulta."""
        if not ids:
            return {}
        return {
            fila.id: self.mapeador.ingrediente(fila)
            for fila in m.IngredienteModelo.objects.filter(id__in=ids)
        }

    def guardar(self, ingrediente: Ingrediente) -> None:
        """Persiste un Ingrediente."""
        m.IngredienteModelo.objects.update_or_create(
            id=ingrediente.id,
            defaults={
                "nombre": ingrediente.nombre,
                "descripcion": ingrediente.descripcion,
            },
        )

    def listar_todos(self) -> list[Ingrediente]:
        """Devuelve el catalogo completo."""
        return [
            self.mapeador.ingrediente(f) for f in m.IngredienteModelo.objects.all()
        ]

    def buscar_por_nombre(self, nombre: str) -> list[Ingrediente]:
        """Busca Ingredientes por coincidencia parcial."""
        return [
            self.mapeador.ingrediente(f)
            for f in m.IngredienteModelo.objects.filter(
                nombre__icontains=nombre.strip()
            )
        ]


class UsuarioRepositorioDjango(UsuarioRepositorio):
    """Persistencia de Usuarios."""

    def __init__(self) -> None:
        self.mapeador = MapeadorUsuarios()

    def obtener(self, usuario_id: UUID) -> Usuario | None:
        """Recupera un Usuario."""
        fila = m.UsuarioModelo.objects.filter(id=usuario_id).first()
        return self.mapeador.a_dominio(fila) if fila else None

    def obtener_por_correo(self, correo: str) -> Usuario | None:
        """Recupera un Usuario por su correo."""
        fila = m.UsuarioModelo.objects.filter(correo__iexact=correo.strip()).first()
        return self.mapeador.a_dominio(fila) if fila else None

    def guardar(self, usuario: Usuario) -> None:
        """Persiste un Usuario conservando su contrasenia."""
        fila = m.UsuarioModelo.objects.filter(id=usuario.id).first()
        if fila is None:
            fila = m.UsuarioModelo(id=usuario.id)
            fila.set_unusable_password()
        self.mapeador.volcar(usuario, fila)
        fila.save()

    def listar_todos(self, incluir_inactivos: bool = False) -> list[Usuario]:
        """Devuelve los Usuarios registrados."""
        consulta = m.UsuarioModelo.objects.all()
        if not incluir_inactivos:
            consulta = consulta.filter(activo=True)
        return [self.mapeador.a_dominio(f) for f in consulta]


class CategoriaRepositorioDjango(CategoriaRepositorio):
    """Persistencia de Categorias."""

    def __init__(self) -> None:
        self.mapeador = MapeadorCatalogo()

    def obtener(self, categoria_id: UUID) -> Categoria | None:
        """Recupera una Categoria."""
        fila = m.CategoriaModelo.objects.filter(id=categoria_id).first()
        return self.mapeador.categoria(fila) if fila else None

    def guardar(self, categoria: Categoria) -> None:
        """Persiste una Categoria."""
        m.CategoriaModelo.objects.update_or_create(
            id=categoria.id,
            defaults={
                "nombre": categoria.nombre,
                "categoria_padre_id": categoria.categoria_padre_id,
            },
        )

    def listar_todas(self) -> list[Categoria]:
        """Devuelve todas las Categorias."""
        return [self.mapeador.categoria(f) for f in m.CategoriaModelo.objects.all()]

    def listar_hijas(self, categoria_padre_id: UUID) -> list[Categoria]:
        """Devuelve las subcategorias de una Categoria."""
        return [
            self.mapeador.categoria(f)
            for f in m.CategoriaModelo.objects.filter(
                categoria_padre_id=categoria_padre_id
            )
        ]


class EtiquetaRepositorioDjango(EtiquetaRepositorio):
    """Persistencia de Etiquetas."""

    def __init__(self) -> None:
        self.mapeador = MapeadorCatalogo()

    def obtener(self, etiqueta_id: UUID) -> Etiqueta | None:
        """Recupera una Etiqueta."""
        fila = m.EtiquetaModelo.objects.filter(id=etiqueta_id).first()
        return self.mapeador.etiqueta(fila) if fila else None

    def guardar(self, etiqueta: Etiqueta) -> None:
        """Persiste una Etiqueta."""
        m.EtiquetaModelo.objects.update_or_create(
            id=etiqueta.id, defaults={"nombre": etiqueta.nombre}
        )

    def listar_todas(self) -> list[Etiqueta]:
        """Devuelve todas las Etiquetas."""
        return [self.mapeador.etiqueta(f) for f in m.EtiquetaModelo.objects.all()]


class FuenteRepositorioDjango(FuenteRepositorio):
    """Persistencia de Fuentes."""

    def __init__(self) -> None:
        self.mapeador = MapeadorCatalogo()

    def obtener(self, fuente_id: UUID) -> Fuente | None:
        """Recupera una Fuente."""
        fila = m.FuenteModelo.objects.filter(id=fuente_id).first()
        return self.mapeador.fuente(fila) if fila else None

    def guardar(self, fuente: Fuente) -> None:
        """Persiste una Fuente."""
        m.FuenteModelo.objects.update_or_create(
            id=fuente.id,
            defaults={"nombre": fuente.nombre, "detalle": fuente.detalle},
        )

    def listar_todas(self) -> list[Fuente]:
        """Devuelve todas las Fuentes."""
        return [self.mapeador.fuente(f) for f in m.FuenteModelo.objects.all()]


class ListaCompraRepositorioDjango(ListaCompraRepositorio):
    """Persistencia de Listas de Compras."""

    def __init__(self) -> None:
        self.mapeador = MapeadorListasCompra()

    def obtener(self, lista_id: UUID) -> ListaCompra | None:
        """Recupera una Lista con todos sus items."""
        fila = (
            m.ListaCompraModelo.objects.prefetch_related("items")
            .filter(id=lista_id)
            .first()
        )
        return self.mapeador.a_dominio(fila) if fila else None

    def guardar(self, lista: ListaCompra) -> None:
        """Persiste la Lista y reescribe sus items."""
        fila, _ = m.ListaCompraModelo.objects.update_or_create(
            id=lista.id,
            defaults={"usuario_id": lista.usuario_id, "fecha": lista.fecha},
        )
        vigentes = [i.id for i in lista.items]
        fila.items.exclude(id__in=vigentes).delete()
        for item in lista.items:
            m.ItemCompraModelo.objects.update_or_create(
                id=item.id,
                defaults={
                    "lista": fila,
                    "ingrediente_id": item.ingrediente_id,
                    "nombre_ingrediente": item.nombre_ingrediente,
                    "cantidad_valor": item.cantidad.valor if item.cantidad else None,
                    "cantidad_unidad": (
                        item.cantidad.unidad.simbolo if item.cantidad else None
                    ),
                    "tipo_escalado": item.tipo_escalado.value,
                    "comprado": item.comprado,
                },
            )

    def listar_por_usuario(self, usuario_id: UUID) -> list[ListaCompra]:
        """Devuelve las Listas de un Usuario."""
        return [
            self.mapeador.a_dominio(f)
            for f in m.ListaCompraModelo.objects.prefetch_related("items").filter(
                usuario_id=usuario_id
            )
        ]
