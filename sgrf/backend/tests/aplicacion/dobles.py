"""Repositorios en memoria para las pruebas de la capa de Aplicacion.

Implementan los contratos definidos por el Dominio sin base de datos. Su
existencia demuestra que la inversion de dependencias funciona: los casos
de uso se ejecutan completos sin Django ni PostgreSQL.

En la Etapa 3 se suman las implementaciones reales sobre PostgreSQL; los
casos de uso no cambiaran una sola linea.
"""

from __future__ import annotations

from uuid import UUID

from sgrf.aplicacion.unidad_de_trabajo import UnidadDeTrabajo
from sgrf.dominio.entidades import (
    Categoria,
    Etiqueta,
    Fuente,
    Ingrediente,
    ListaCompra,
    Receta,
    Usuario,
)
from sgrf.dominio.repositorios import (
    CategoriaRepositorio,
    EtiquetaRepositorio,
    FuenteRepositorio,
    IngredienteRepositorio,
    ListaCompraRepositorio,
    RecetaRepositorio,
    UsuarioRepositorio,
)
from sgrf.dominio.servicios import BuscadorRecetas, CriteriosBusqueda


class RecetasEnMemoria(RecetaRepositorio):
    """Almacen de Recetas en memoria."""

    def __init__(self) -> None:
        self.datos: dict[UUID, Receta] = {}

    def obtener(self, receta_id: UUID) -> Receta | None:
        return self.datos.get(receta_id)

    def guardar(self, receta: Receta) -> None:
        self.datos[receta.id] = receta

    def eliminar(self, receta_id: UUID) -> None:
        self.datos.pop(receta_id, None)

    def buscar(self, criterios: CriteriosBusqueda) -> list[Receta]:
        return BuscadorRecetas().buscar(list(self.datos.values()), criterios)

    def listar_todas(self, incluir_archivadas: bool = False) -> list[Receta]:
        return [
            receta
            for receta in self.datos.values()
            if incluir_archivadas or not receta.archivada
        ]

    def existe_con_nombre(self, nombre: str, excluir_id: UUID | None = None) -> bool:
        buscado = nombre.strip().lower()
        return any(
            receta.nombre.lower() == buscado and receta.id != excluir_id
            for receta in self.datos.values()
        )


class IngredientesEnMemoria(IngredienteRepositorio):
    """Almacen del catalogo de Ingredientes en memoria."""

    def __init__(self) -> None:
        self.datos: dict[UUID, Ingrediente] = {}

    def obtener(self, ingrediente_id: UUID) -> Ingrediente | None:
        return self.datos.get(ingrediente_id)

    def obtener_varios(self, ids: set[UUID]) -> dict[UUID, Ingrediente]:
        return {i: self.datos[i] for i in ids if i in self.datos}

    def guardar(self, ingrediente: Ingrediente) -> None:
        self.datos[ingrediente.id] = ingrediente

    def listar_todos(self) -> list[Ingrediente]:
        return list(self.datos.values())

    def buscar_por_nombre(self, nombre: str) -> list[Ingrediente]:
        buscado = nombre.strip().lower()
        return [i for i in self.datos.values() if buscado in i.nombre.lower()]


class UsuariosEnMemoria(UsuarioRepositorio):
    """Almacen de Usuarios en memoria."""

    def __init__(self) -> None:
        self.datos: dict[UUID, Usuario] = {}

    def obtener(self, usuario_id: UUID) -> Usuario | None:
        return self.datos.get(usuario_id)

    def obtener_por_correo(self, correo: str) -> Usuario | None:
        return next(
            (u for u in self.datos.values() if u.correo == correo.lower().strip()),
            None,
        )

    def guardar(self, usuario: Usuario) -> None:
        self.datos[usuario.id] = usuario

    def listar_todos(self, incluir_inactivos: bool = False) -> list[Usuario]:
        return [
            u for u in self.datos.values() if incluir_inactivos or u.activo
        ]


class CategoriasEnMemoria(CategoriaRepositorio):
    """Almacen de Categorias en memoria."""

    def __init__(self) -> None:
        self.datos: dict[UUID, Categoria] = {}

    def obtener(self, categoria_id: UUID) -> Categoria | None:
        return self.datos.get(categoria_id)

    def guardar(self, categoria: Categoria) -> None:
        self.datos[categoria.id] = categoria

    def listar_todas(self) -> list[Categoria]:
        return list(self.datos.values())

    def listar_hijas(self, categoria_padre_id: UUID) -> list[Categoria]:
        return [
            c
            for c in self.datos.values()
            if c.categoria_padre_id == categoria_padre_id
        ]


class EtiquetasEnMemoria(EtiquetaRepositorio):
    """Almacen de Etiquetas en memoria."""

    def __init__(self) -> None:
        self.datos: dict[UUID, Etiqueta] = {}

    def obtener(self, etiqueta_id: UUID) -> Etiqueta | None:
        return self.datos.get(etiqueta_id)

    def guardar(self, etiqueta: Etiqueta) -> None:
        self.datos[etiqueta.id] = etiqueta

    def listar_todas(self) -> list[Etiqueta]:
        return list(self.datos.values())


class FuentesEnMemoria(FuenteRepositorio):
    """Almacen de Fuentes en memoria."""

    def __init__(self) -> None:
        self.datos: dict[UUID, Fuente] = {}

    def obtener(self, fuente_id: UUID) -> Fuente | None:
        return self.datos.get(fuente_id)

    def guardar(self, fuente: Fuente) -> None:
        self.datos[fuente.id] = fuente

    def listar_todas(self) -> list[Fuente]:
        return list(self.datos.values())


class ListasCompraEnMemoria(ListaCompraRepositorio):
    """Almacen de Listas de Compras en memoria."""

    def __init__(self) -> None:
        self.datos: dict[UUID, ListaCompra] = {}

    def obtener(self, lista_id: UUID) -> ListaCompra | None:
        return self.datos.get(lista_id)

    def guardar(self, lista: ListaCompra) -> None:
        self.datos[lista.id] = lista

    def listar_por_usuario(self, usuario_id: UUID) -> list[ListaCompra]:
        return [l for l in self.datos.values() if l.usuario_id == usuario_id]


class UnidadDeTrabajoEnMemoria(UnidadDeTrabajo):
    """Unidad de Trabajo en memoria.

    Registra las confirmaciones y reversiones para que las pruebas puedan
    verificar el manejo transaccional.
    """

    def __init__(self) -> None:
        self.recetas = RecetasEnMemoria()
        self.ingredientes = IngredientesEnMemoria()
        self.usuarios = UsuariosEnMemoria()
        self.categorias = CategoriasEnMemoria()
        self.etiquetas = EtiquetasEnMemoria()
        self.fuentes = FuentesEnMemoria()
        self.listas_compra = ListasCompraEnMemoria()
        self.confirmaciones = 0
        self.reversiones = 0

    def confirmar(self) -> None:
        self.confirmaciones += 1

    def revertir(self) -> None:
        self.reversiones += 1
