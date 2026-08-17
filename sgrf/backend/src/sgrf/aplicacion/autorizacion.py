"""Autorizacion de la capa de Aplicacion.

El Capitulo 5.4 asigna a esta capa la validacion de permisos. Los perfiles
provienen del Capitulo 1.7:

- Administrador: administra usuarios, catalogos y el contenido de las
  recetas ya creadas.
- Usuario Familiar: consulta el recetario, crea recetas y genera listas de
  compras.

Decision D-20: crear una Receta queda abierto a cualquier usuario activo
-es lo que hace crecer el recetario-, pero modificar una receta ya
existente (datos generales, preparaciones, ingredientes, pasos,
fotografias, notas, categorias y etiquetas; archivar o restaurar) requiere
Administrador. Se separa asi para que ningun integrante pueda alterar sin
querer una receta que cargo otra persona.

Duplicar una receta cuenta como crear -genera una copia independiente, la
original no se toca (RN-004)- asi que sigue abierto a cualquier usuario
activo, igual que marcar una receta como favorita, que es una preferencia
personal y no una modificacion del contenido.

Decision D-9: la administracion de Categorias, Etiquetas y Fuentes sigue
reservada al Administrador. Decision D-19: crear un Ingrediente del
catalogo es la unica excepcion abierta a cualquier usuario activo, para
que cargar una receta no dependa de un tercero cuando el ingrediente
todavia no existe.
"""

from __future__ import annotations

from ..dominio.entidades import Usuario
from .excepciones import PermisoDenegado, UsuarioInactivo


class Autorizacion:
    """Verifica que un Usuario pueda ejecutar una operacion."""

    def asegurar_activo(self, usuario: Usuario) -> None:
        """Exige que el usuario se encuentre habilitado."""
        if not usuario.activo:
            raise UsuarioInactivo(
                f"El usuario {usuario.nombre} se encuentra desactivado."
            )

    def asegurar_administrador(self, usuario: Usuario) -> None:
        """Exige perfil Administrador.

        Cubre la gestion de usuarios y catalogos (Categorias, Etiquetas,
        Fuentes) y, desde la decision D-20, tambien la edicion del
        contenido de una Receta ya existente.
        """
        self.asegurar_activo(usuario)
        if not usuario.es_administrador:
            raise PermisoDenegado(
                "La operacion requiere perfil de Administrador."
            )

    def asegurar_puede_gestionar_recetas(self, usuario: Usuario) -> None:
        """Exige un usuario activo.

        Cubre las operaciones que no modifican una receta ya existente:
        crearla, duplicarla o marcarla como favorita (decision D-20).
        """
        self.asegurar_activo(usuario)
