"""Rutas del proyecto.

Reune la verificacion de estado, la autenticacion, la API del recetario y
el panel de administracion.
"""

from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from sgrf import __version__


def estado(request):
    """Verificacion de estado usada por Render y por el front."""
    return JsonResponse(
        {"estado": "operativo", "sistema": "SGRF", "version": __version__}
    )


urlpatterns = [
    path("", estado),
    path("api/estado/", estado, name="estado"),
    path("api/auth/token/", TokenObtainPairView.as_view(), name="obtener_token"),
    path("api/auth/refrescar/", TokenRefreshView.as_view(), name="refrescar_token"),
    path("api/", include("sgrf.presentacion.api.urls")),
    path("admin/", admin.site.urls),
]
