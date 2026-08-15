"""Configuracion de Django para el SGRF.

Toda la configuracion sensible se lee de variables de entorno, nunca del
codigo fuente. En Render se definen en el panel del servicio.
"""

from __future__ import annotations

import os
import sys
from datetime import timedelta
from pathlib import Path

import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# El Dominio y la Aplicacion viven en `src/` como paquete independiente de
# Django, de modo que puedan probarse sin levantar el framework.
sys.path.insert(0, str(BASE_DIR / "src"))


def variable(nombre: str, por_defecto: str = "") -> str:
    """Lee una variable de entorno."""
    return os.environ.get(nombre, por_defecto)


def bandera(nombre: str, por_defecto: bool = False) -> bool:
    """Lee una variable de entorno booleana."""
    valor = os.environ.get(nombre)
    if valor is None:
        return por_defecto
    return valor.strip().lower() in {"1", "true", "yes", "si"}


def lista(nombre: str) -> list[str]:
    """Lee una variable de entorno separada por comas."""
    crudo = os.environ.get(nombre, "")
    return [item.strip() for item in crudo.split(",") if item.strip()]


# --- Seguridad -------------------------------------------------------------

SECRET_KEY = variable("SECRET_KEY", "clave-insegura-solo-para-arranque-inicial")
DEBUG = bandera("DEBUG", False)

# Render publica el dominio del servicio en RENDER_EXTERNAL_HOSTNAME.
ALLOWED_HOSTS = lista("ALLOWED_HOSTS") or ["*"]
if variable("RENDER_EXTERNAL_HOSTNAME"):
    ALLOWED_HOSTS.append(variable("RENDER_EXTERNAL_HOSTNAME"))

CSRF_TRUSTED_ORIGINS = lista("CSRF_TRUSTED_ORIGINS")

if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

# --- Aplicaciones ----------------------------------------------------------

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
    "sgrf.infraestructura.recetario",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]

# --- Base de datos ---------------------------------------------------------

# Render entrega la cadena de conexion completa en DATABASE_URL.
DATABASES = {
    "default": dj_database_url.config(
        default=variable("DATABASE_URL", "sqlite:///db.sqlite3"),
        conn_max_age=600,
        conn_health_checks=True,
        ssl_require=not DEBUG and bool(variable("DATABASE_URL")),
    )
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "recetario.UsuarioModelo"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 8},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --- API -------------------------------------------------------------------

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_RENDERER_CLASSES": ("rest_framework.renderers.JSONRenderer",),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "EXCEPTION_HANDLER": "sgrf.presentacion.api.soporte.manejar_excepciones",
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=8),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=30),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": False,
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "usuario_id",
}

# El front se despliega en Vercel, en un dominio distinto del backend.
CORS_ALLOWED_ORIGINS = lista("CORS_ALLOWED_ORIGINS")
CORS_ALLOW_CREDENTIALS = True
if DEBUG and not CORS_ALLOWED_ORIGINS:
    CORS_ALLOW_ALL_ORIGINS = True

# --- Fotografias -----------------------------------------------------------

# El filesystem de Render es efimero: lo que se sube se pierde en cada
# redespliegue. Por eso las imagenes se almacenan fuera de la aplicacion.
CLOUDINARY_URL = variable("CLOUDINARY_URL")

if CLOUDINARY_URL:
    # La biblioteca se configura sola leyendo CLOUDINARY_URL del entorno.
    import cloudinary

    cloudinary.config(secure=True)

# --- Archivos estaticos ----------------------------------------------------

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"
    },
}

# --- Localizacion ----------------------------------------------------------

LANGUAGE_CODE = "es-ar"
TIME_ZONE = "America/Argentina/Buenos_Aires"
USE_I18N = True
USE_TZ = True

# --- Registro --------------------------------------------------------------

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"consola": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["consola"], "level": variable("LOG_LEVEL", "INFO")},
}
