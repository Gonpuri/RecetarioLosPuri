# SGRF — Sistema de Gestión de Recetas Familiares

Implementación de la especificación **SGRF-EIS-001** (Capítulos 1 a 7) siguiendo
las directivas de `PROMPT_CODEX.md`.

**Estado: las cinco etapas completas.**

| Documento | Para qué |
|---|---|
| [TUTORIAL_DESPLIEGUE.md](TUTORIAL_DESPLIEGUE.md) | Poner el sistema en producción, paso a paso |
| [DOCUMENTACION.md](DOCUMENTACION.md) | Cómo está hecho: arquitectura, dominio, API, decisiones |
| [docs/](docs/) | Los 7 capítulos del análisis funcional |

---

## Stack definido

| Capa | Tecnología | Despliegue |
|---|---|---|
| Presentación | React + TypeScript + Tailwind | Vercel |
| Aplicación / Dominio / Infraestructura | Python + Django REST Framework | Render |
| Persistencia | PostgreSQL | Render |

El **Dominio no depende de Django**: usa exclusivamente la biblioteca estándar de
Python. Esto cumple el principio 5.1 del Capítulo 5 (*independiente del framework
y del motor de base de datos*) y permite probarlo sin levantar la aplicación.

---

## Estructura

```
backend/
├── pyproject.toml
├── src/sgrf/
│   └── dominio/
│       ├── excepciones.py            Errores de negocio
│       ├── objetos_valor/            Cantidad, Unidad, Rendimiento, TipoEscalado
│       ├── entidades/
│       │   ├── catalogo.py           Usuario, Fuente, Categoria, Etiqueta, Ingrediente
│       │   ├── componentes.py        IngredientePreparacion, Paso, Fotografia, Nota
│       │   ├── preparacion.py        Preparacion (unidad funcional, ADR-002)
│       │   ├── receta.py             Receta (Aggregate Root, ADR-001)
│       │   └── lista_compra.py       ListaCompra, ItemCompra
│       │   ├── servicios/            EscaladorRecetas, GeneradorListaCompras,
│       │   │                          BuscadorRecetas, ValidadorRecetas
│       │   └── repositorios/         Interfaces (contratos de persistencia)
│       └── aplicacion/
│           ├── dto.py                Comandos y Resultados
│           ├── ensambladores.py      Traducción Dominio ↔ DTO
│           ├── autorizacion.py       Permisos por perfil
│           ├── unidad_de_trabajo.py  Transacciones (Unit of Work)
│       │   └── casos_uso/            23 casos de uso
│       └── infraestructura/
│           ├── recetario/            Modelos Django + migración + admin
│           └── persistencia/         Repositorios, mapeadores, UnitOfWork
├── config/                           settings, urls, wsgi
├── manage.py
├── requirements.txt
└── tests/
    ├── dominio/                      79 pruebas unitarias
    ├── aplicacion/                   60 pruebas de integración
    └── infraestructura/              16 pruebas contra PostgreSQL
```

---

## Trazabilidad: reglas de negocio implementadas

| Regla | Enunciado | Dónde se garantiza |
|---|---|---|
| RN-001 | Rendimiento Base único | `Receta.__post_init__`, `Rendimiento` |
| RN-002 | Fuente única y obligatoria | `Receta.__post_init__` |
| RN-003 | Una o más Preparaciones | `Receta.quitar_preparacion`, `ValidadorRecetas` |
| RN-004 | La receta base nunca se modifica | `Cantidad` inmutable + `RecetaEscalada` |
| RN-005 | Máx. 2 fotos proceso + 1 final | `Receta._validar_limite_fotografias` |
| RN-006 | Lista solo con lo seleccionado | `GeneradorListaCompras.generar` |

### Cómo se garantiza RN-004 (la regla más importante)

Tres mecanismos independientes:

1. `Cantidad` es un `dataclass(frozen=True)`: no se puede mutar.
2. `EscaladorRecetas` no recibe permisos de escritura — solo lee la `Receta` y
   construye estructuras nuevas.
3. El resultado es `RecetaEscalada`, un tipo **distinto** de `Receta` e inmutable,
   que solo referencia la receta por su `id`. Es imposible confundirlo con la
   entidad y no existe repositorio capaz de persistirlo (ADR-003).

---

## Pruebas

```bash
cd backend
pip install -e ".[dev]"    # o: pip install pytest
pytest
```

Cobertura actual: **139 pruebas**.

| Capa | Pruebas | Cubre |
|---|---|---|
| Dominio | 79 | Objetos de valor, agregado Receta, servicios |
| Aplicación | 60 | Casos de uso, permisos, transacciones, flujo completo |

Las pruebas de Aplicación usan repositorios en memoria (`tests/aplicacion/dobles.py`)
que implementan los contratos del Dominio. Esto demuestra que la inversión de
dependencias funciona: **los 23 casos de uso se ejecutan completos sin Django ni
PostgreSQL**. En la Etapa 3 se suman las implementaciones reales y los casos de uso
no cambian una línea.

---

## Decisiones tomadas y su justificación

Estas decisiones resuelven puntos que el análisis no detalla. **Están marcadas
para tu confirmación** porque `PROMPT_CODEX.md` prohíbe inventar reglas.

| # | Decisión | Razón |
|---|---|---|
| D-1 | `A gusto` y `Cantidad necesaria` **no llevan** cantidad numérica | Se definen por la ausencia de cantidad determinada |
| D-2 | La consolidación de la lista agrupa por (Ingrediente, Unidad, TipoEscalado) | El análisis dice "mantener unidades": no se convierte entre g y ml |
| D-3 | `Fijo` conserva la cantidad al escalar | Interpretación literal del término |
| D-4 | Una receta archivada no se puede editar hasta restaurarla | Preserva el valor histórico del archivado |
| D-5 | El límite de fotos (RN-005) se valida en `Receta`, no en `Preparacion` | Cap. 3.9 asocia fotos a Preparación, pero RN-005 fija el límite por Receta |
| D-6 | `Rendimiento` incluye descripción y solo escala entre iguales | Evita convertir "4 porciones" en "8 tortas" |
| D-7 | No se repite el mismo Ingrediente dentro de una Preparación | Mitiga el riesgo de duplicados (Cap. 2.11) |
| D-8 | Se usa `Decimal`, nunca `float` | Evita que 0.1 + 0.2 = 0.30000000000000004 en cantidades |
| D-9 | Catálogos (Ingredientes, Categorías, Etiquetas, Fuentes) y Usuarios: solo Administrador. Recetas: cualquier usuario activo | Cap. 1.7 asigna catálogos al Administrador; el recetario es compartido (Cap. 1.5) |
| D-10 | Duplicar una receta hace copia profunda, sin fotografías | Las fotos pertenecen a la elaboración original |
| D-11 | Una receta archivada sí puede escalarse | Escalar es solo lectura, no modifica nada |
| D-12 | Autenticación con JWT (`simplejwt`) | Front y back en dominios distintos (Vercel/Render): sin cookies de sesión |
| D-13 | Usuario identificado por correo, no username | El análisis no menciona nombre de usuario; el correo alcanza |
| D-14 | Fotos en Cloudinary, no en disco | El filesystem de Render es efímero: se perderían en cada deploy |
| D-15 | Guardar una receta reescribe sus preparaciones completas | Más simple y seguro que rastrear qué cambió; siempre dentro de la transacción |
| D-16 | El admin de Django expone recetas en solo lectura | Editarlas desde ahí saltearía las validaciones del Dominio |

---

## Etapas siguientes

- [x] **1 — Modelo del Dominio**
- [x] **2 — Casos de Uso** (capa de Aplicación)
- [x] **3 — Persistencia** (modelos Django + PostgreSQL + repositorios)
- [x] **4 — Interfaz** (API REST + React)
- [x] **5 — Pruebas** (192 en total)

---

## Puesta en marcha del repositorio

```bash
git init
git add .
git commit -m "Etapa 1: modelo del dominio"
git remote add origin <tu-repo-en-github>
git push -u origin main
```

Render y Vercel se conectan a ese repositorio y despliegan en cada `push`.
La configuración de ambos se agrega en la Etapa 3, cuando exista el proyecto
Django y algo que servir.

### Nota sobre trabajar solo en producción

Es viable, pero conviene tener presente que:

- Cada corrección exige un `push` y esperar el redeploy (1–3 minutos).
- Los errores los ve cualquier persona que use la app en ese momento.
- Las migraciones de base de datos aplicadas mal en producción son difíciles de
  revertir sin backup.

Una alternativa de bajo costo: activar **GitHub Actions** para que corra `pytest`
en cada `push`. Así los errores de dominio se detectan antes de desplegar, sin
que necesites instalar nada localmente. Te lo puedo dejar configurado.

---

## Casos de Uso implementados (Etapa 2)

La capa de Aplicación orquesta: autoriza → recupera el agregado → delega la regla
en el Dominio → confirma la transacción. **No contiene reglas de negocio.**

| Área | Casos de uso | RF |
|---|---|---|
| Recetas | Crear, Consultar, Editar, Archivar, Restaurar, Duplicar, MarcarFavorita | RF-005 a RF-010, RF-043 |
| Preparaciones | Gestionar (agregar, renombrar, eliminar, reordenar) | RF-011 a RF-014 |
| Ingredientes | GestionarIngredientesDePreparacion, GestionarCatalogoIngredientes | RF-015 a RF-018 |
| Pasos | GestionarPasos | RF-019 a RF-022 |
| Fotos y notas | GestionarFotografias, GestionarNotas | RF-023 a RF-026 |
| Organización | GestionarCategorias, GestionarEtiquetas, GestionarFuentes, AsignarClasificacion | RF-027 a RF-030 |
| Escalado | EscalarReceta | RF-031 a RF-033 |
| Lista de compras | GenerarListaCompras, CombinarListasCompras | RF-034 a RF-037 |
| Búsquedas | BuscarRecetas, ListarRecetas | RF-038 a RF-043 |
| Usuarios | GestionarUsuarios | RF-001 a RF-004 |

### Por qué existen los DTO

La Presentación nunca toca un agregado del Dominio. Los **Comandos** expresan la
intención del usuario y los **Resultados**, lo que la API devuelve. Están escritos
en tipos primitivos, así que serializarlos a JSON en DRF es directo y la API no
queda acoplada al modelo interno.

### Permisos (decisión D-9)

| Operación | Administrador | Usuario Familiar |
|---|---|---|
| Gestionar usuarios | Sí | No |
| Crear ingredientes, categorías, etiquetas, fuentes | Sí | No |
| Consultar catálogos | Sí | Sí |
| Crear, editar, archivar recetas | Sí | Sí |
| Escalar y generar listas | Sí | Sí |

Un usuario desactivado no puede ejecutar ninguna operación. El recetario es
compartido: cualquier usuario activo puede editar recetas creadas por otro
(Cap. 1.5).

---

## Bug encontrado y corregido durante esta etapa

Las pruebas del flujo completo detectaron que `Decimal.normalize()` expresa los
enteros grandes en notación científica: al escalar 500 g al triple, el resultado
se mostraba como **`1E+3 g`** en lugar de `1000 g`.

Corregido en `Cantidad._normalizar`, con dos pruebas de regresión. Es exactamente
el tipo de error que sólo aparece al ejercitar el recorrido de punta a punta.

---

## Etapa 3: persistencia

### Modelo físico

13 tablas que respetan el modelo E-R del Cap. 7.3 y sus cardinalidades. Nombres
de tabla en Lenguaje Ubicuo (`receta`, `preparacion`, `ingrediente_preparacion`).

Restricciones declaradas en la base **además** de validarse en el Dominio, como
exige el Cap. 5.7: unicidad de nombres, un ingrediente no se repite dentro de una
preparación, y `PROTECT` en las claves foráneas de catálogo (no se puede borrar un
ingrediente que alguna receta usa).

RN-005 (máximo 3 fotos por receta) **no** puede expresarse como restricción de
tabla, porque abarca todas las preparaciones de la receta. Vive en el Dominio.

### Cómo se guarda el agregado

`guardar()` reescribe las preparaciones completas: borra las que ya no están y
hace `update_or_create` del resto, todo dentro de la transacción. Es más simple
que rastrear qué componente cambió y garantiza que lo almacenado coincida
exactamente con el agregado en memoria.

La lectura usa `prefetch_related` para traer receta, preparaciones, ingredientes,
pasos, fotos, categorías, etiquetas y notas **sin el problema N+1**.

### La búsqueda se traduce a SQL

`BuscadorRecetas` (Dominio) define qué significa cada criterio; el repositorio lo
expresa como `QuerySet` para no traer el recetario entero a memoria. La regla vive
en un solo lugar, la eficiencia en el otro.

### Transacciones

`UnidadDeTrabajoDjango` envuelve cada caso de uso en `transaction.atomic`. Si algo
falla, se revierte todo: una receta inválida nunca queda a medio guardar. Hay una
prueba que lo verifica provocando un error a propósito.
