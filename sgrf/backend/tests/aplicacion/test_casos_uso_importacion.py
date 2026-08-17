"""Pruebas de integracion del Caso de Uso de Importacion de Recetas (v2.0).

Usa dobles de prueba para ExtractorTexto y AsistenteEstructuracion: nunca
llama a la API real de Claude ni abre un PDF de verdad. Es el mismo patron
que los repositorios en memoria de las demas pruebas de aplicacion.
"""

from decimal import Decimal
from uuid import uuid4

import pytest

from sgrf.aplicacion.casos_uso import ImportarRecetaDesdeArchivo
from sgrf.aplicacion.dto import IngredienteImportado, PreparacionImportada, RecetaImportada
from sgrf.aplicacion.excepciones import RecursoNoEncontrado, UsuarioInactivo
from sgrf.aplicacion.servicios_externos import (
    AsistenteEstructuracion,
    ExtractorTexto,
    ServicioNoDisponible,
)
from sgrf.dominio.excepciones import ValorInvalido


class ExtractorFalso(ExtractorTexto):
    """Devuelve un texto fijo, sin abrir ningun archivo de verdad."""

    def __init__(self, texto: str = "Texto de una receta cualquiera.") -> None:
        self.texto = texto
        self.ultimo_contenido_recibido: bytes | None = None
        self.ultimo_nombre_recibido: str | None = None

    def extraer(self, contenido: bytes, nombre_archivo: str = "archivo") -> str:
        self.ultimo_contenido_recibido = contenido
        self.ultimo_nombre_recibido = nombre_archivo
        return self.texto


class AsistenteFalso(AsistenteEstructuracion):
    """Devuelve un borrador fijo, sin llamar a ninguna API de verdad."""

    def __init__(self, borrador: RecetaImportada | None = None) -> None:
        self.borrador = borrador or self._borrador_por_defecto()
        self.ultimo_texto_recibido: str | None = None
        self.ultimo_catalogo_recibido: list[str] | None = None

    def estructurar_receta(
        self, texto: str, nombres_ingredientes_catalogo: list[str]
    ) -> RecetaImportada:
        self.ultimo_texto_recibido = texto
        self.ultimo_catalogo_recibido = nombres_ingredientes_catalogo
        return self.borrador

    @staticmethod
    def _borrador_por_defecto() -> RecetaImportada:
        return RecetaImportada(
            nombre="Pan casero",
            descripcion="Receta de un cuaderno familiar.",
            rendimiento_base=Decimal("4"),
            rendimiento_descripcion="porciones",
            fuente_sugerida="Cuaderno familiar",
            preparaciones=(
                PreparacionImportada(
                    nombre="Masa",
                    ingredientes=(
                        IngredienteImportado(
                            texto="Harina 000",
                            ingrediente_id=None,
                            cantidad=Decimal("500"),
                            unidad="g",
                            tipo_escalado="lineal",
                        ),
                        IngredienteImportado(
                            texto="Sal",
                            ingrediente_id=None,
                            cantidad=None,
                            unidad=None,
                            tipo_escalado="a_gusto",
                        ),
                    ),
                    pasos=("Mezclar.", "Amasar."),
                ),
            ),
        )


class TestImportarRecetaDesdeArchivo:
    """CU-026: extraccion de un borrador, sin persistir nada."""

    def test_devuelve_un_borrador_con_los_datos_de_la_ia(self, uow, familiar):
        caso_de_uso = ImportarRecetaDesdeArchivo(
            uow,
            extractor_texto=ExtractorFalso(),
            asistente_ia=AsistenteFalso(),
        )
        borrador = caso_de_uso.ejecutar(familiar.id, b"contenido-pdf-falso")
        assert borrador.nombre == "Pan casero"
        assert len(borrador.preparaciones) == 1
        assert len(borrador.preparaciones[0].ingredientes) == 2

    def test_le_pasa_el_nombre_real_del_archivo_al_extractor(self, uow, familiar):
        """Bug reportado: OCR.space rechazaba fotos que no eran JPEG porque
        el nombre de archivo quedaba hardcodeado como 'receta.jpg' sin
        importar el formato real. El nombre real tiene que llegar entero
        hasta el extractor, que es quien lo necesita para inferir el
        formato de la imagen.
        """
        extractor = ExtractorFalso()
        caso_de_uso = ImportarRecetaDesdeArchivo(
            uow,
            extractor_texto=extractor,
            asistente_ia=AsistenteFalso(),
        )
        caso_de_uso.ejecutar(familiar.id, b"contenido-png-falso", "mi_receta.png")
        assert extractor.ultimo_nombre_recibido == "mi_receta.png"

    def test_no_persiste_ninguna_receta(self, uow, familiar):
        caso_de_uso = ImportarRecetaDesdeArchivo(
            uow,
            extractor_texto=ExtractorFalso(),
            asistente_ia=AsistenteFalso(),
        )
        caso_de_uso.ejecutar(familiar.id, b"contenido-pdf-falso")
        assert uow.recetas.listar_todas() == []
        assert uow.confirmaciones == 0

    def test_hace_coincidir_ingredientes_del_catalogo_por_nombre(
        self, uow, familiar, harina
    ):
        """El ingrediente 'Harina 000' del borrador debe encontrar el del catalogo."""
        caso_de_uso = ImportarRecetaDesdeArchivo(
            uow,
            extractor_texto=ExtractorFalso(),
            asistente_ia=AsistenteFalso(),
        )
        borrador = caso_de_uso.ejecutar(familiar.id, b"contenido-pdf-falso")
        harina_importada = borrador.preparaciones[0].ingredientes[0]
        assert harina_importada.ingrediente_id == harina.id

    def test_ingrediente_sin_coincidencia_queda_sin_id(self, uow, familiar, harina):
        """'Sal' no esta en el catalogo de prueba: debe quedar sin coincidencia."""
        caso_de_uso = ImportarRecetaDesdeArchivo(
            uow,
            extractor_texto=ExtractorFalso(),
            asistente_ia=AsistenteFalso(),
        )
        borrador = caso_de_uso.ejecutar(familiar.id, b"contenido-pdf-falso")
        sal_importada = borrador.preparaciones[0].ingredientes[1]
        assert sal_importada.ingrediente_id is None
        assert sal_importada.texto == "Sal"

    def test_le_pasa_los_nombres_del_catalogo_al_asistente(
        self, uow, familiar, harina, sal
    ):
        """El asistente debe recibir el catalogo para preferir nombres existentes."""
        asistente = AsistenteFalso()
        caso_de_uso = ImportarRecetaDesdeArchivo(
            uow, extractor_texto=ExtractorFalso(), asistente_ia=asistente
        )
        caso_de_uso.ejecutar(familiar.id, b"contenido-pdf-falso")
        assert harina.nombre in asistente.ultimo_catalogo_recibido
        assert sal.nombre in asistente.ultimo_catalogo_recibido

    def test_archivo_sin_texto_falla_con_mensaje_claro(self, uow, familiar):
        caso_de_uso = ImportarRecetaDesdeArchivo(
            uow,
            extractor_texto=ExtractorFalso(texto="   "),
            asistente_ia=AsistenteFalso(),
        )
        with pytest.raises(ValorInvalido, match="No se pudo leer texto"):
            caso_de_uso.ejecutar(familiar.id, b"contenido-pdf-falso")

    def test_usuario_inactivo_no_puede_importar(self, uow, familiar_inactivo):
        caso_de_uso = ImportarRecetaDesdeArchivo(
            uow,
            extractor_texto=ExtractorFalso(),
            asistente_ia=AsistenteFalso(),
        )
        with pytest.raises(UsuarioInactivo):
            caso_de_uso.ejecutar(familiar_inactivo.id, b"contenido-pdf-falso")

    def test_solicitante_inexistente_falla(self, uow):
        caso_de_uso = ImportarRecetaDesdeArchivo(
            uow,
            extractor_texto=ExtractorFalso(),
            asistente_ia=AsistenteFalso(),
        )
        with pytest.raises(RecursoNoEncontrado):
            caso_de_uso.ejecutar(uuid4(), b"contenido-pdf-falso")

    def test_conserva_la_advertencia_del_asistente(self, uow, familiar):
        borrador_con_advertencia = RecetaImportada(
            nombre="Receta dudosa",
            descripcion="",
            rendimiento_base=Decimal("4"),
            rendimiento_descripcion="porciones",
            fuente_sugerida="",
            preparaciones=(),
            advertencia="No se pudo determinar el rendimiento con confianza.",
        )
        caso_de_uso = ImportarRecetaDesdeArchivo(
            uow,
            extractor_texto=ExtractorFalso(),
            asistente_ia=AsistenteFalso(borrador_con_advertencia),
        )
        borrador = caso_de_uso.ejecutar(familiar.id, b"contenido-pdf-falso")
        assert borrador.advertencia == "No se pudo determinar el rendimiento con confianza."

    def test_propaga_error_del_servicio_externo(self, uow, familiar):
        """Si el asistente de IA falla, el error no debe quedar oculto."""

        class AsistenteQueFalla(AsistenteEstructuracion):
            def estructurar_receta(self, texto, nombres_ingredientes_catalogo):
                raise ServicioNoDisponible("La API no respondió.")

        caso_de_uso = ImportarRecetaDesdeArchivo(
            uow,
            extractor_texto=ExtractorFalso(),
            asistente_ia=AsistenteQueFalla(),
        )
        with pytest.raises(ServicioNoDisponible):
            caso_de_uso.ejecutar(familiar.id, b"contenido-pdf-falso")
