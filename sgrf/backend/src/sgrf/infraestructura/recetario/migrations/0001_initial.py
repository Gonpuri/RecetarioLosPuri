"""Migracion inicial del SGRF.

Crea el modelo fisico descrito en el Capitulo 7.3 respetando las
cardinalidades del analisis.

Escrita a mano porque el entorno de generacion no disponia de Django. Si
al desplegar `makemigrations --check` detectara alguna diferencia menor
respecto de los modelos, basta con generar una migracion complementaria:
las tablas y columnas creadas aqui son las correctas.
"""

import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    """Estructura inicial de la base de datos."""

    initial = True

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.CreateModel(
            name="UsuarioModelo",
            fields=[
                ("password", models.CharField(max_length=128, verbose_name="password")),
                (
                    "last_login",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="last login"
                    ),
                ),
                (
                    "is_superuser",
                    models.BooleanField(
                        default=False,
                        help_text=(
                            "Designates that this user has all permissions without "
                            "explicitly assigning them."
                        ),
                        verbose_name="superuser status",
                    ),
                ),
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("nombre", models.CharField(max_length=150)),
                ("correo", models.EmailField(max_length=254, unique=True)),
                (
                    "rol",
                    models.CharField(
                        choices=[
                            ("administrador", "Administrador"),
                            ("usuario_familiar", "Usuario Familiar"),
                        ],
                        default="usuario_familiar",
                        max_length=20,
                    ),
                ),
                ("activo", models.BooleanField(default=True)),
                ("is_staff", models.BooleanField(default=False)),
                ("fecha_alta", models.DateTimeField(auto_now_add=True)),
                (
                    "groups",
                    models.ManyToManyField(
                        blank=True,
                        help_text=(
                            "The groups this user belongs to. A user will get all "
                            "permissions granted to each of their groups."
                        ),
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.group",
                        verbose_name="groups",
                    ),
                ),
                (
                    "user_permissions",
                    models.ManyToManyField(
                        blank=True,
                        help_text="Specific permissions for this user.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.permission",
                        verbose_name="user permissions",
                    ),
                ),
            ],
            options={
                "verbose_name": "Usuario",
                "verbose_name_plural": "Usuarios",
                "db_table": "usuario",
            },
        ),
        migrations.CreateModel(
            name="FuenteModelo",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("nombre", models.CharField(max_length=200, unique=True)),
                ("detalle", models.TextField(blank=True, default="")),
            ],
            options={
                "verbose_name": "Fuente",
                "verbose_name_plural": "Fuentes",
                "db_table": "fuente",
                "ordering": ["nombre"],
            },
        ),
        migrations.CreateModel(
            name="EtiquetaModelo",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("nombre", models.CharField(max_length=50, unique=True)),
            ],
            options={
                "verbose_name": "Etiqueta",
                "verbose_name_plural": "Etiquetas",
                "db_table": "etiqueta",
                "ordering": ["nombre"],
            },
        ),
        migrations.CreateModel(
            name="IngredienteModelo",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("nombre", models.CharField(max_length=150, unique=True)),
                ("descripcion", models.TextField(blank=True, default="")),
            ],
            options={
                "verbose_name": "Ingrediente",
                "verbose_name_plural": "Ingredientes",
                "db_table": "ingrediente",
                "ordering": ["nombre"],
            },
        ),
        migrations.CreateModel(
            name="CategoriaModelo",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("nombre", models.CharField(max_length=100)),
                (
                    "categoria_padre",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="subcategorias",
                        to="recetario.categoriamodelo",
                    ),
                ),
            ],
            options={
                "verbose_name": "Categoria",
                "verbose_name_plural": "Categorias",
                "db_table": "categoria",
                "ordering": ["nombre"],
                "unique_together": {("nombre", "categoria_padre")},
            },
        ),
        migrations.CreateModel(
            name="RecetaModelo",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("nombre", models.CharField(max_length=200, unique=True)),
                ("descripcion", models.TextField(blank=True, default="")),
                (
                    "rendimiento_valor",
                    models.DecimalField(decimal_places=3, max_digits=10),
                ),
                (
                    "rendimiento_descripcion",
                    models.CharField(default="porciones", max_length=50),
                ),
                ("archivada", models.BooleanField(default=False)),
                ("favorita", models.BooleanField(default=False)),
                ("fecha_creacion", models.DateTimeField()),
                (
                    "autor",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="recetas_creadas",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "fuente",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="recetas",
                        to="recetario.fuentemodelo",
                    ),
                ),
                (
                    "categorias",
                    models.ManyToManyField(
                        blank=True,
                        db_table="receta_categoria",
                        related_name="recetas",
                        to="recetario.categoriamodelo",
                    ),
                ),
                (
                    "etiquetas",
                    models.ManyToManyField(
                        blank=True,
                        db_table="receta_etiqueta",
                        related_name="recetas",
                        to="recetario.etiquetamodelo",
                    ),
                ),
            ],
            options={
                "verbose_name": "Receta",
                "verbose_name_plural": "Recetas",
                "db_table": "receta",
                "ordering": ["nombre"],
            },
        ),
        migrations.CreateModel(
            name="PreparacionModelo",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("nombre", models.CharField(max_length=150)),
                ("orden", models.PositiveIntegerField(default=1)),
                (
                    "receta",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="preparaciones",
                        to="recetario.recetamodelo",
                    ),
                ),
            ],
            options={
                "verbose_name": "Preparacion",
                "verbose_name_plural": "Preparaciones",
                "db_table": "preparacion",
                "ordering": ["orden"],
            },
        ),
        migrations.CreateModel(
            name="IngredientePreparacionModelo",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "cantidad_valor",
                    models.DecimalField(
                        blank=True, decimal_places=3, max_digits=12, null=True
                    ),
                ),
                (
                    "cantidad_unidad",
                    models.CharField(blank=True, max_length=10, null=True),
                ),
                (
                    "tipo_escalado",
                    models.CharField(
                        choices=[
                            ("lineal", "Lineal"),
                            ("fijo", "Fijo"),
                            ("a_gusto", "A gusto"),
                            ("cantidad_necesaria", "Cantidad necesaria"),
                        ],
                        default="lineal",
                        max_length=25,
                    ),
                ),
                ("observacion", models.CharField(blank=True, default="", max_length=250)),
                (
                    "ingrediente",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="usos",
                        to="recetario.ingredientemodelo",
                    ),
                ),
                (
                    "preparacion",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="ingredientes",
                        to="recetario.preparacionmodelo",
                    ),
                ),
            ],
            options={
                "verbose_name": "Ingrediente de preparacion",
                "verbose_name_plural": "Ingredientes de preparacion",
                "db_table": "ingrediente_preparacion",
            },
        ),
        migrations.CreateModel(
            name="PasoModelo",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("descripcion", models.TextField()),
                ("orden", models.PositiveIntegerField(default=1)),
                (
                    "preparacion",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="pasos",
                        to="recetario.preparacionmodelo",
                    ),
                ),
            ],
            options={
                "verbose_name": "Paso",
                "verbose_name_plural": "Pasos",
                "db_table": "paso",
                "ordering": ["orden"],
            },
        ),
        migrations.CreateModel(
            name="FotografiaModelo",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("ruta", models.URLField(max_length=500)),
                (
                    "tipo",
                    models.CharField(
                        choices=[("proceso", "Proceso"), ("final", "Final")],
                        default="proceso",
                        max_length=10,
                    ),
                ),
                ("descripcion", models.CharField(blank=True, default="", max_length=250)),
                (
                    "preparacion",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="fotografias",
                        to="recetario.preparacionmodelo",
                    ),
                ),
            ],
            options={
                "verbose_name": "Fotografia",
                "verbose_name_plural": "Fotografias",
                "db_table": "fotografia",
            },
        ),
        migrations.CreateModel(
            name="NotaModelo",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("texto", models.TextField()),
                ("fecha", models.DateTimeField()),
                (
                    "autor",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="notas",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "receta",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="notas",
                        to="recetario.recetamodelo",
                    ),
                ),
            ],
            options={
                "verbose_name": "Nota",
                "verbose_name_plural": "Notas",
                "db_table": "nota",
                "ordering": ["-fecha"],
            },
        ),
        migrations.CreateModel(
            name="ListaCompraModelo",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("fecha", models.DateTimeField()),
                (
                    "usuario",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="listas_compra",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Lista de compras",
                "verbose_name_plural": "Listas de compras",
                "db_table": "lista_compra",
                "ordering": ["-fecha"],
            },
        ),
        migrations.CreateModel(
            name="ItemCompraModelo",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("nombre_ingrediente", models.CharField(max_length=150)),
                (
                    "cantidad_valor",
                    models.DecimalField(
                        blank=True, decimal_places=3, max_digits=12, null=True
                    ),
                ),
                (
                    "cantidad_unidad",
                    models.CharField(blank=True, max_length=10, null=True),
                ),
                ("tipo_escalado", models.CharField(default="lineal", max_length=25)),
                ("comprado", models.BooleanField(default=False)),
                (
                    "ingrediente",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="items_compra",
                        to="recetario.ingredientemodelo",
                    ),
                ),
                (
                    "lista",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="items",
                        to="recetario.listacompramodelo",
                    ),
                ),
            ],
            options={
                "verbose_name": "Item de compra",
                "verbose_name_plural": "Items de compra",
                "db_table": "item_compra",
                "ordering": ["nombre_ingrediente"],
            },
        ),
        migrations.AddIndex(
            model_name="recetamodelo",
            index=models.Index(
                fields=["archivada", "nombre"], name="receta_archivada_nombre_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="recetamodelo",
            index=models.Index(fields=["favorita"], name="receta_favorita_idx"),
        ),
        migrations.AddConstraint(
            model_name="ingredientepreparacionmodelo",
            constraint=models.UniqueConstraint(
                fields=("preparacion", "ingrediente"),
                name="ingrediente_unico_por_preparacion",
            ),
        ),
    ]
