"""Casos de Uso de Preparaciones y sus componentes (RF-011 a RF-026).

Todas las operaciones ingresan por la Receta, raiz del agregado (ADR-001):
ningun caso de uso persiste una Preparacion por separado.
"""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from ...dominio.entidades import (
    Fotografia,
    IngredientePreparacion,
    Nota,
    TipoFotografia,
)
from ...dominio.objetos_valor import Cantidad, TipoEscalado, Unidad
from ..dto import DatosIngrediente, DatosPreparacion
from ..excepciones import RecursoNoEncontrado
from .base import CasoDeUso
from .recetas import ConstructorPreparaciones


class GestionarPreparaciones(CasoDeUso):
    """CU-008: alta, baja y reordenamiento de Preparaciones (RF-011 a RF-014)."""

    def agregar(
        self, solicitante_id: UUID, receta_id: UUID, datos: DatosPreparacion
    ) -> UUID:
        """Incorpora una Preparacion y devuelve su identidad (RF-011)."""
        receta = self._preparar(solicitante_id, receta_id)
        preparacion = ConstructorPreparaciones().construir(datos)
        receta.agregar_preparacion(preparacion)
        self._guardar(receta)
        return preparacion.id

    def renombrar(
        self,
        solicitante_id: UUID,
        receta_id: UUID,
        preparacion_id: UUID,
        nombre: str,
    ) -> None:
        """Modifica el nombre de una Preparacion (RF-012)."""
        receta = self._preparar(solicitante_id, receta_id)
        preparacion = receta.obtener_preparacion(preparacion_id)
        preparacion.nombre = nombre.strip() or preparacion.nombre
        self._guardar(receta)

    def eliminar(
        self, solicitante_id: UUID, receta_id: UUID, preparacion_id: UUID
    ) -> None:
        """Elimina una Preparacion respetando RN-003 (RF-013)."""
        receta = self._preparar(solicitante_id, receta_id)
        receta.quitar_preparacion(preparacion_id)
        self._guardar(receta)

    def reordenar(
        self, solicitante_id: UUID, receta_id: UUID, ids_en_orden: list[UUID]
    ) -> None:
        """Reordena las Preparaciones de la receta (RF-014)."""
        receta = self._preparar(solicitante_id, receta_id)
        receta.reordenar_preparaciones(ids_en_orden)
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


class GestionarIngredientesDePreparacion(CasoDeUso):
    """CU-009: ingredientes de una Preparacion (RF-016 a RF-018)."""

    def agregar(
        self,
        solicitante_id: UUID,
        receta_id: UUID,
        preparacion_id: UUID,
        datos: DatosIngrediente,
    ) -> UUID:
        """Agrega un ingrediente a la Preparacion (RF-016)."""
        receta = self._preparar(solicitante_id, receta_id)
        self._asegurar_ingrediente_existente(datos.ingrediente_id)
        preparacion = receta.obtener_preparacion(preparacion_id)
        ingrediente = self._construir(datos)
        preparacion.agregar_ingrediente(ingrediente)
        self._guardar(receta)
        return ingrediente.id

    def modificar(
        self,
        solicitante_id: UUID,
        receta_id: UUID,
        preparacion_id: UUID,
        ingrediente_preparacion_id: UUID,
        cantidad: Decimal | None = None,
        unidad: str | None = None,
        tipo_escalado: str | None = None,
        observacion: str | None = None,
    ) -> None:
        """Modifica cantidad, unidad, tipo de escalado u observacion (RF-017).

        Se reemplaza el ingrediente por una instancia nueva para que el
        constructor vuelva a validar la coherencia entre TipoEscalado y
        Cantidad.
        """
        receta = self._preparar(solicitante_id, receta_id)
        preparacion = receta.obtener_preparacion(preparacion_id)
        actual = preparacion.obtener_ingrediente(ingrediente_preparacion_id)

        tipo = TipoEscalado(tipo_escalado) if tipo_escalado else actual.tipo_escalado
        nueva_cantidad = self._resolver_cantidad(actual, tipo, cantidad, unidad)

        reemplazo = IngredientePreparacion(
            ingrediente_id=actual.ingrediente_id,
            tipo_escalado=tipo,
            cantidad=nueva_cantidad,
            observacion=(
                actual.observacion if observacion is None else observacion
            ),
            id=actual.id,
        )
        posicion = preparacion.ingredientes.index(actual)
        preparacion.ingredientes[posicion] = reemplazo
        self._guardar(receta)

    def quitar(
        self,
        solicitante_id: UUID,
        receta_id: UUID,
        preparacion_id: UUID,
        ingrediente_preparacion_id: UUID,
    ) -> None:
        """Elimina un ingrediente de la Preparacion (RF-018)."""
        receta = self._preparar(solicitante_id, receta_id)
        preparacion = receta.obtener_preparacion(preparacion_id)
        preparacion.quitar_ingrediente(ingrediente_preparacion_id)
        self._guardar(receta)

    def _resolver_cantidad(
        self,
        actual: IngredientePreparacion,
        tipo: TipoEscalado,
        cantidad: Decimal | None,
        unidad: str | None,
    ) -> Cantidad | None:
        """Calcula la Cantidad resultante segun el TipoEscalado destino."""
        if not tipo.admite_cantidad:
            return None
        if cantidad is None and unidad is None:
            return actual.cantidad
        valor = cantidad if cantidad is not None else (
            actual.cantidad.valor if actual.cantidad else None
        )
        simbolo = unidad or (
            actual.cantidad.unidad.simbolo if actual.cantidad else None
        )
        if valor is None or simbolo is None:
            return None
        return Cantidad(valor, Unidad.desde_simbolo(simbolo))

    def _construir(self, datos: DatosIngrediente) -> IngredientePreparacion:
        """Arma un IngredientePreparacion a partir de tipos primitivos."""
        cantidad = None
        if datos.cantidad is not None and datos.unidad is not None:
            cantidad = Cantidad(datos.cantidad, Unidad.desde_simbolo(datos.unidad))
        return IngredientePreparacion(
            ingrediente_id=datos.ingrediente_id,
            tipo_escalado=TipoEscalado(datos.tipo_escalado),
            cantidad=cantidad,
            observacion=datos.observacion,
        )

    def _asegurar_ingrediente_existente(self, ingrediente_id: UUID) -> None:
        """El ingrediente debe pertenecer al catalogo (Capitulo 3.6)."""
        if self.uow.ingredientes.obtener(ingrediente_id) is None:
            raise RecursoNoEncontrado("Ingrediente", ingrediente_id)

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


class GestionarPasos(CasoDeUso):
    """CU-010: pasos de una Preparacion (RF-019 a RF-022)."""

    def agregar(
        self,
        solicitante_id: UUID,
        receta_id: UUID,
        preparacion_id: UUID,
        descripcion: str,
    ) -> UUID:
        """Agrega un paso al final de la secuencia (RF-019)."""
        receta = self._preparar(solicitante_id, receta_id)
        paso = receta.obtener_preparacion(preparacion_id).agregar_paso(descripcion)
        self._guardar(receta)
        return paso.id

    def modificar(
        self,
        solicitante_id: UUID,
        receta_id: UUID,
        preparacion_id: UUID,
        paso_id: UUID,
        descripcion: str,
    ) -> None:
        """Cambia la descripcion de un paso (RF-020)."""
        receta = self._preparar(solicitante_id, receta_id)
        preparacion = receta.obtener_preparacion(preparacion_id)
        paso = next((p for p in preparacion.pasos if p.id == paso_id), None)
        if paso is None:
            raise RecursoNoEncontrado("Paso", paso_id)
        limpia = descripcion.strip()
        if limpia:
            paso.descripcion = limpia
        self._guardar(receta)

    def eliminar(
        self,
        solicitante_id: UUID,
        receta_id: UUID,
        preparacion_id: UUID,
        paso_id: UUID,
    ) -> None:
        """Elimina un paso y renumera los restantes (RF-021)."""
        receta = self._preparar(solicitante_id, receta_id)
        receta.obtener_preparacion(preparacion_id).quitar_paso(paso_id)
        self._guardar(receta)

    def reordenar(
        self,
        solicitante_id: UUID,
        receta_id: UUID,
        preparacion_id: UUID,
        ids_en_orden: list[UUID],
    ) -> None:
        """Reordena los pasos de la Preparacion (RF-022)."""
        receta = self._preparar(solicitante_id, receta_id)
        receta.obtener_preparacion(preparacion_id).reordenar_pasos(ids_en_orden)
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


class GestionarFotografias(CasoDeUso):
    """CU-011: fotografias de una Receta (RF-023 y RF-024).

    El limite de RN-005 lo aplica la Receta, que conoce todas sus
    Preparaciones.
    """

    def agregar(
        self,
        solicitante_id: UUID,
        receta_id: UUID,
        preparacion_id: UUID,
        ruta: str,
        tipo: str = "proceso",
        descripcion: str = "",
    ) -> UUID:
        """Agrega una fotografia respetando el maximo permitido (RF-023)."""
        receta = self._preparar(solicitante_id, receta_id)
        fotografia = Fotografia(
            ruta=ruta, tipo=TipoFotografia(tipo), descripcion=descripcion
        )
        receta.agregar_fotografia(preparacion_id, fotografia)
        self._guardar(receta)
        return fotografia.id

    def eliminar(
        self,
        solicitante_id: UUID,
        receta_id: UUID,
        preparacion_id: UUID,
        fotografia_id: UUID,
    ) -> None:
        """Elimina una fotografia (RF-024)."""
        receta = self._preparar(solicitante_id, receta_id)
        receta.quitar_fotografia(preparacion_id, fotografia_id)
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


class GestionarNotas(CasoDeUso):
    """CU-012: notas permanentes de una Receta (RF-025 y RF-026)."""

    def agregar(self, solicitante_id: UUID, receta_id: UUID, texto: str) -> UUID:
        """Registra una nota firmada por el solicitante (RF-025)."""
        usuario = self._obtener_usuario(solicitante_id)
        self.autorizacion.asegurar_puede_gestionar_recetas(usuario)
        receta = self._obtener_receta(receta_id)
        nota = Nota(texto=texto, autor_id=usuario.id)
        receta.agregar_nota(nota)
        self._guardar(receta)
        return nota.id

    def editar(
        self, solicitante_id: UUID, receta_id: UUID, nota_id: UUID, texto: str
    ) -> None:
        """Modifica el contenido de una nota (RF-026)."""
        receta = self._preparar(solicitante_id, receta_id)
        nota = next((n for n in receta.notas if n.id == nota_id), None)
        if nota is None:
            raise RecursoNoEncontrado("Nota", nota_id)
        nota.editar(texto)
        self._guardar(receta)

    def eliminar(
        self, solicitante_id: UUID, receta_id: UUID, nota_id: UUID
    ) -> None:
        """Elimina una nota de la receta (RF-026)."""
        receta = self._preparar(solicitante_id, receta_id)
        receta.quitar_nota(nota_id)
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
