"""Casos de Uso de Usuarios y catalogos (RF-001 a RF-004, RF-015, RF-029, RF-030).

Segun el Capitulo 1.7, la administracion de usuarios y catalogos
corresponde al perfil Administrador (decision D-9).
"""

from __future__ import annotations

from uuid import UUID

from ...dominio.entidades import (
    Categoria,
    Etiqueta,
    Fuente,
    Ingrediente,
    RolUsuario,
    Usuario,
)
from ..dto import UsuarioResultado
from ..ensambladores import EnsambladorUsuarios
from ..excepciones import ConflictoDeDatos, RecursoNoEncontrado
from .base import CasoDeUso


class GestionarUsuarios(CasoDeUso):
    """CU-016: alta, modificacion y baja logica de Usuarios (RF-001 a RF-004)."""

    def registrar(
        self,
        solicitante_id: UUID,
        nombre: str,
        correo: str,
        rol: str = "usuario_familiar",
    ) -> UsuarioResultado:
        """Registra un nuevo Usuario familiar (RF-001)."""
        solicitante = self._obtener_usuario(solicitante_id)
        self.autorizacion.asegurar_administrador(solicitante)

        if self.uow.usuarios.obtener_por_correo(correo.lower().strip()):
            raise ConflictoDeDatos(f"Ya existe un usuario con el correo {correo}.")

        usuario = Usuario(nombre=nombre, correo=correo, rol=RolUsuario(rol))
        with self.uow:
            self.uow.usuarios.guardar(usuario)
            self.uow.confirmar()
        return EnsambladorUsuarios().a_resultado(usuario)

    def modificar(
        self,
        solicitante_id: UUID,
        usuario_id: UUID,
        nombre: str | None = None,
        rol: str | None = None,
    ) -> UsuarioResultado:
        """Modifica los datos de un Usuario (RF-002 y RF-004)."""
        solicitante = self._obtener_usuario(solicitante_id)
        self.autorizacion.asegurar_administrador(solicitante)
        usuario = self._obtener_usuario(usuario_id)

        if nombre and nombre.strip():
            usuario.nombre = nombre.strip()
        if rol:
            usuario.rol = RolUsuario(rol)

        with self.uow:
            self.uow.usuarios.guardar(usuario)
            self.uow.confirmar()
        return EnsambladorUsuarios().a_resultado(usuario)

    def desactivar(self, solicitante_id: UUID, usuario_id: UUID) -> None:
        """Desactiva un Usuario conservando su historial (RF-003)."""
        solicitante = self._obtener_usuario(solicitante_id)
        self.autorizacion.asegurar_administrador(solicitante)
        if solicitante_id == usuario_id:
            raise ConflictoDeDatos(
                "Un administrador no puede desactivar su propia cuenta."
            )
        usuario = self._obtener_usuario(usuario_id)
        usuario.desactivar()
        with self.uow:
            self.uow.usuarios.guardar(usuario)
            self.uow.confirmar()

    def listar(
        self, solicitante_id: UUID, incluir_inactivos: bool = False
    ) -> list[UsuarioResultado]:
        """Lista los Usuarios registrados."""
        solicitante = self._obtener_usuario(solicitante_id)
        self.autorizacion.asegurar_administrador(solicitante)
        ensamblador = EnsambladorUsuarios()
        return [
            ensamblador.a_resultado(usuario)
            for usuario in self.uow.usuarios.listar_todos(incluir_inactivos)
        ]


class GestionarCatalogoIngredientes(CasoDeUso):
    """CU-017: catalogo reutilizable de Ingredientes (RF-015).

    Decision D-19: a diferencia del resto de los catalogos, cualquier
    usuario activo puede dar de alta un Ingrediente, no solo el
    Administrador. Se habilita para que quien carga una receta no dependa
    de un tercero cuando el ingrediente que necesita todavia no existe.
    Categorias, Etiquetas y Fuentes siguen reservadas al Administrador
    (decision D-9): a diferencia de un ingrediente puntual, definen la
    clasificacion del recetario completo.
    """

    def crear(
        self, solicitante_id: UUID, nombre: str, descripcion: str = ""
    ) -> UUID:
        """Da de alta un Ingrediente en el catalogo."""
        solicitante = self._obtener_usuario(solicitante_id)
        self.autorizacion.asegurar_puede_gestionar_recetas(solicitante)

        if self._existe_con_nombre(nombre):
            raise ConflictoDeDatos(f"Ya existe el ingrediente '{nombre}'.")

        ingrediente = Ingrediente(nombre=nombre, descripcion=descripcion)
        with self.uow:
            self.uow.ingredientes.guardar(ingrediente)
            self.uow.confirmar()
        return ingrediente.id

    def listar(self, solicitante_id: UUID) -> list[Ingrediente]:
        """Devuelve el catalogo completo para alimentar los formularios."""
        solicitante = self._obtener_usuario(solicitante_id)
        self.autorizacion.asegurar_activo(solicitante)
        return self.uow.ingredientes.listar_todos()

    def _existe_con_nombre(self, nombre: str) -> bool:
        """Evita duplicar entradas del catalogo (Capitulo 2.11)."""
        buscado = nombre.strip().lower()
        return any(
            ingrediente.nombre.lower() == buscado
            for ingrediente in self.uow.ingredientes.buscar_por_nombre(nombre)
        )


class GestionarCategorias(CasoDeUso):
    """CU-018: categorias y subcategorias (RF-029)."""

    def crear(
        self,
        solicitante_id: UUID,
        nombre: str,
        categoria_padre_id: UUID | None = None,
    ) -> UUID:
        """Crea una Categoria o subcategoria."""
        solicitante = self._obtener_usuario(solicitante_id)
        self.autorizacion.asegurar_administrador(solicitante)

        if categoria_padre_id is not None:
            if self.uow.categorias.obtener(categoria_padre_id) is None:
                raise RecursoNoEncontrado("Categoria", categoria_padre_id)

        categoria = Categoria(nombre=nombre, categoria_padre_id=categoria_padre_id)
        with self.uow:
            self.uow.categorias.guardar(categoria)
            self.uow.confirmar()
        return categoria.id

    def listar(self, solicitante_id: UUID) -> list[Categoria]:
        """Devuelve todas las Categorias."""
        solicitante = self._obtener_usuario(solicitante_id)
        self.autorizacion.asegurar_activo(solicitante)
        return self.uow.categorias.listar_todas()


class GestionarEtiquetas(CasoDeUso):
    """CU-019: etiquetas transversales (RF-028)."""

    def crear(self, solicitante_id: UUID, nombre: str) -> UUID:
        """Crea una Etiqueta."""
        solicitante = self._obtener_usuario(solicitante_id)
        self.autorizacion.asegurar_administrador(solicitante)
        etiqueta = Etiqueta(nombre=nombre)
        with self.uow:
            self.uow.etiquetas.guardar(etiqueta)
            self.uow.confirmar()
        return etiqueta.id

    def listar(self, solicitante_id: UUID) -> list[Etiqueta]:
        """Devuelve todas las Etiquetas."""
        solicitante = self._obtener_usuario(solicitante_id)
        self.autorizacion.asegurar_activo(solicitante)
        return self.uow.etiquetas.listar_todas()


class GestionarFuentes(CasoDeUso):
    """CU-020: fuentes de las recetas (RF-030)."""

    def crear(self, solicitante_id: UUID, nombre: str, detalle: str = "") -> UUID:
        """Crea una Fuente."""
        solicitante = self._obtener_usuario(solicitante_id)
        self.autorizacion.asegurar_administrador(solicitante)
        fuente = Fuente(nombre=nombre, detalle=detalle)
        with self.uow:
            self.uow.fuentes.guardar(fuente)
            self.uow.confirmar()
        return fuente.id

    def listar(self, solicitante_id: UUID) -> list[Fuente]:
        """Devuelve todas las Fuentes."""
        solicitante = self._obtener_usuario(solicitante_id)
        self.autorizacion.asegurar_activo(solicitante)
        return self.uow.fuentes.listar_todas()


class AsignarClasificacion(CasoDeUso):
    """CU-021: asigna categorias y etiquetas a una Receta (RF-027 y RF-028).

    A diferencia de la creacion de catalogos, clasificar una receta es una
    operacion sobre el recetario y la puede realizar cualquier usuario
    activo.
    """

    def asignar_categoria(
        self, solicitante_id: UUID, receta_id: UUID, categoria_id: UUID
    ) -> None:
        """Asocia una Categoria existente a la Receta."""
        receta = self._preparar(solicitante_id, receta_id)
        if self.uow.categorias.obtener(categoria_id) is None:
            raise RecursoNoEncontrado("Categoria", categoria_id)
        receta.asignar_categoria(categoria_id)
        self._guardar(receta)

    def quitar_categoria(
        self, solicitante_id: UUID, receta_id: UUID, categoria_id: UUID
    ) -> None:
        """Desasocia una Categoria de la Receta."""
        receta = self._preparar(solicitante_id, receta_id)
        receta.quitar_categoria(categoria_id)
        self._guardar(receta)

    def asignar_etiqueta(
        self, solicitante_id: UUID, receta_id: UUID, etiqueta_id: UUID
    ) -> None:
        """Asocia una Etiqueta existente a la Receta."""
        receta = self._preparar(solicitante_id, receta_id)
        if self.uow.etiquetas.obtener(etiqueta_id) is None:
            raise RecursoNoEncontrado("Etiqueta", etiqueta_id)
        receta.asignar_etiqueta(etiqueta_id)
        self._guardar(receta)

    def quitar_etiqueta(
        self, solicitante_id: UUID, receta_id: UUID, etiqueta_id: UUID
    ) -> None:
        """Desasocia una Etiqueta de la Receta."""
        receta = self._preparar(solicitante_id, receta_id)
        receta.quitar_etiqueta(etiqueta_id)
        self._guardar(receta)

    def _preparar(self, solicitante_id: UUID, receta_id: UUID):
        """Autoriza al solicitante y recupera la receta."""
        usuario = self._obtener_usuario(solicitante_id)
        self.autorizacion.asegurar_puede_gestionar_recetas(usuario)
        return self._obtener_receta(receta_id)

    def _guardar(self, receta) -> None:
        """Persiste el agregado dentro de una transaccion."""
        with self.uow:
            self.uow.recetas.guardar(receta)
            self.uow.confirmar()
