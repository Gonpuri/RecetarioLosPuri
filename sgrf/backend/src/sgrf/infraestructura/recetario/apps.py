"""Configuracion de la aplicacion Django del recetario."""

from django.apps import AppConfig


class RecetarioConfig(AppConfig):
    """Registra los modelos de persistencia bajo la etiqueta `recetario`."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "sgrf.infraestructura.recetario"
    label = "recetario"
    verbose_name = "Recetario"
