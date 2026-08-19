"""Rutas de la API del SGRF.

Las rutas siguen el Lenguaje Ubicuo: `/api/recetas/`, no `/api/recipes/`.
Los recursos que solo existen dentro de una Receta se anidan bajo ella,
reflejando que el agregado es la unidad de acceso (ADR-001).
"""

from django.urls import path

from . import vistas_catalogo as c
from . import vistas_fotografias as f
from . import vistas_importacion as imp
from . import vistas_recetas as r

urlpatterns = [
    # Recetas
    path("recetas/", r.RecetasVista.as_view(), name="recetas"),
    path("recetas/<uuid:receta_id>/", r.RecetaVista.as_view(), name="receta"),
    path(
        "recetas/<uuid:receta_id>/archivar/",
        r.ArchivarVista.as_view(),
        name="archivar",
    ),
    path(
        "recetas/<uuid:receta_id>/duplicar/",
        r.DuplicarVista.as_view(),
        name="duplicar",
    ),
    path(
        "recetas/<uuid:receta_id>/favorita/",
        r.FavoritaVista.as_view(),
        name="favorita",
    ),
    path("recetas/<uuid:receta_id>/escalar/", r.EscalarVista.as_view(), name="escalar"),
    path(
        "recetas/<uuid:receta_id>/lista-compras/",
        r.ListaComprasVista.as_view(),
        name="lista_compras",
    ),
    # Preparaciones
    path(
        "recetas/<uuid:receta_id>/preparaciones/",
        r.PreparacionesVista.as_view(),
        name="preparaciones",
    ),
    path(
        "recetas/<uuid:receta_id>/preparaciones/reordenar/",
        r.ReordenarPreparacionesVista.as_view(),
        name="reordenar_preparaciones",
    ),
    path(
        "recetas/<uuid:receta_id>/preparaciones/<uuid:preparacion_id>/",
        r.PreparacionVista.as_view(),
        name="preparacion",
    ),
    # Ingredientes de una preparacion
    path(
        "recetas/<uuid:receta_id>/preparaciones/<uuid:preparacion_id>/ingredientes/",
        r.IngredientesPreparacionVista.as_view(),
        name="ingredientes_preparacion",
    ),
    path(
        "recetas/<uuid:receta_id>/preparaciones/<uuid:preparacion_id>/"
        "ingredientes/<uuid:ingrediente_id>/",
        r.IngredientePreparacionVista.as_view(),
        name="ingrediente_preparacion",
    ),
    # Pasos
    path(
        "recetas/<uuid:receta_id>/preparaciones/<uuid:preparacion_id>/pasos/",
        r.PasosVista.as_view(),
        name="pasos",
    ),
    path(
        "recetas/<uuid:receta_id>/preparaciones/<uuid:preparacion_id>/pasos/reordenar/",
        r.ReordenarPasosVista.as_view(),
        name="reordenar_pasos",
    ),
    path(
        "recetas/<uuid:receta_id>/preparaciones/<uuid:preparacion_id>/"
        "pasos/<uuid:paso_id>/",
        r.PasoVista.as_view(),
        name="paso",
    ),
    # Fotografias
    path(
        "recetas/<uuid:receta_id>/preparaciones/<uuid:preparacion_id>/fotografias/",
        r.FotografiasVista.as_view(),
        name="fotografias",
    ),
    path(
        "recetas/<uuid:receta_id>/preparaciones/<uuid:preparacion_id>/"
        "fotografias/<uuid:fotografia_id>/",
        r.FotografiaVista.as_view(),
        name="fotografia",
    ),
    # Notas
    path("recetas/<uuid:receta_id>/notas/", r.NotasVista.as_view(), name="notas"),
    path(
        "recetas/<uuid:receta_id>/notas/<uuid:nota_id>/",
        r.NotaVista.as_view(),
        name="nota",
    ),
    # Clasificacion
    path(
        "recetas/<uuid:receta_id>/<str:tipo>/<uuid:elemento_id>/",
        r.ClasificacionVista.as_view(),
        name="clasificacion",
    ),
    # Fotografias
    path(
        "fotografias/firma/",
        f.FirmaFotografiaVista.as_view(),
        name="firma_fotografia",
    ),
    # Importacion de recetas (Cap. 7.7, version 2.0)
    path(
        "importar/pdf/",
        imp.ImportarPdfVista.as_view(),
        name="importar_pdf",
    ),
    path(
        "importar/foto/",
        imp.ImportarFotoVista.as_view(),
        name="importar_foto",
    ),
    path(
        "importar/dictado/",
        imp.ImportarDictadoVista.as_view(),
        name="importar_dictado",
    ),
    # Listas de compras
    path("listas-compra/", r.ListasComprasVista.as_view(), name="listas_compra"),
    path(
        "listas-compra/<uuid:lista_id>/items/<uuid:item_id>/",
        r.ItemCompraVista.as_view(),
        name="item_compra",
    ),
    # Catalogos
    path("ingredientes/", c.IngredientesVista.as_view(), name="ingredientes"),
    path("categorias/", c.CategoriasVista.as_view(), name="categorias"),
    path("etiquetas/", c.EtiquetasVista.as_view(), name="etiquetas"),
    path("fuentes/", c.FuentesVista.as_view(), name="fuentes"),
    # Usuarios
    path("usuarios/", c.UsuariosVista.as_view(), name="usuarios"),
    path("usuarios/<uuid:usuario_id>/", c.UsuarioVista.as_view(), name="usuario"),
    path("perfil/", c.PerfilVista.as_view(), name="perfil"),
]
