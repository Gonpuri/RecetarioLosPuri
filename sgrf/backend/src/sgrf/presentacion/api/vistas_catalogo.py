"""Vistas de catalogos y usuarios.

Los catalogos se consultan constantemente desde los formularios del front,
de modo que su lectura esta abierta a cualquier usuario activo; el alta
queda reservada al Administrador (decision D-9).
"""

from __future__ import annotations

from rest_framework.response import Response

from ...aplicacion.casos_uso import (
    GestionarCatalogoIngredientes,
    GestionarCategorias,
    GestionarEtiquetas,
    GestionarFuentes,
    GestionarUsuarios,
)
from ...infraestructura.recetario.models import UsuarioModelo
from . import serializadores as s
from .soporte import correcto, creado
from .vistas_recetas import VistaBase


class IngredientesVista(VistaBase):
    """Catalogo de Ingredientes (RF-015)."""

    def get(self, peticion):
        """Lista el catalogo para alimentar los formularios."""
        ingredientes = GestionarCatalogoIngredientes(self.uow).listar(
            self.solicitante_id
        )
        return Response(
            [
                {
                    "id": str(i.id),
                    "nombre": i.nombre,
                    "descripcion": i.descripcion,
                }
                for i in ingredientes
            ]
        )

    def post(self, peticion):
        """Da de alta un Ingrediente."""
        datos = self.validar(s.IngredienteCatalogoEntrada)
        identidad = GestionarCatalogoIngredientes(self.uow).crear(
            self.solicitante_id, datos["nombre"], datos.get("descripcion", "")
        )
        return creado({"id": identidad, "nombre": datos["nombre"]})


class CategoriasVista(VistaBase):
    """Categorias y subcategorias (RF-029)."""

    def get(self, peticion):
        """Lista las categorias con su jerarquia."""
        categorias = GestionarCategorias(self.uow).listar(self.solicitante_id)
        return Response(
            [
                {
                    "id": str(c.id),
                    "nombre": c.nombre,
                    "categoria_padre_id": (
                        str(c.categoria_padre_id) if c.categoria_padre_id else None
                    ),
                }
                for c in categorias
            ]
        )

    def post(self, peticion):
        """Crea una categoria o subcategoria."""
        datos = self.validar(s.CategoriaEntrada)
        identidad = GestionarCategorias(self.uow).crear(
            self.solicitante_id, datos["nombre"], datos.get("categoria_padre_id")
        )
        return creado({"id": identidad, "nombre": datos["nombre"]})


class EtiquetasVista(VistaBase):
    """Etiquetas transversales (RF-028)."""

    def get(self, peticion):
        """Lista las etiquetas."""
        etiquetas = GestionarEtiquetas(self.uow).listar(self.solicitante_id)
        return Response(
            [{"id": str(e.id), "nombre": e.nombre} for e in etiquetas]
        )

    def post(self, peticion):
        """Crea una etiqueta."""
        datos = self.validar(s.NombreEntrada)
        identidad = GestionarEtiquetas(self.uow).crear(
            self.solicitante_id, datos["nombre"]
        )
        return creado({"id": identidad, "nombre": datos["nombre"]})


class FuentesVista(VistaBase):
    """Fuentes de las recetas (RF-030)."""

    def get(self, peticion):
        """Lista las fuentes."""
        fuentes = GestionarFuentes(self.uow).listar(self.solicitante_id)
        return Response(
            [
                {"id": str(f.id), "nombre": f.nombre, "detalle": f.detalle}
                for f in fuentes
            ]
        )

    def post(self, peticion):
        """Crea una fuente."""
        datos = self.validar(s.FuenteEntrada)
        identidad = GestionarFuentes(self.uow).crear(
            self.solicitante_id, datos["nombre"], datos.get("detalle", "")
        )
        return creado({"id": identidad, "nombre": datos["nombre"]})


class UsuariosVista(VistaBase):
    """Gestion de Usuarios (RF-001 a RF-004).

    El alta se completa en dos tiempos: el Caso de Uso registra al usuario
    y luego se le asigna la contrasenia, que es un detalle tecnico ajeno al
    Dominio.
    """

    def get(self, peticion):
        """Lista los usuarios registrados."""
        usuarios = GestionarUsuarios(self.uow).listar(
            self.solicitante_id,
            incluir_inactivos=peticion.query_params.get("incluir_inactivos") == "true",
        )
        return correcto(usuarios)

    def post(self, peticion):
        """Registra un usuario y le asigna su contrasenia."""
        datos = self.validar(s.UsuarioEntrada)
        resultado = GestionarUsuarios(self.uow).registrar(
            self.solicitante_id,
            nombre=datos["nombre"],
            correo=datos["correo"],
            rol=datos["rol"],
        )
        fila = UsuarioModelo.objects.get(id=resultado.id)
        fila.set_password(datos["clave"])
        fila.save(update_fields=["password"])
        return creado(resultado)


class UsuarioVista(VistaBase):
    """Usuario individual (RF-002 y RF-003)."""

    def delete(self, peticion, usuario_id):
        """Desactiva el usuario conservando su historial."""
        GestionarUsuarios(self.uow).desactivar(self.solicitante_id, usuario_id)
        return correcto()


class PerfilVista(VistaBase):
    """Datos del usuario autenticado.

    El front la consulta al iniciar sesion para saber que opciones mostrar.
    """

    def get(self, peticion):
        """Devuelve el perfil propio."""
        usuario = peticion.user
        return Response(
            {
                "id": str(usuario.id),
                "nombre": usuario.nombre,
                "correo": usuario.correo,
                "rol": usuario.rol,
                "activo": usuario.activo,
            }
        )
