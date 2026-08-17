"""Casos de Uso de Importacion de Recetas (Cap. 7.7, version 2.0).

Ninguno persiste una Receta: devuelven un borrador para que la persona lo
revise antes de guardarlo con CrearReceta, que es quien realmente valida y
persiste (Capitulo 5.3: la Presentacion nunca toca el agregado
directamente, y el borrador tampoco es una excepcion a esa regla).
"""

from __future__ import annotations

from uuid import UUID

from ...dominio.excepciones import ValorInvalido
from ..dto import IngredienteImportado, PreparacionImportada, RecetaImportada
from ..servicios_externos import AsistenteEstructuracion, ExtractorTexto
from .base import CasoDeUso


class ImportarRecetaDesdeArchivo(CasoDeUso):
    """CU-026: extrae un borrador de Receta a partir de un archivo.

    No sabe si el archivo es un PDF, una foto o cualquier otra cosa: recibe
    un ExtractorTexto y un AsistenteEstructuracion ya elegidos por quien lo
    invoca (Cap. 7.7 - PDF usa pdfplumber y la API de Claude; foto usa una
    API de OCR gratuita y reglas simples, sin IA, para no generar costo).

    La extraccion nunca es perfecta -una cantidad mal leida, un ingrediente
    que no coincide con el catalogo- asi que el resultado se muestra para
    que la persona lo corrija antes de guardarlo. Cualquier usuario activo
    puede importar, igual que puede crear una Receta desde el formulario
    (decision D-20: crear es libre, editar es del Administrador; importar
    es una forma de crear).
    """

    def __init__(
        self,
        unidad_de_trabajo,
        autorizacion=None,
        extractor_texto: ExtractorTexto | None = None,
        asistente_ia: AsistenteEstructuracion | None = None,
    ) -> None:
        super().__init__(unidad_de_trabajo, autorizacion)
        self._extractor_texto = extractor_texto
        self._asistente_ia = asistente_ia

    def ejecutar(self, solicitante_id: UUID, contenido: bytes) -> RecetaImportada:
        """Extrae el texto del archivo y le pide al asistente que lo estructure."""
        usuario = self._obtener_usuario(solicitante_id)
        self.autorizacion.asegurar_activo(usuario)

        texto = self._extractor_texto.extraer(contenido)
        if not texto.strip():
            raise ValorInvalido(
                "No se pudo leer texto de este archivo. Probá con una "
                "imagen más nítida o con otro método de importación."
            )

        nombres_catalogo = [i.nombre for i in self.uow.ingredientes.listar_todos()]
        borrador = self._asistente_ia.estructurar_receta(texto, nombres_catalogo)
        return self._resolver_ingredientes(borrador)

    def _resolver_ingredientes(self, borrador: RecetaImportada) -> RecetaImportada:
        """Busca en el catalogo una coincidencia para cada ingrediente extraido.

        La IA trabaja solo con nombres de texto: no conoce las identidades
        del catalogo. Esta busqueda es lo que le permite al formulario
        preseleccionar el ingrediente correcto en lugar de dejarlo todo
        para crear de nuevo.
        """
        preparaciones_resueltas = tuple(
            PreparacionImportada(
                nombre=preparacion.nombre,
                ingredientes=tuple(
                    self._resolver_ingrediente(ingrediente)
                    for ingrediente in preparacion.ingredientes
                ),
                pasos=preparacion.pasos,
            )
            for preparacion in borrador.preparaciones
        )
        return RecetaImportada(
            nombre=borrador.nombre,
            descripcion=borrador.descripcion,
            rendimiento_base=borrador.rendimiento_base,
            rendimiento_descripcion=borrador.rendimiento_descripcion,
            fuente_sugerida=borrador.fuente_sugerida,
            preparaciones=preparaciones_resueltas,
            advertencia=borrador.advertencia,
        )

    def _resolver_ingrediente(
        self, ingrediente: IngredienteImportado
    ) -> IngredienteImportado:
        """Completa `ingrediente_id` si el texto coincide con el catalogo."""
        if ingrediente.ingrediente_id is not None:
            return ingrediente
        coincidencias = self.uow.ingredientes.buscar_por_nombre(ingrediente.texto)
        coincidencia_exacta = next(
            (
                i
                for i in coincidencias
                if i.nombre.strip().lower() == ingrediente.texto.strip().lower()
            ),
            None,
        )
        objetivo = coincidencia_exacta or (coincidencias[0] if coincidencias else None)
        if objetivo is None:
            return ingrediente
        return IngredienteImportado(
            texto=ingrediente.texto,
            ingrediente_id=objetivo.id,
            cantidad=ingrediente.cantidad,
            unidad=ingrediente.unidad,
            tipo_escalado=ingrediente.tipo_escalado,
            observacion=ingrediente.observacion,
        )
