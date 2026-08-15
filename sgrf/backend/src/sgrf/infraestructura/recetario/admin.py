"""Panel de administracion de Django.

Sirve como herramienta operativa para cargar catalogos y revisar datos
mientras la interfaz definitiva se construye en la Etapa 4. No reemplaza a
los Casos de Uso: editar recetas desde aqui evita las validaciones del
Dominio, de modo que conviene reservarlo para los catalogos.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from . import models


@admin.register(models.UsuarioModelo)
class UsuarioAdmin(UserAdmin):
    """Administracion de Usuarios identificados por correo."""

    ordering = ["correo"]
    list_display = ["correo", "nombre", "rol", "activo"]
    list_filter = ["rol", "activo"]
    search_fields = ["correo", "nombre"]
    fieldsets = (
        (None, {"fields": ("correo", "password")}),
        ("Datos personales", {"fields": ("nombre",)}),
        ("Permisos", {"fields": ("rol", "activo", "is_staff", "is_superuser")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("correo", "nombre", "rol", "password1", "password2"),
            },
        ),
    )


@admin.register(models.FuenteModelo)
class FuenteAdmin(admin.ModelAdmin):
    """Administracion de Fuentes."""

    list_display = ["nombre", "detalle"]
    search_fields = ["nombre"]


@admin.register(models.CategoriaModelo)
class CategoriaAdmin(admin.ModelAdmin):
    """Administracion de Categorias y subcategorias."""

    list_display = ["nombre", "categoria_padre"]
    list_filter = ["categoria_padre"]
    search_fields = ["nombre"]


@admin.register(models.EtiquetaModelo)
class EtiquetaAdmin(admin.ModelAdmin):
    """Administracion de Etiquetas."""

    list_display = ["nombre"]
    search_fields = ["nombre"]


@admin.register(models.IngredienteModelo)
class IngredienteAdmin(admin.ModelAdmin):
    """Administracion del catalogo de Ingredientes."""

    list_display = ["nombre", "descripcion"]
    search_fields = ["nombre"]


@admin.register(models.RecetaModelo)
class RecetaAdmin(admin.ModelAdmin):
    """Consulta de Recetas.

    Se expone en modo lectura: modificar una receta debe hacerse mediante
    los Casos de Uso, que aplican las reglas del negocio.
    """

    list_display = ["nombre", "rendimiento_valor", "fuente", "archivada", "favorita"]
    list_filter = ["archivada", "favorita", "fuente"]
    search_fields = ["nombre"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
