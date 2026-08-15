"""Modelos de persistencia (Django ORM).

Implementan el modelo fisico del Capitulo 7.3 respetando las
cardinalidades del analisis. Son detalle de Infraestructura: el Dominio no
los conoce y nunca los importa.

Se mantiene el Lenguaje Ubicuo en los nombres de tablas y campos. El
sufijo `Modelo` distingue la clase de persistencia de la entidad del
Dominio homonima.

Las restricciones de integridad se declaran aqui ademas de validarse en el
Dominio, segun exige el Capitulo 5.7.
"""

from __future__ import annotations

import uuid

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class GestorUsuarios(BaseUserManager):
    """Gestor de usuarios que identifica por correo electronico."""

    def create_user(self, correo, nombre, password=None, **extras):
        """Crea un Usuario Familiar."""
        if not correo:
            raise ValueError("El usuario requiere un correo electronico.")
        usuario = self.model(
            correo=self.normalize_email(correo), nombre=nombre, **extras
        )
        usuario.set_password(password)
        usuario.save(using=self._db)
        return usuario

    def create_superuser(self, correo, nombre, password=None, **extras):
        """Crea un Administrador con acceso al panel de Django."""
        extras.setdefault("rol", "administrador")
        extras.setdefault("is_staff", True)
        extras.setdefault("is_superuser", True)
        return self.create_user(correo, nombre, password, **extras)


class UsuarioModelo(AbstractBaseUser, PermissionsMixin):
    """Integrante de la familia con acceso al recetario.

    RF-003: los usuarios se desactivan mediante `activo`, nunca se
    eliminan, para preservar el historial.
    """

    ROLES = [
        ("administrador", "Administrador"),
        ("usuario_familiar", "Usuario Familiar"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=150)
    correo = models.EmailField(unique=True)
    rol = models.CharField(max_length=20, choices=ROLES, default="usuario_familiar")
    activo = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    fecha_alta = models.DateTimeField(auto_now_add=True)

    objects = GestorUsuarios()

    USERNAME_FIELD = "correo"
    REQUIRED_FIELDS = ["nombre"]

    class Meta:
        db_table = "usuario"
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"

    @property
    def is_active(self) -> bool:
        """Django exige `is_active`; el dominio lo llama `activo`."""
        return self.activo

    def __str__(self) -> str:
        return f"{self.nombre} ({self.correo})"


class FuenteModelo(models.Model):
    """Origen de una Receta. RN-002: cada receta referencia exactamente una."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=200, unique=True)
    detalle = models.TextField(blank=True, default="")

    class Meta:
        db_table = "fuente"
        ordering = ["nombre"]
        verbose_name = "Fuente"
        verbose_name_plural = "Fuentes"

    def __str__(self) -> str:
        return self.nombre


class CategoriaModelo(models.Model):
    """Clasificacion jerarquica. La subcategoria referencia a su padre."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=100)
    categoria_padre = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="subcategorias",
    )

    class Meta:
        db_table = "categoria"
        ordering = ["nombre"]
        unique_together = [("nombre", "categoria_padre")]
        verbose_name = "Categoria"
        verbose_name_plural = "Categorias"

    def __str__(self) -> str:
        return self.nombre


class EtiquetaModelo(models.Model):
    """Clasificacion transversal de Recetas."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=50, unique=True)

    class Meta:
        db_table = "etiqueta"
        ordering = ["nombre"]
        verbose_name = "Etiqueta"
        verbose_name_plural = "Etiquetas"

    def __str__(self) -> str:
        return self.nombre


class IngredienteModelo(models.Model):
    """Elemento del catalogo unico reutilizable.

    Capitulo 3.6: el Ingrediente jamas almacena cantidades.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=150, unique=True)
    descripcion = models.TextField(blank=True, default="")

    class Meta:
        db_table = "ingrediente"
        ordering = ["nombre"]
        verbose_name = "Ingrediente"
        verbose_name_plural = "Ingredientes"

    def __str__(self) -> str:
        return self.nombre


class RecetaModelo(models.Model):
    """Elaboracion culinaria completa. Raiz del agregado (ADR-001).

    El Rendimiento Base se almacena descompuesto en valor y descripcion,
    ya que el Objeto de Valor carece de identidad propia.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=200, unique=True)
    descripcion = models.TextField(blank=True, default="")
    rendimiento_valor = models.DecimalField(max_digits=10, decimal_places=3)
    rendimiento_descripcion = models.CharField(max_length=50, default="porciones")
    fuente = models.ForeignKey(
        FuenteModelo, on_delete=models.PROTECT, related_name="recetas"
    )
    categorias = models.ManyToManyField(
        CategoriaModelo, blank=True, related_name="recetas", db_table="receta_categoria"
    )
    etiquetas = models.ManyToManyField(
        EtiquetaModelo, blank=True, related_name="recetas", db_table="receta_etiqueta"
    )
    archivada = models.BooleanField(default=False)
    favorita = models.BooleanField(default=False)
    autor = models.ForeignKey(
        UsuarioModelo,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="recetas_creadas",
    )
    fecha_creacion = models.DateTimeField()

    class Meta:
        db_table = "receta"
        ordering = ["nombre"]
        verbose_name = "Receta"
        verbose_name_plural = "Recetas"
        indexes = [
            models.Index(
                fields=["archivada", "nombre"], name="receta_archivada_nombre_idx"
            ),
            models.Index(fields=["favorita"], name="receta_favorita_idx"),
        ]

    def __str__(self) -> str:
        return self.nombre


class PreparacionModelo(models.Model):
    """Etapa independiente de una Receta (ADR-002).

    El borrado en cascada es correcto: la Preparacion carece de sentido
    fuera de su Receta.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    receta = models.ForeignKey(
        RecetaModelo, on_delete=models.CASCADE, related_name="preparaciones"
    )
    nombre = models.CharField(max_length=150)
    orden = models.PositiveIntegerField(default=1)

    class Meta:
        db_table = "preparacion"
        ordering = ["orden"]
        verbose_name = "Preparacion"
        verbose_name_plural = "Preparaciones"

    def __str__(self) -> str:
        return f"{self.receta.nombre} / {self.nombre}"


class IngredientePreparacionModelo(models.Model):
    """Relacion entre un Ingrediente y una Preparacion.

    Aqui residen las cantidades. Los ingredientes 'a gusto' y 'cantidad
    necesaria' no poseen cantidad: por eso los campos admiten nulo.
    """

    TIPOS_ESCALADO = [
        ("lineal", "Lineal"),
        ("fijo", "Fijo"),
        ("a_gusto", "A gusto"),
        ("cantidad_necesaria", "Cantidad necesaria"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    preparacion = models.ForeignKey(
        PreparacionModelo, on_delete=models.CASCADE, related_name="ingredientes"
    )
    ingrediente = models.ForeignKey(
        IngredienteModelo, on_delete=models.PROTECT, related_name="usos"
    )
    cantidad_valor = models.DecimalField(
        max_digits=12, decimal_places=3, null=True, blank=True
    )
    cantidad_unidad = models.CharField(max_length=10, null=True, blank=True)
    tipo_escalado = models.CharField(
        max_length=25, choices=TIPOS_ESCALADO, default="lineal"
    )
    observacion = models.CharField(max_length=250, blank=True, default="")

    class Meta:
        db_table = "ingrediente_preparacion"
        verbose_name = "Ingrediente de preparacion"
        verbose_name_plural = "Ingredientes de preparacion"
        constraints = [
            models.UniqueConstraint(
                fields=["preparacion", "ingrediente"],
                name="ingrediente_unico_por_preparacion",
            )
        ]

    def __str__(self) -> str:
        return f"{self.ingrediente.nombre} en {self.preparacion.nombre}"


class PasoModelo(models.Model):
    """Instruccion ordenada dentro de una Preparacion."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    preparacion = models.ForeignKey(
        PreparacionModelo, on_delete=models.CASCADE, related_name="pasos"
    )
    descripcion = models.TextField()
    orden = models.PositiveIntegerField(default=1)

    class Meta:
        db_table = "paso"
        ordering = ["orden"]
        verbose_name = "Paso"
        verbose_name_plural = "Pasos"

    def __str__(self) -> str:
        return f"{self.orden}. {self.descripcion[:40]}"


class FotografiaModelo(models.Model):
    """Imagen asociada a una Preparacion.

    `ruta` guarda la URL devuelta por el almacenamiento externo. El
    filesystem de Render es efimero, de modo que las imagenes viven fuera
    de la aplicacion.

    RN-005 (maximo dos de proceso y una final por Receta) se valida en el
    Dominio, ya que la restriccion abarca todas las Preparaciones de la
    Receta y no puede expresarse como una restriccion de tabla.
    """

    TIPOS = [("proceso", "Proceso"), ("final", "Final")]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    preparacion = models.ForeignKey(
        PreparacionModelo, on_delete=models.CASCADE, related_name="fotografias"
    )
    ruta = models.URLField(max_length=500)
    tipo = models.CharField(max_length=10, choices=TIPOS, default="proceso")
    descripcion = models.CharField(max_length=250, blank=True, default="")

    class Meta:
        db_table = "fotografia"
        verbose_name = "Fotografia"
        verbose_name_plural = "Fotografias"

    def __str__(self) -> str:
        return f"{self.tipo}: {self.ruta}"


class NotaModelo(models.Model):
    """Observacion permanente asociada a una Receta."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    receta = models.ForeignKey(
        RecetaModelo, on_delete=models.CASCADE, related_name="notas"
    )
    texto = models.TextField()
    autor = models.ForeignKey(
        UsuarioModelo,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="notas",
    )
    fecha = models.DateTimeField()

    class Meta:
        db_table = "nota"
        ordering = ["-fecha"]
        verbose_name = "Nota"
        verbose_name_plural = "Notas"

    def __str__(self) -> str:
        return self.texto[:50]


class ListaCompraModelo(models.Model):
    """Lista de Compras consolidada.

    Se persiste la Lista, jamas la receta escalada que la origino
    (ADR-003).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    usuario = models.ForeignKey(
        UsuarioModelo,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="listas_compra",
    )
    fecha = models.DateTimeField()

    class Meta:
        db_table = "lista_compra"
        ordering = ["-fecha"]
        verbose_name = "Lista de compras"
        verbose_name_plural = "Listas de compras"

    def __str__(self) -> str:
        return f"Lista del {self.fecha:%d/%m/%Y}"


class ItemCompraModelo(models.Model):
    """Renglon consolidado de una Lista de Compras.

    Conserva `nombre_ingrediente` ademas de la referencia al catalogo para
    que la lista siga siendo legible aunque el ingrediente se renombre.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lista = models.ForeignKey(
        ListaCompraModelo, on_delete=models.CASCADE, related_name="items"
    )
    ingrediente = models.ForeignKey(
        IngredienteModelo, on_delete=models.PROTECT, related_name="items_compra"
    )
    nombre_ingrediente = models.CharField(max_length=150)
    cantidad_valor = models.DecimalField(
        max_digits=12, decimal_places=3, null=True, blank=True
    )
    cantidad_unidad = models.CharField(max_length=10, null=True, blank=True)
    tipo_escalado = models.CharField(max_length=25, default="lineal")
    comprado = models.BooleanField(default=False)

    class Meta:
        db_table = "item_compra"
        ordering = ["nombre_ingrediente"]
        verbose_name = "Item de compra"
        verbose_name_plural = "Items de compra"

    def __str__(self) -> str:
        return self.nombre_ingrediente
