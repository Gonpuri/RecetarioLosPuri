"""Comando para crear el Administrador inicial.

Permite dejar operativo el sistema en el primer despliegue sin acceso
interactivo a la consola, leyendo los datos de variables de entorno.
"""

import os

from django.core.management.base import BaseCommand

from ...models import UsuarioModelo


class Command(BaseCommand):
    """Crea el Administrador inicial si todavia no existe."""

    help = "Crea el usuario Administrador inicial a partir de variables de entorno."

    def handle(self, *args, **opciones):
        correo = os.environ.get("ADMIN_CORREO")
        clave = os.environ.get("ADMIN_CLAVE")
        nombre = os.environ.get("ADMIN_NOMBRE", "Administrador")

        if not correo or not clave:
            self.stdout.write(
                "ADMIN_CORREO y ADMIN_CLAVE no definidos: no se crea administrador."
            )
            return

        if UsuarioModelo.objects.filter(correo__iexact=correo).exists():
            self.stdout.write(f"El administrador {correo} ya existe.")
            return

        UsuarioModelo.objects.create_superuser(
            correo=correo, nombre=nombre, password=clave
        )
        self.stdout.write(self.style.SUCCESS(f"Administrador {correo} creado."))
