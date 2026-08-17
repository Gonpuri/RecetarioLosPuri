"""Serializadores de entrada.

Validan la forma de los datos que llegan por HTTP (tipos, obligatoriedad,
longitudes). Las reglas del negocio no se validan aqui: eso corresponde al
Dominio. Esta capa solo garantiza que el Caso de Uso reciba un comando bien
formado.
"""

from __future__ import annotations

from rest_framework import serializers

TIPOS_ESCALADO = ["lineal", "fijo", "a_gusto", "cantidad_necesaria"]
UNIDADES = ["g", "kg", "ml", "l", "cda", "cdita", "taza", "pizca", "u"]
TIPOS_FOTOGRAFIA = ["proceso", "final"]


class IngredienteEntrada(serializers.Serializer):
    """Ingrediente de una Preparacion."""

    ingrediente_id = serializers.UUIDField()
    tipo_escalado = serializers.ChoiceField(
        choices=TIPOS_ESCALADO, default="lineal"
    )
    cantidad = serializers.DecimalField(
        max_digits=12, decimal_places=3, required=False, allow_null=True
    )
    unidad = serializers.ChoiceField(
        choices=UNIDADES, required=False, allow_null=True
    )
    observacion = serializers.CharField(
        max_length=250, required=False, allow_blank=True, default=""
    )


class PreparacionEntrada(serializers.Serializer):
    """Preparacion completa."""

    nombre = serializers.CharField(max_length=150)
    ingredientes = IngredienteEntrada(many=True, required=False, default=list)
    pasos = serializers.ListField(
        child=serializers.CharField(), required=False, default=list
    )


class CrearRecetaEntrada(serializers.Serializer):
    """Alta de una Receta (RF-005)."""

    nombre = serializers.CharField(max_length=200)
    descripcion = serializers.CharField(
        required=False, allow_blank=True, default=""
    )
    rendimiento_base = serializers.DecimalField(max_digits=10, decimal_places=3)
    rendimiento_descripcion = serializers.CharField(
        max_length=50, required=False, default="porciones"
    )
    fuente_id = serializers.UUIDField()
    preparaciones = PreparacionEntrada(many=True, required=False, default=list)
    categorias_ids = serializers.ListField(
        child=serializers.UUIDField(), required=False, default=list
    )
    etiquetas_ids = serializers.ListField(
        child=serializers.UUIDField(), required=False, default=list
    )


class EditarRecetaEntrada(serializers.Serializer):
    """Edicion de los datos generales (RF-006). Todos los campos opcionales."""

    nombre = serializers.CharField(max_length=200, required=False)
    descripcion = serializers.CharField(required=False, allow_blank=True)
    rendimiento_base = serializers.DecimalField(
        max_digits=10, decimal_places=3, required=False
    )
    rendimiento_descripcion = serializers.CharField(max_length=50, required=False)
    fuente_id = serializers.UUIDField(required=False)


class EscalarEntrada(serializers.Serializer):
    """Solicitud de escalado (RF-031)."""

    rendimiento_objetivo = serializers.DecimalField(
        max_digits=10, decimal_places=3, min_value=0
    )
    rendimiento_descripcion = serializers.CharField(max_length=50, required=False)


class ListaComprasEntrada(serializers.Serializer):
    """Solicitud de Lista de Compras (RF-034 y RF-035)."""

    ingredientes_seleccionados = serializers.ListField(
        child=serializers.UUIDField(), allow_empty=True
    )
    rendimiento_objetivo = serializers.DecimalField(
        max_digits=10, decimal_places=3, required=False, allow_null=True
    )
    rendimiento_descripcion = serializers.CharField(max_length=50, required=False)
    persistir = serializers.BooleanField(default=False)


class DuplicarEntrada(serializers.Serializer):
    """Solicitud de variante (RF-010)."""

    nombre = serializers.CharField(max_length=200)


class FavoritaEntrada(serializers.Serializer):
    """Marcado de favorita (RF-043)."""

    favorita = serializers.BooleanField(default=True)


class ItemCompraEntrada(serializers.Serializer):
    """Marcado de un item de la Lista de Compras como comprado (RF-036)."""

    comprado = serializers.BooleanField(default=True)


class ReordenarEntrada(serializers.Serializer):
    """Reordenamiento de preparaciones o pasos (RF-014 y RF-022)."""

    ids_en_orden = serializers.ListField(child=serializers.UUIDField())


class NombreEntrada(serializers.Serializer):
    """Alta o renombrado de un elemento identificado solo por su nombre."""

    nombre = serializers.CharField(max_length=200)


class PasoEntrada(serializers.Serializer):
    """Alta o edicion de un paso (RF-019 y RF-020)."""

    descripcion = serializers.CharField()


class NotaEntrada(serializers.Serializer):
    """Alta o edicion de una nota (RF-025 y RF-026)."""

    texto = serializers.CharField()


class FotografiaEntrada(serializers.Serializer):
    """Alta de una fotografia (RF-023)."""

    ruta = serializers.URLField(max_length=500)
    tipo = serializers.ChoiceField(choices=TIPOS_FOTOGRAFIA, default="proceso")
    descripcion = serializers.CharField(
        max_length=250, required=False, allow_blank=True, default=""
    )


class ModificarIngredienteEntrada(serializers.Serializer):
    """Edicion de un ingrediente de Preparacion (RF-017)."""

    cantidad = serializers.DecimalField(
        max_digits=12, decimal_places=3, required=False, allow_null=True
    )
    unidad = serializers.ChoiceField(
        choices=UNIDADES, required=False, allow_null=True
    )
    tipo_escalado = serializers.ChoiceField(choices=TIPOS_ESCALADO, required=False)
    observacion = serializers.CharField(
        max_length=250, required=False, allow_blank=True
    )


class IngredienteCatalogoEntrada(serializers.Serializer):
    """Alta de un Ingrediente del catalogo (RF-015)."""

    nombre = serializers.CharField(max_length=150)
    descripcion = serializers.CharField(
        required=False, allow_blank=True, default=""
    )


class CategoriaEntrada(serializers.Serializer):
    """Alta de una Categoria o subcategoria (RF-029)."""

    nombre = serializers.CharField(max_length=100)
    categoria_padre_id = serializers.UUIDField(required=False, allow_null=True)


class FuenteEntrada(serializers.Serializer):
    """Alta de una Fuente (RF-030)."""

    nombre = serializers.CharField(max_length=200)
    detalle = serializers.CharField(required=False, allow_blank=True, default="")


class UsuarioEntrada(serializers.Serializer):
    """Alta de un Usuario (RF-001)."""

    nombre = serializers.CharField(max_length=150)
    correo = serializers.EmailField()
    rol = serializers.ChoiceField(
        choices=["administrador", "usuario_familiar"], default="usuario_familiar"
    )
    clave = serializers.CharField(min_length=8, write_only=True)


class ImportarPdfEntrada(serializers.Serializer):
    """Importar una receta desde un PDF (Cap. 7.7, version 2.0)."""

    archivo = serializers.FileField()

    def validate_archivo(self, archivo):
        """Exige que el archivo sea, al menos por extension, un PDF."""
        if not archivo.name.lower().endswith(".pdf"):
            raise serializers.ValidationError("El archivo debe ser un PDF.")
        return archivo


class ImportarFotoEntrada(serializers.Serializer):
    """Importar una receta desde una foto (Cap. 7.7, version 2.0)."""

    archivo = serializers.ImageField()
