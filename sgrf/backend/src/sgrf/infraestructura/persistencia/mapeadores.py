"""Mapeadores entre los modelos de persistencia y las entidades del Dominio.

Concentran la traduccion en un unico lugar. La direccion es siempre la
misma: el Dominio ignora por completo la existencia de Django.

Los Objetos de Valor se reconstruyen aqui, no se persisten como tales: la
Cantidad se guarda descompuesta en valor y unidad, y el Rendimiento en
valor y descripcion.
"""

from __future__ import annotations

from ...dominio.entidades import (
    Categoria,
    Etiqueta,
    Fotografia,
    Fuente,
    Ingrediente,
    IngredientePreparacion,
    ItemCompra,
    ListaCompra,
    Nota,
    Paso,
    Preparacion,
    Receta,
    RolUsuario,
    TipoFotografia,
    Usuario,
)
from ...dominio.objetos_valor import Cantidad, Rendimiento, TipoEscalado, Unidad
from ..recetario import models as m


def _a_cantidad(valor, simbolo) -> Cantidad | None:
    """Reconstruye una Cantidad desde sus columnas, tolerando el nulo."""
    if valor is None or not simbolo:
        return None
    return Cantidad(valor, Unidad.desde_simbolo(simbolo))


class MapeadorUsuarios:
    """Traduce Usuarios entre persistencia y Dominio."""

    def a_dominio(self, fila: m.UsuarioModelo) -> Usuario:
        """Construye la entidad a partir de la fila."""
        return Usuario(
            nombre=fila.nombre,
            correo=fila.correo,
            rol=RolUsuario(fila.rol),
            activo=fila.activo,
            id=fila.id,
        )

    def volcar(self, usuario: Usuario, fila: m.UsuarioModelo) -> m.UsuarioModelo:
        """Vuelca la entidad sobre la fila sin tocar la contrasenia."""
        fila.nombre = usuario.nombre
        fila.correo = usuario.correo
        fila.rol = usuario.rol.value
        fila.activo = usuario.activo
        return fila


class MapeadorCatalogo:
    """Traduce las entidades de catalogo, que son planas."""

    def fuente(self, fila: m.FuenteModelo) -> Fuente:
        """Construye una Fuente."""
        return Fuente(nombre=fila.nombre, detalle=fila.detalle, id=fila.id)

    def categoria(self, fila: m.CategoriaModelo) -> Categoria:
        """Construye una Categoria conservando su jerarquia."""
        return Categoria(
            nombre=fila.nombre,
            categoria_padre_id=fila.categoria_padre_id,
            id=fila.id,
        )

    def etiqueta(self, fila: m.EtiquetaModelo) -> Etiqueta:
        """Construye una Etiqueta."""
        return Etiqueta(nombre=fila.nombre, id=fila.id)

    def ingrediente(self, fila: m.IngredienteModelo) -> Ingrediente:
        """Construye un Ingrediente del catalogo."""
        return Ingrediente(
            nombre=fila.nombre, descripcion=fila.descripcion, id=fila.id
        )


class MapeadorRecetas:
    """Traduce el agregado Receta completo.

    La reconstruccion evita los constructores que renumeran o validan
    (`agregar_preparacion`, `agregar_paso`): los datos ya fueron validados
    al guardarse, y reejecutar esa logica alteraria el orden almacenado.
    """

    def a_dominio(self, fila: m.RecetaModelo) -> Receta:
        """Reconstruye el agregado completo desde la base de datos."""
        receta = Receta(
            nombre=fila.nombre,
            descripcion=fila.descripcion,
            rendimiento_base=Rendimiento(
                fila.rendimiento_valor, fila.rendimiento_descripcion
            ),
            fuente_id=fila.fuente_id,
            archivada=fila.archivada,
            favorita=fila.favorita,
            autor_id=fila.autor_id,
            fecha_creacion=fila.fecha_creacion,
            id=fila.id,
        )
        receta.preparaciones = [
            self._preparacion(p) for p in fila.preparaciones.all()
        ]
        receta.categorias_ids = {c.id for c in fila.categorias.all()}
        receta.etiquetas_ids = {e.id for e in fila.etiquetas.all()}
        receta.notas = [
            Nota(
                texto=n.texto,
                autor_id=n.autor_id,
                fecha=n.fecha,
                id=n.id,
            )
            for n in fila.notas.all()
        ]
        return receta

    def _preparacion(self, fila: m.PreparacionModelo) -> Preparacion:
        """Reconstruye una Preparacion con todos sus componentes."""
        preparacion = Preparacion(nombre=fila.nombre, orden=fila.orden, id=fila.id)
        preparacion.ingredientes = [
            IngredientePreparacion(
                ingrediente_id=i.ingrediente_id,
                tipo_escalado=TipoEscalado(i.tipo_escalado),
                cantidad=_a_cantidad(i.cantidad_valor, i.cantidad_unidad),
                observacion=i.observacion,
                id=i.id,
            )
            for i in fila.ingredientes.all()
        ]
        preparacion.pasos = [
            Paso(descripcion=p.descripcion, orden=p.orden, id=p.id)
            for p in fila.pasos.all()
        ]
        preparacion.fotografias = [
            Fotografia(
                ruta=f.ruta,
                tipo=TipoFotografia(f.tipo),
                descripcion=f.descripcion,
                id=f.id,
            )
            for f in fila.fotografias.all()
        ]
        return preparacion

    def volcar_cabecera(
        self, receta: Receta, fila: m.RecetaModelo
    ) -> m.RecetaModelo:
        """Vuelca los datos generales de la Receta sobre la fila."""
        fila.id = receta.id
        fila.nombre = receta.nombre
        fila.descripcion = receta.descripcion
        fila.rendimiento_valor = receta.rendimiento_base.valor
        fila.rendimiento_descripcion = receta.rendimiento_base.descripcion
        fila.fuente_id = receta.fuente_id
        fila.archivada = receta.archivada
        fila.favorita = receta.favorita
        fila.autor_id = receta.autor_id
        fila.fecha_creacion = receta.fecha_creacion
        return fila


class MapeadorListasCompra:
    """Traduce Listas de Compras."""

    def a_dominio(self, fila: m.ListaCompraModelo) -> ListaCompra:
        """Reconstruye la Lista con todos sus items."""
        lista = ListaCompra(
            usuario_id=fila.usuario_id, fecha=fila.fecha, id=fila.id
        )
        lista.items = [
            ItemCompra(
                ingrediente_id=i.ingrediente_id,
                nombre_ingrediente=i.nombre_ingrediente,
                cantidad=_a_cantidad(i.cantidad_valor, i.cantidad_unidad),
                tipo_escalado=TipoEscalado(i.tipo_escalado),
                comprado=i.comprado,
                id=i.id,
            )
            for i in fila.items.all()
        ]
        return lista
