"""Autorizacion de la capa de Aplicacion.

El Capitulo 5.4 asigna a esta capa la validacion de permisos. Los perfiles
provienen del Capitulo 1.7:

- Administrador: administra usuarios y catalogos.
- Usuario Familiar: crea, consulta, modifica y archiva recetas; genera
  listas de compras.

Decision D-9 (pendiente de confirmacion): la administracion de los
catalogos (Ingredientes, Categorias, Etiquetas y Fuentes) queda reservada
al Administrador, mientras que toda operacion sobre Recetas y Listas de
Compras esta disponible para cualquier usuario activo. El recetario es
compartido (Capitulo 1.5), de modo que un Usuario Familiar puede editar
recetas creadas por otro integrante.
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
        """Exige perfil Administrador (gestion de usuarios y catalogos)."""
        self.asegurar_activo(usuario)
        if not usuario.es_administrador:
            raise PermisoDenegado(
                "La operacion requiere perfil de Administrador."
            )

    def asegurar_puede_gestionar_recetas(self, usuario: Usuario) -> None:
        """Exige un usuario activo: el recetario es compartido."""
        self.asegurar_activo(usuario)
