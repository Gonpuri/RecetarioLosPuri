"""Interfaces de Repositorio del dominio del SGRF.

El dominio define QUE necesita persistir; la Infraestructura decide COMO
(ANALISIS.md, seccion 5.5). Estas interfaces invierten la dependencia: la
capa interna no conoce Django ni PostgreSQL.

Solo la Receta, raiz del agregado, posee un repositorio propio para sus
componentes internos; las Preparaciones, Pasos y Fotografias se persisten
junto a ella.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from ..entidades import (
    Categoria,
    Etiqueta,
    Fuente,
    Ingrediente,
    ListaCompra,
    Receta,
    Usuario,
)
from ..servicios.buscador_recetas import CriteriosBusqueda


class RecetaRepositorio(ABC):
    """Contrato de persistencia del agregado Receta."""

    @abstractmethod
    def obtener(self, receta_id: UUID) -> Receta | None:
        """Recupera una Receta completa con todas sus Preparaciones."""

    @abstractmethod
    def guardar(self, receta: Receta) -> None:
        """Persiste el agregado completo de forma transaccional."""

    @abstractmethod
    def eliminar(self, receta_id: UUID) -> None:
        """Elimina fisicamente una Receta.

        El flujo habitual es archivar (RF-008); esta operacion se reserva
        para tareas administrativas.
        """

    @abstractmethod
    def buscar(self, criterios: CriteriosBusqueda) -> list[Receta]:
        """Devuelve las Recetas que satisfacen los criterios indicados."""

    @abstractmethod
    def listar_todas(self, incluir_archivadas: bool = False) -> list[Receta]:
        """Devuelve el recetario completo."""

    @abstractmethod
    def existe_con_nombre(self, nombre: str, excluir_id: UUID | None = None) -> bool:
        """Indica si ya existe una Receta con ese nombre.

        Mitiga el riesgo de duplicados senialado en ANALISIS.md, 2.11.
        """


class IngredienteRepositorio(ABC):
    """Contrato de persistencia del catalogo de Ingredientes."""

    @abstractmethod
    def obtener(self, ingrediente_id: UUID) -> Ingrediente | None:
        """Recupera un Ingrediente del catalogo."""

    @abstractmethod
    def obtener_varios(self, ids: set[UUID]) -> dict[UUID, Ingrediente]:
        """Recupera varios Ingredientes indexados por identidad.

        Evita consultas repetidas al construir la Lista de Compras.
        """

    @abstractmethod
    def guardar(self, ingrediente: Ingrediente) -> None:
        """Persiste un Ingrediente del catalogo."""

    @abstractmethod
    def listar_todos(self) -> list[Ingrediente]:
        """Devuelve el catalogo completo de Ingredientes."""

    @abstractmethod
    def buscar_por_nombre(self, nombre: str) -> list[Ingrediente]:
        """Busca Ingredientes cuyo nombre contenga el texto indicado."""


class UsuarioRepositorio(ABC):
    """Contrato de persistencia de Usuarios."""

    @abstractmethod
    def obtener(self, usuario_id: UUID) -> Usuario | None:
        """Recupera un Usuario por su identidad."""

    @abstractmethod
    def obtener_por_correo(self, correo: str) -> Usuario | None:
        """Recupera un Usuario por su correo electronico."""

    @abstractmethod
    def guardar(self, usuario: Usuario) -> None:
        """Persiste un Usuario."""

    @abstractmethod
    def listar_todos(self, incluir_inactivos: bool = False) -> list[Usuario]:
        """Devuelve los Usuarios registrados."""


class CategoriaRepositorio(ABC):
    """Contrato de persistencia de Categorias y subcategorias."""

    @abstractmethod
    def obtener(self, categoria_id: UUID) -> Categoria | None:
        """Recupera una Categoria por su identidad."""

    @abstractmethod
    def guardar(self, categoria: Categoria) -> None:
        """Persiste una Categoria."""

    @abstractmethod
    def listar_todas(self) -> list[Categoria]:
        """Devuelve todas las Categorias."""

    @abstractmethod
    def listar_hijas(self, categoria_padre_id: UUID) -> list[Categoria]:
        """Devuelve las subcategorias de una Categoria."""


class EtiquetaRepositorio(ABC):
    """Contrato de persistencia de Etiquetas."""

    @abstractmethod
    def obtener(self, etiqueta_id: UUID) -> Etiqueta | None:
        """Recupera una Etiqueta por su identidad."""

    @abstractmethod
    def guardar(self, etiqueta: Etiqueta) -> None:
        """Persiste una Etiqueta."""

    @abstractmethod
    def listar_todas(self) -> list[Etiqueta]:
        """Devuelve todas las Etiquetas."""


class FuenteRepositorio(ABC):
    """Contrato de persistencia de Fuentes."""

    @abstractmethod
    def obtener(self, fuente_id: UUID) -> Fuente | None:
        """Recupera una Fuente por su identidad."""

    @abstractmethod
    def guardar(self, fuente: Fuente) -> None:
        """Persiste una Fuente."""

    @abstractmethod
    def listar_todas(self) -> list[Fuente]:
        """Devuelve todas las Fuentes."""


class ListaCompraRepositorio(ABC):
    """Contrato de persistencia de Listas de Compras.

    Se persiste la Lista, no la receta escalada que la origino (ADR-003).
    """

    @abstractmethod
    def obtener(self, lista_id: UUID) -> ListaCompra | None:
        """Recupera una Lista de Compras por su identidad."""

    @abstractmethod
    def guardar(self, lista: ListaCompra) -> None:
        """Persiste una Lista de Compras."""

    @abstractmethod
    def listar_por_usuario(self, usuario_id: UUID) -> list[ListaCompra]:
        """Devuelve las Listas de Compras de un Usuario."""


__all__ = [
    "CategoriaRepositorio",
    "EtiquetaRepositorio",
    "FuenteRepositorio",
    "IngredienteRepositorio",
    "ListaCompraRepositorio",
    "RecetaRepositorio",
    "UsuarioRepositorio",
]
