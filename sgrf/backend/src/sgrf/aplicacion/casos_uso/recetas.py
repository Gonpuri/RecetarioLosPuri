"""Casos de Uso de Recetas (RF-005 a RF-010).

Cada caso de uso orquesta: autoriza, recupera el agregado, delega la regla
de negocio en el Dominio y confirma la transaccion. No contiene reglas de
negocio propias.
"""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from ...dominio.entidades import (
    IngredientePreparacion,
    Preparacion,
    Receta,
)
from ...dominio.objetos_valor import Cantidad, Rendimiento, TipoEscalado, Unidad
from ...dominio.servicios import ValidadorRecetas
from ..dto import (
    ComandoCrearReceta,
    ComandoEditarReceta,
    DatosPreparacion,
    RecetaResultado,
)
from ..ensambladores import EnsambladorRecetas
from ..excepciones import ConflictoDeDatos, RecursoNoEncontrado
from .base import CasoDeUso


class ConstructorPreparaciones:
    """Traduce los datos recibidos por la interfaz a Preparaciones del Dominio.

    Aisla la conversion de tipos primitivos a Objetos de Valor para que los
    casos de uso no la repitan.
    """

    def construir(self, datos: DatosPreparacion) -> Preparacion:
        """Arma una Preparacion completa con ingredientes y pasos."""
        preparacion = Preparacion(nombre=datos.nombre)
        for ingrediente in datos.ingredientes:
            preparacion.agregar_ingrediente(self._ingrediente(ingrediente))
        for descripcion in datos.pasos:
            preparacion.agregar_paso(descripcion)
        return preparacion

    def _ingrediente(self, datos) -> IngredientePreparacion:
        """Arma un IngredientePreparacion resolviendo sus Objetos de Valor."""
        tipo = TipoEscalado(datos.tipo_escalado)
        cantidad = None
        if datos.cantidad is not None and datos.unidad is not None:
            cantidad = Cantidad(datos.cantidad, Unidad.desde_simbolo(datos.unidad))
        return IngredientePreparacion(
            ingrediente_id=datos.ingrediente_id,
            tipo_escalado=tipo,
            cantidad=cantidad,
            observacion=datos.observacion,
        )


class CrearReceta(CasoDeUso):
    """CU-001: registra una nueva Receta (RF-005).

    Valida el agregado completo antes de persistirlo, de modo que nunca se
    guarde una receta que incumpla las reglas del negocio.
    """

    def ejecutar(self, comando: ComandoCrearReceta) -> RecetaResultado:
        """Crea la receta y devuelve su representacion completa."""
        usuario = self._obtener_usuario(comando.solicitante_id)
        self.autorizacion.asegurar_puede_gestionar_recetas(usuario)

        self._asegurar_fuente_existente(comando.fuente_id)
        self._asegurar_nombre_disponible(comando.nombre)

        receta = Receta(
            nombre=comando.nombre,
            descripcion=comando.descripcion,
            rendimiento_base=Rendimiento(
                comando.rendimiento_base, comando.rendimiento_descripcion
            ),
            fuente_id=comando.fuente_id,
            autor_id=usuario.id,
        )

        constructor = ConstructorPreparaciones()
        for datos in comando.preparaciones:
            receta.agregar_preparacion(constructor.construir(datos))
        for categoria_id in comando.categorias_ids:
            receta.asignar_categoria(categoria_id)
        for etiqueta_id in comando.etiquetas_ids:
            receta.asignar_etiqueta(etiqueta_id)

        ValidadorRecetas().validar(receta).elevar_si_invalida()

        with self.uow:
            self.uow.recetas.guardar(receta)
            self.uow.confirmar()

        return self._ensamblar(receta)

    def _asegurar_fuente_existente(self, fuente_id: UUID) -> None:
        """RN-002: la fuente indicada debe existir en el catalogo."""
        if self.uow.fuentes.obtener(fuente_id) is None:
            raise RecursoNoEncontrado("Fuente", fuente_id)

    def _asegurar_nombre_disponible(self, nombre: str) -> None:
        """Mitiga el riesgo de recetas duplicadas (Capitulo 2.11)."""
        if self.uow.recetas.existe_con_nombre(nombre):
            raise ConflictoDeDatos(f"Ya existe una receta llamada '{nombre}'.")

    def _ensamblar(self, receta: Receta) -> RecetaResultado:
        """Traduce el agregado a su DTO resolviendo nombres del catalogo."""
        return EnsambladorRecetas().a_resultado(
            receta,
            self._nombres_de_ingredientes(receta.ingredientes_utilizados()),
            self._nombre_de_fuente(receta.fuente_id),
        )


class ConsultarReceta(CasoDeUso):
    """CU-002: devuelve una Receta completa (RF-007)."""

    def ejecutar(self, solicitante_id: UUID, receta_id: UUID) -> RecetaResultado:
        """Recupera la receta con sus nombres de catalogo resueltos."""
        usuario = self._obtener_usuario(solicitante_id)
        self.autorizacion.asegurar_activo(usuario)
        receta = self._obtener_receta(receta_id)
        return EnsambladorRecetas().a_resultado(
            receta,
            self._nombres_de_ingredientes(receta.ingredientes_utilizados()),
            self._nombre_de_fuente(receta.fuente_id),
        )


class EditarReceta(CasoDeUso):
    """CU-003: modifica los datos generales de una Receta (RF-006)."""

    def ejecutar(self, comando: ComandoEditarReceta) -> RecetaResultado:
        """Actualiza la informacion general delegando en el agregado."""
        usuario = self._obtener_usuario(comando.solicitante_id)
        self.autorizacion.asegurar_puede_gestionar_recetas(usuario)
        receta = self._obtener_receta(comando.receta_id)

        if comando.nombre and self.uow.recetas.existe_con_nombre(
            comando.nombre, excluir_id=receta.id
        ):
            raise ConflictoDeDatos(
                f"Ya existe otra receta llamada '{comando.nombre}'."
            )
        if comando.fuente_id and self.uow.fuentes.obtener(comando.fuente_id) is None:
            raise RecursoNoEncontrado("Fuente", comando.fuente_id)

        receta.actualizar_informacion(
            nombre=comando.nombre,
            descripcion=comando.descripcion,
            rendimiento_base=self._nuevo_rendimiento(comando, receta),
            fuente_id=comando.fuente_id,
        )

        with self.uow:
            self.uow.recetas.guardar(receta)
            self.uow.confirmar()

        return EnsambladorRecetas().a_resultado(
            receta,
            self._nombres_de_ingredientes(receta.ingredientes_utilizados()),
            self._nombre_de_fuente(receta.fuente_id),
        )

    def _nuevo_rendimiento(
        self, comando: ComandoEditarReceta, receta: Receta
    ) -> Rendimiento | None:
        """Arma el nuevo Rendimiento Base si el comando lo solicita."""
        if comando.rendimiento_base is None and comando.rendimiento_descripcion is None:
            return None
        valor = comando.rendimiento_base or receta.rendimiento_base.valor
        descripcion = (
            comando.rendimiento_descripcion or receta.rendimiento_base.descripcion
        )
        return Rendimiento(valor, descripcion)


class ArchivarReceta(CasoDeUso):
    """CU-004: archiva una Receta sin eliminarla (RF-008)."""

    def ejecutar(self, solicitante_id: UUID, receta_id: UUID) -> None:
        """Marca la receta como archivada."""
        usuario = self._obtener_usuario(solicitante_id)
        self.autorizacion.asegurar_puede_gestionar_recetas(usuario)
        receta = self._obtener_receta(receta_id)
        receta.archivar()
        with self.uow:
            self.uow.recetas.guardar(receta)
            self.uow.confirmar()


class RestaurarReceta(CasoDeUso):
    """CU-005: devuelve al estado activo una Receta archivada (RF-009)."""

    def ejecutar(self, solicitante_id: UUID, receta_id: UUID) -> None:
        """Quita la marca de archivada."""
        usuario = self._obtener_usuario(solicitante_id)
        self.autorizacion.asegurar_puede_gestionar_recetas(usuario)
        receta = self._obtener_receta(receta_id)
        receta.restaurar()
        with self.uow:
            self.uow.recetas.guardar(receta)
            self.uow.confirmar()


class DuplicarReceta(CasoDeUso):
    """CU-006: crea una variante a partir de una Receta existente (RF-010).

    La copia es profunda: la variante no comparte Preparaciones con el
    original, de modo que editarla jamas afecte la receta base (RN-004).
    Las fotografias no se copian, ya que pertenecen a la elaboracion
    original.
    """

    def ejecutar(
        self, solicitante_id: UUID, receta_id: UUID, nombre_variante: str
    ) -> RecetaResultado:
        """Duplica la receta bajo un nombre nuevo."""
        usuario = self._obtener_usuario(solicitante_id)
        self.autorizacion.asegurar_puede_gestionar_recetas(usuario)
        original = self._obtener_receta(receta_id)

        if self.uow.recetas.existe_con_nombre(nombre_variante):
            raise ConflictoDeDatos(
                f"Ya existe una receta llamada '{nombre_variante}'."
            )

        variante = Receta(
            nombre=nombre_variante,
            descripcion=original.descripcion,
            rendimiento_base=original.rendimiento_base,
            fuente_id=original.fuente_id,
            autor_id=usuario.id,
        )
        for preparacion in original.preparaciones_ordenadas:
            variante.agregar_preparacion(self._copiar_preparacion(preparacion))
        for categoria_id in original.categorias_ids:
            variante.asignar_categoria(categoria_id)
        for etiqueta_id in original.etiquetas_ids:
            variante.asignar_etiqueta(etiqueta_id)

        with self.uow:
            self.uow.recetas.guardar(variante)
            self.uow.confirmar()

        return EnsambladorRecetas().a_resultado(
            variante,
            self._nombres_de_ingredientes(variante.ingredientes_utilizados()),
            self._nombre_de_fuente(variante.fuente_id),
        )

    def _copiar_preparacion(self, preparacion: Preparacion) -> Preparacion:
        """Copia una Preparacion generando identidades nuevas."""
        copia = Preparacion(nombre=preparacion.nombre)
        for ingrediente in preparacion.ingredientes:
            copia.agregar_ingrediente(
                IngredientePreparacion(
                    ingrediente_id=ingrediente.ingrediente_id,
                    tipo_escalado=ingrediente.tipo_escalado,
                    cantidad=ingrediente.cantidad,
                    observacion=ingrediente.observacion,
                )
            )
        for paso in preparacion.pasos_ordenados:
            copia.agregar_paso(paso.descripcion)
        return copia


class MarcarFavorita(CasoDeUso):
    """CU-007: marca o desmarca una Receta como favorita (RF-043)."""

    def ejecutar(
        self, solicitante_id: UUID, receta_id: UUID, favorita: bool = True
    ) -> None:
        """Actualiza la marca de favorita."""
        usuario = self._obtener_usuario(solicitante_id)
        self.autorizacion.asegurar_puede_gestionar_recetas(usuario)
        receta = self._obtener_receta(receta_id)
        receta.marcar_favorita(favorita)
        with self.uow:
            self.uow.recetas.guardar(receta)
            self.uow.confirmar()
