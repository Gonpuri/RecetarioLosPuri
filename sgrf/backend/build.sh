#!/usr/bin/env bash
# Script de compilacion que ejecuta Render en cada despliegue.
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
python manage.py crear_administrador
