"""Vistas de Recetas y sus componentes.

Cada vista hace lo mismo: valida la forma de la entrada, arma el Comando,
invoca el Caso de Uso y serializa el resultado. No contiene reglas de
negocio (Capitulo 5.3).

Las excepciones no se capturan aqui: el manejador configurado en
`soporte.manejar_excepciones` las traduce a codigos HTTP.
"""

from __future__ import annotations

from rest_framework.views import APIView

from ...aplicacion.casos_uso import (
    ArchivarReceta,
    AsignarClasificacion,
    BuscarRecetas,
    ConsultarReceta,
    CrearReceta,
    DuplicarReceta,
    EditarReceta,
    EscalarReceta,
    GenerarListaCompras,
    GestionarFotografias,
    GestionarIngredientesDePreparacion,
    GestionarNotas,
    GestionarPasos,
    GestionarPreparaciones,
    ListarListasCompras,
    ListarRecetas,
    MarcarFavorita,
    MarcarItemComprado,
    QuitarItemDeLista,
    RestaurarReceta,
)
from ...aplicacion.dto import (
    ComandoBuscarRecetas,
    ComandoCrearReceta,
    ComandoEditarReceta,
    ComandoEscalarReceta,
    ComandoGenerarListaCompras,
    DatosIngrediente,
    DatosPreparacion,
)
from ...infraestructura.persistencia import UnidadDeTrabajoDjango
from . import serializadores as s
from .soporte import correcto, creado


class VistaBase(APIView):
    """Base de las vistas de la API.

    Construye la Unidad de Trabajo y expone la identidad del solicitante,
    que llega del token JWT ya verificado por DRF.
    """

    @property
    def uow(self) -> UnidadDeTrabajoDjango:
        """Unidad de Trabajo para esta peticion."""
        return UnidadDeTrabajoDjango()

    @property
    def solicitante_id(self):
        """Identidad del usuario autenticado."""
        return self.request.user.id

    def validar(self, serializador_clase):
        """Valida el cuerpo de la peticion y devuelve los datos limpios."""
        serializador = serializador_clase(data=self.request.data)
        serializador.is_valid(raise_exception=True)
        return serializador.validated_data


def _a_datos_preparacion(entrada) -> DatosPreparacion:
    """Traduce una preparacion validada al DTO de la Aplicacion."""
    return DatosPreparacion(
        nombre=entrada["nombre"],
        ingredientes=tuple(
            DatosIngrediente(
                ingrediente_id=i["ingrediente_id"],
                tipo_escalado=i.get("tipo_escalado", "lineal"),
                cantidad=i.get("cantidad"),
                unidad=i.get("unidad"),
                observacion=i.get("observacion", ""),
            )
            for i in entrada.get("ingredientes", [])
        ),
        pasos=tuple(entrada.get("pasos", [])),
    )


class RecetasVista(VistaBase):
    """Coleccion de Recetas: listar, buscar y crear."""

    def get(self, peticion):
        """Lista o busca recetas segun los parametros recibidos (RF-038 a RF-043)."""
        parametros = peticion.query_params
        criterios_presentes = any(
            parametros.get(clave)
            for clave in (
                "texto",
                "ingrediente_id",
                "categoria_id",
                "etiqueta_id",
                "fuente_id",
                "solo_favoritas",
            )
        )

        if not criterios_presentes:
            resultados = ListarRecetas(self.uow).ejecutar(
                self.solicitante_id,
                incluir_archivadas=parametros.get("incluir_archivadas") == "true",
            )
        else:
            comando = ComandoBuscarRecetas(
                solicitante_id=self.solicitante_id,
                texto=parametros.get("texto") or None,
                ingrediente_id=parametros.get("ingrediente_id") or None,
                categoria_id=parametros.get("categoria_id") or None,
                etiqueta_id=parametros.get("etiqueta_id") or None,
                fuente_id=parametros.get("fuente_id") or None,
                solo_favoritas=parametros.get("solo_favoritas") == "true",
                incluir_archivadas=parametros.get("incluir_archivadas") == "true",
            )
            resultados = BuscarRecetas(self.uow).ejecutar(comando)

        return correcto(resultados)

    def post(self, peticion):
        """Crea una Receta (RF-005)."""
        datos = self.validar(s.CrearRecetaEntrada)
        comando = ComandoCrearReceta(
            solicitante_id=self.solicitante_id,
            nombre=datos["nombre"],
            descripcion=datos.get("descripcion", ""),
            rendimiento_base=datos["rendimiento_base"],
            rendimiento_descripcion=datos.get("rendimiento_descripcion", "porciones"),
            fuente_id=datos["fuente_id"],
            preparaciones=tuple(
                _a_datos_preparacion(p) for p in datos.get("preparaciones", [])
            ),
            categorias_ids=tuple(datos.get("categorias_ids", [])),
            etiquetas_ids=tuple(datos.get("etiquetas_ids", [])),
        )
        return creado(CrearReceta(self.uow).ejecutar(comando))


class RecetaVista(VistaBase):
    """Receta individual: consultar y editar."""

    def get(self, peticion, receta_id):
        """Devuelve la receta completa (RF-007)."""
        return correcto(
            ConsultarReceta(self.uow).ejecutar(self.solicitante_id, receta_id)
        )

    def patch(self, peticion, receta_id):
        """Edita los datos generales (RF-006)."""
        datos = self.validar(s.EditarRecetaEntrada)
        comando = ComandoEditarReceta(
            solicitante_id=self.solicitante_id,
            receta_id=receta_id,
            nombre=datos.get("nombre"),
            descripcion=datos.get("descripcion"),
            rendimiento_base=datos.get("rendimiento_base"),
            rendimiento_descripcion=datos.get("rendimiento_descripcion"),
            fuente_id=datos.get("fuente_id"),
        )
        return correcto(EditarReceta(self.uow).ejecutar(comando))


class ArchivarVista(VistaBase):
    """Archivado y restauracion (RF-008 y RF-009)."""

    def post(self, peticion, receta_id):
        """Archiva la receta."""
        ArchivarReceta(self.uow).ejecutar(self.solicitante_id, receta_id)
        return correcto()

    def delete(self, peticion, receta_id):
        """Restaura la receta archivada."""
        RestaurarReceta(self.uow).ejecutar(self.solicitante_id, receta_id)
        return correcto()


class DuplicarVista(VistaBase):
    """Creacion de variantes (RF-010)."""

    def post(self, peticion, receta_id):
        """Duplica la receta bajo un nombre nuevo."""
        datos = self.validar(s.DuplicarEntrada)
        return creado(
            DuplicarReceta(self.uow).ejecutar(
                self.solicitante_id, receta_id, datos["nombre"]
            )
        )


class FavoritaVista(VistaBase):
    """Marcado de favoritas (RF-043)."""

    def post(self, peticion, receta_id):
        """Marca o desmarca la receta."""
        datos = self.validar(s.FavoritaEntrada)
        MarcarFavorita(self.uow).ejecutar(
            self.solicitante_id, receta_id, datos["favorita"]
        )
        return correcto()


class EscalarVista(VistaBase):
    """Escalado de una Receta (RF-031 a RF-033).

    Es una operacion de solo lectura: no persiste absolutamente nada
    (ADR-003). Usa POST porque recibe un cuerpo con el rendimiento
    solicitado.
    """

    def post(self, peticion, receta_id):
        """Devuelve la receta escalada sin modificar la almacenada."""
        datos = self.validar(s.EscalarEntrada)
        comando = ComandoEscalarReceta(
            solicitante_id=self.solicitante_id,
            receta_id=receta_id,
            rendimiento_objetivo=datos["rendimiento_objetivo"],
            rendimiento_descripcion=datos.get("rendimiento_descripcion"),
        )
        return correcto(EscalarReceta(self.uow).ejecutar(comando))


class ListaComprasVista(VistaBase):
    """Generacion de la Lista de Compras (RF-034 y RF-035)."""

    def post(self, peticion, receta_id):
        """Consolida los ingredientes marcados como faltantes."""
        datos = self.validar(s.ListaComprasEntrada)
        comando = ComandoGenerarListaCompras(
            solicitante_id=self.solicitante_id,
            receta_id=receta_id,
            ingredientes_seleccionados=tuple(datos["ingredientes_seleccionados"]),
            rendimiento_objetivo=datos.get("rendimiento_objetivo"),
            rendimiento_descripcion=datos.get("rendimiento_descripcion"),
            persistir=datos.get("persistir", False),
        )
        return correcto(GenerarListaCompras(self.uow).ejecutar(comando))


class PreparacionesVista(VistaBase):
    """Coleccion de Preparaciones de una Receta (RF-011)."""

    def post(self, peticion, receta_id):
        """Agrega una Preparacion."""
        datos = self.validar(s.PreparacionEntrada)
        identidad = GestionarPreparaciones(self.uow).agregar(
            self.solicitante_id, receta_id, _a_datos_preparacion(datos)
        )
        return creado({"id": identidad})


class PreparacionVista(VistaBase):
    """Preparacion individual (RF-012 y RF-013)."""

    def patch(self, peticion, receta_id, preparacion_id):
        """Renombra la Preparacion."""
        datos = self.validar(s.NombreEntrada)
        GestionarPreparaciones(self.uow).renombrar(
            self.solicitante_id, receta_id, preparacion_id, datos["nombre"]
        )
        return correcto()

    def delete(self, peticion, receta_id, preparacion_id):
        """Elimina la Preparacion respetando RN-003."""
        GestionarPreparaciones(self.uow).eliminar(
            self.solicitante_id, receta_id, preparacion_id
        )
        return correcto()


class ReordenarPreparacionesVista(VistaBase):
    """Reordenamiento de Preparaciones (RF-014)."""

    def post(self, peticion, receta_id):
        """Aplica el nuevo orden."""
        datos = self.validar(s.ReordenarEntrada)
        GestionarPreparaciones(self.uow).reordenar(
            self.solicitante_id, receta_id, list(datos["ids_en_orden"])
        )
        return correcto()


class IngredientesPreparacionVista(VistaBase):
    """Ingredientes de una Preparacion (RF-016)."""

    def post(self, peticion, receta_id, preparacion_id):
        """Agrega un ingrediente."""
        datos = self.validar(s.IngredienteEntrada)
        identidad = GestionarIngredientesDePreparacion(self.uow).agregar(
            self.solicitante_id,
            receta_id,
            preparacion_id,
            DatosIngrediente(
                ingrediente_id=datos["ingrediente_id"],
                tipo_escalado=datos.get("tipo_escalado", "lineal"),
                cantidad=datos.get("cantidad"),
                unidad=datos.get("unidad"),
                observacion=datos.get("observacion", ""),
            ),
        )
        return creado({"id": identidad})


class IngredientePreparacionVista(VistaBase):
    """Ingrediente individual de una Preparacion (RF-017 y RF-018)."""

    def patch(self, peticion, receta_id, preparacion_id, ingrediente_id):
        """Modifica cantidad, unidad, tipo de escalado u observacion."""
        datos = self.validar(s.ModificarIngredienteEntrada)
        GestionarIngredientesDePreparacion(self.uow).modificar(
            self.solicitante_id,
            receta_id,
            preparacion_id,
            ingrediente_id,
            cantidad=datos.get("cantidad"),
            unidad=datos.get("unidad"),
            tipo_escalado=datos.get("tipo_escalado"),
            observacion=datos.get("observacion"),
        )
        return correcto()

    def delete(self, peticion, receta_id, preparacion_id, ingrediente_id):
        """Quita el ingrediente de la Preparacion."""
        GestionarIngredientesDePreparacion(self.uow).quitar(
            self.solicitante_id, receta_id, preparacion_id, ingrediente_id
        )
        return correcto()


class PasosVista(VistaBase):
    """Pasos de una Preparacion (RF-019)."""

    def post(self, peticion, receta_id, preparacion_id):
        """Agrega un paso al final de la secuencia."""
        datos = self.validar(s.PasoEntrada)
        identidad = GestionarPasos(self.uow).agregar(
            self.solicitante_id, receta_id, preparacion_id, datos["descripcion"]
        )
        return creado({"id": identidad})


class PasoVista(VistaBase):
    """Paso individual (RF-020 y RF-021)."""

    def patch(self, peticion, receta_id, preparacion_id, paso_id):
        """Modifica la descripcion del paso."""
        datos = self.validar(s.PasoEntrada)
        GestionarPasos(self.uow).modificar(
            self.solicitante_id,
            receta_id,
            preparacion_id,
            paso_id,
            datos["descripcion"],
        )
        return correcto()

    def delete(self, peticion, receta_id, preparacion_id, paso_id):
        """Elimina el paso y renumera los restantes."""
        GestionarPasos(self.uow).eliminar(
            self.solicitante_id, receta_id, preparacion_id, paso_id
        )
        return correcto()


class ReordenarPasosVista(VistaBase):
    """Reordenamiento de pasos (RF-022)."""

    def post(self, peticion, receta_id, preparacion_id):
        """Aplica el nuevo orden."""
        datos = self.validar(s.ReordenarEntrada)
        GestionarPasos(self.uow).reordenar(
            self.solicitante_id,
            receta_id,
            preparacion_id,
            list(datos["ids_en_orden"]),
        )
        return correcto()


class FotografiasVista(VistaBase):
    """Fotografias de una Receta (RF-023).

    El limite de RN-005 lo aplica el Dominio; si se supera, la respuesta
    es 422 con el codigo de la regla.
    """

    def post(self, peticion, receta_id, preparacion_id):
        """Agrega una fotografia."""
        datos = self.validar(s.FotografiaEntrada)
        identidad = GestionarFotografias(self.uow).agregar(
            self.solicitante_id,
            receta_id,
            preparacion_id,
            ruta=datos["ruta"],
            tipo=datos.get("tipo", "proceso"),
            descripcion=datos.get("descripcion", ""),
        )
        return creado({"id": identidad})


class FotografiaVista(VistaBase):
    """Fotografia individual (RF-024)."""

    def delete(self, peticion, receta_id, preparacion_id, fotografia_id):
        """Elimina la fotografia."""
        GestionarFotografias(self.uow).eliminar(
            self.solicitante_id, receta_id, preparacion_id, fotografia_id
        )
        return correcto()


class NotasVista(VistaBase):
    """Notas de una Receta (RF-025)."""

    def post(self, peticion, receta_id):
        """Registra una nota."""
        datos = self.validar(s.NotaEntrada)
        identidad = GestionarNotas(self.uow).agregar(
            self.solicitante_id, receta_id, datos["texto"]
        )
        return creado({"id": identidad})


class NotaVista(VistaBase):
    """Nota individual (RF-026)."""

    def patch(self, peticion, receta_id, nota_id):
        """Edita el texto de la nota."""
        datos = self.validar(s.NotaEntrada)
        GestionarNotas(self.uow).editar(
            self.solicitante_id, receta_id, nota_id, datos["texto"]
        )
        return correcto()

    def delete(self, peticion, receta_id, nota_id):
        """Elimina la nota."""
        GestionarNotas(self.uow).eliminar(self.solicitante_id, receta_id, nota_id)
        return correcto()


class ClasificacionVista(VistaBase):
    """Asignacion de categorias y etiquetas (RF-027 y RF-028)."""

    def post(self, peticion, receta_id, tipo, elemento_id):
        """Asocia una categoria o etiqueta a la receta."""
        caso = AsignarClasificacion(self.uow)
        if tipo == "categorias":
            caso.asignar_categoria(self.solicitante_id, receta_id, elemento_id)
        else:
            caso.asignar_etiqueta(self.solicitante_id, receta_id, elemento_id)
        return correcto()

    def delete(self, peticion, receta_id, tipo, elemento_id):
        """Desasocia una categoria o etiqueta de la receta."""
        caso = AsignarClasificacion(self.uow)
        if tipo == "categorias":
            caso.quitar_categoria(self.solicitante_id, receta_id, elemento_id)
        else:
            caso.quitar_etiqueta(self.solicitante_id, receta_id, elemento_id)
        return correcto()


class ListasComprasVista(VistaBase):
    """Listas de Compras guardadas del usuario autenticado."""

    def get(self, peticion):
        """Devuelve las listas propias, no las de otros integrantes."""
        return correcto(ListarListasCompras(self.uow).ejecutar(self.solicitante_id))


class ItemCompraVista(VistaBase):
    """Item individual de una Lista de Compras (RF-036 y RF-037)."""

    def patch(self, peticion, lista_id, item_id):
        """Marca o desmarca el item como comprado."""
        datos = self.validar(s.ItemCompraEntrada)
        MarcarItemComprado(self.uow).ejecutar(
            self.solicitante_id, lista_id, item_id, datos.get("comprado", True)
        )
        return correcto()

    def delete(self, peticion, lista_id, item_id):
        """Saca el producto de la lista."""
        QuitarItemDeLista(self.uow).ejecutar(self.solicitante_id, lista_id, item_id)
        return correcto()
