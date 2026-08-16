# Documentación técnica — SGRF

Sistema de Gestión de Recetas Familiares. Implementación de la especificación
**SGRF-EIS-001** (capítulos 1 a 7) siguiendo `PROMPT_CODEX.md`.

---

## Índice

1. [Qué hace el sistema](#1-qué-hace-el-sistema)
2. [Arquitectura](#2-arquitectura)
3. [El dominio](#3-el-dominio)
4. [Casos de uso](#4-casos-de-uso)
5. [Persistencia](#5-persistencia)
6. [API REST](#6-api-rest)
7. [Interfaz](#7-interfaz)
8. [Pruebas](#8-pruebas)
9. [Trazabilidad](#9-trazabilidad)
10. [Decisiones tomadas](#10-decisiones-tomadas)
11. [Qué falta](#11-qué-falta)

---

## 1. Qué hace el sistema

Un recetario compartido por una familia. Permite guardar recetas divididas en
preparaciones, buscarlas, **escalarlas a cualquier rendimiento sin alterar la
receta original**, y generar listas de compras con lo que falta.

El recorrido principal (Cap. 6.8) es:

```
buscar → abrir → elegir rendimiento → escalar → marcar faltantes → lista → cocinar
```

### La regla que ordena todo el diseño

**RN-004: la receta base nunca se modifica.**

Es el activo del sistema: la receta como la escribió la abuela. Escalar produce
un cálculo temporal que se muestra y se descarta. Nada de eso se guarda.

Tres mecanismos independientes lo garantizan:

1. `Cantidad` es un `dataclass(frozen=True)`: es imposible mutarla.
2. `EscaladorRecetas` sólo lee la receta; construye estructuras nuevas.
3. El resultado es `RecetaEscalada`, un **tipo distinto** de `Receta`, inmutable,
   que sólo guarda el `id` de origen. No existe repositorio capaz de
   persistirlo.

Hay pruebas en las cuatro capas que lo verifican, incluso escalando a 100
porciones contra la base de datos real.

---

## 2. Arquitectura

Clean Architecture en cinco capas. Cada una depende sólo de la de adentro.

```
┌─────────────────────────────────────────────┐
│  Presentación   React + DRF                 │
│  ┌───────────────────────────────────────┐  │
│  │  Aplicación   Casos de uso, DTO       │  │
│  │  ┌─────────────────────────────────┐  │  │
│  │  │  Dominio                        │  │  │
│  │  │  Entidades, objetos de valor,   │  │  │
│  │  │  servicios, interfaces          │  │  │
│  │  └─────────────────────────────────┘  │  │
│  └───────────────────────────────────────┘  │
│                                             │
│  Infraestructura   Django ORM, PostgreSQL   │
└─────────────────────────────────────────────┘
```

**El dominio no importa Django.** Usa sólo la biblioteca estándar de Python.
Esto no es purismo: es lo que permite que 139 pruebas corran en segundos sin
levantar el framework ni tocar una base de datos.

La inversión de dependencias se hace con interfaces de repositorio: el dominio
declara *qué* necesita persistir, la infraestructura decide *cómo*.

### Estructura de carpetas

```
sgrf/
├── backend/
│   ├── config/                    settings, urls, wsgi
│   ├── manage.py
│   ├── requirements.txt
│   ├── build.sh                   lo ejecuta Render en cada deploy
│   ├── src/sgrf/
│   │   ├── dominio/
│   │   │   ├── excepciones.py
│   │   │   ├── objetos_valor/     Cantidad, Unidad, Rendimiento, TipoEscalado
│   │   │   ├── entidades/         Receta (raíz), Preparacion, catálogo…
│   │   │   ├── servicios/         Escalador, GeneradorLista, Buscador, Validador
│   │   │   └── repositorios/      interfaces (contratos)
│   │   ├── aplicacion/
│   │   │   ├── dto.py             comandos y resultados
│   │   │   ├── ensambladores.py   dominio ↔ DTO
│   │   │   ├── autorizacion.py    permisos por perfil
│   │   │   ├── unidad_de_trabajo.py
│   │   │   └── casos_uso/         24 casos de uso
│   │   ├── infraestructura/
│   │   │   ├── recetario/         modelos Django, migración, admin
│   │   │   └── persistencia/      repositorios, mapeadores, UnitOfWork
│   │   └── presentacion/api/      serializadores, vistas, rutas
│   └── tests/
│       ├── dominio/               79 pruebas
│       ├── aplicacion/            60 pruebas
│       ├── infraestructura/       16 pruebas (requieren BD)
│       └── presentacion/          26 pruebas (requieren BD)
├── frontend/
│   ├── src/
│   │   ├── api/                   cliente HTTP y tipos
│   │   ├── contexto/              autenticación
│   │   ├── componentes/           piezas compartidas
│   │   └── paginas/               Ingresar, Recetas, Detalle, Nueva, Lista
│   └── tailwind.config.js         identidad visual del Cap. 6.4
├── docs/                          los 7 capítulos del análisis
└── render.yaml                    infraestructura de Render
```

---

## 3. El dominio

### Lenguaje ubicuo

Los nombres del análisis se usan tal cual, en español, en todo el código:
`Receta`, `Preparacion`, `IngredientePreparacion`, `Fuente`, `Rendimiento`.
Nunca `Recipe` ni `CookingStep`. Alcanza también a las tablas de la base y a
las rutas de la API (`/api/recetas/`).

### Objetos de valor

| Objeto | Qué representa | Detalle |
|---|---|---|
| `Cantidad` | Valor + unidad | Inmutable. Usa `Decimal`, nunca `float` |
| `Unidad` | Unidad de medida | No convierte entre unidades |
| `Rendimiento` | Cuánto produce | Sólo escala entre rendimientos iguales |
| `TipoEscalado` | Cómo se comporta al escalar | Lineal, fijo, a gusto, cantidad necesaria |

**Por qué `Decimal` y no `float`:** en coma flotante, `0.1 + 0.2` da
`0.30000000000000004`. En una receta eso es inaceptable. Hay una prueba que lo
verifica.

### Los cuatro tipos de escalado

| Tipo | Al escalar | Ejemplo |
|---|---|---|
| **Lineal** | Se multiplica por el factor | 500 g de harina → 1000 g al doble |
| **Fijo** | No cambia | La levadura no acompaña proporcionalmente |
| **A gusto** | Sin cantidad numérica | Sal a gusto |
| **Cantidad necesaria** | Sin cantidad numérica | Harina para estirar |

Los dos últimos se definen justamente por la ausencia de cantidad, así que el
dominio rechaza que la lleven.

### La receta como raíz de agregado

`Receta` es Aggregate Root (ADR-001): toda modificación pasa por ella. No se
puede guardar una `Preparacion` suelta.

Esto no es una formalidad. **RN-005** (máximo 2 fotos de proceso y 1 final) lo
demuestra: el Cap. 3.9 asocia las fotos a la preparación, pero el límite es por
receta. Sólo la raíz ve todas las preparaciones a la vez, así que sólo ella
puede hacerla cumplir. Es también la razón por la que esa regla **no puede** ser
una restricción de tabla.

### Servicios de dominio

| Servicio | Responsabilidad |
|---|---|
| `EscaladorRecetas` | Calcula cantidades para un rendimiento nuevo |
| `GeneradorListaCompras` | Consolida los ingredientes seleccionados |
| `BuscadorRecetas` | Define qué significa cada criterio de búsqueda |
| `ValidadorRecetas` | Audita una receta completa y devuelve todos los incumplimientos |

`ValidadorRecetas` existe aunque las entidades ya impidan estados inválidos:
sirve para revisar una receta entera antes de guardarla y producir un informe
legible en lugar de detenerse en el primer problema.

### Consolidación de la lista de compras

Se agrupa por **(ingrediente, unidad, tipo de escalado)**. No se convierte entre
unidades: sumar 200 g de harina con 100 ml de otra cosa requeriría conocer la
densidad, y el análisis dice "mantener unidades". Si una receta usa el mismo
ingrediente en gramos y en mililitros, aparecen como dos renglones.

---

## 4. Casos de uso

La capa de aplicación orquesta: **autoriza → recupera el agregado → delega la
regla en el dominio → confirma la transacción.** No contiene reglas de negocio.

| Área | Casos de uso | RF |
|---|---|---|
| Recetas | Crear, Consultar, Editar, Archivar, Restaurar, Duplicar, MarcarFavorita | RF-005 a RF-010, RF-043 |
| Preparaciones | Gestionar (agregar, renombrar, eliminar, reordenar) | RF-011 a RF-014 |
| Ingredientes | GestionarIngredientesDePreparacion, GestionarCatalogoIngredientes | RF-015 a RF-018 |
| Pasos | GestionarPasos | RF-019 a RF-022 |
| Fotos y notas | GestionarFotografias, GestionarNotas | RF-023 a RF-026 |
| Organización | Categorías, Etiquetas, Fuentes, AsignarClasificacion | RF-027 a RF-030 |
| Escalado | EscalarReceta | RF-031 a RF-033 |
| Lista de compras | GenerarListaCompras, ListarListasCompras, Combinar | RF-034 a RF-037 |
| Búsquedas | BuscarRecetas, ListarRecetas | RF-038 a RF-043 |
| Usuarios | GestionarUsuarios | RF-001 a RF-004 |

### Por qué existen los DTO

La presentación nunca toca un agregado del dominio. Los **comandos** expresan la
intención del usuario; los **resultados**, lo que devuelve la API. Están escritos
en tipos primitivos, así que serializarlos es directo y la API no queda acoplada
al modelo interno.

### Permisos

Cap. 1.7 define dos perfiles. La lectura que hace el sistema:

| Operación | Administrador | Usuario Familiar |
|---|---|---|
| Gestionar usuarios | Sí | No |
| Crear ingredientes | Sí | Sí (decisión D-19) |
| Crear categorías, etiquetas, fuentes | Sí | No |
| Consultar catálogos | Sí | Sí |
| Crear, editar, archivar recetas | Sí | Sí |
| Escalar y generar listas | Sí | Sí |

Un usuario desactivado no puede hacer nada. El recetario es compartido: cualquier
usuario activo puede editar recetas creadas por otro (Cap. 1.5). Las listas de
compras, en cambio, son personales.

### Transacciones

`UnidadDeTrabajo` agrupa los repositorios y delimita la transacción. La
implementación de Django usa `transaction.atomic`: si algo falla, se revierte
todo. Una receta inválida nunca queda a medio guardar.

---

## 5. Persistencia

13 tablas que respetan el modelo E-R del Cap. 7.3 y sus cardinalidades, con
nombres en lenguaje ubicuo (`receta`, `preparacion`, `ingrediente_preparacion`).

### Restricciones en la base

Cap. 5.7 pide declararlas también en la base, no sólo en el dominio:

- Nombres únicos de receta, ingrediente, etiqueta y fuente
- Un ingrediente no se repite dentro de una preparación
- `PROTECT` en las claves foráneas de catálogo: no se puede borrar un
  ingrediente que alguna receta usa
- `CASCADE` en los componentes internos del agregado: una preparación no tiene
  sentido sin su receta

### Cómo se guarda el agregado

`guardar()` reescribe las preparaciones completas: borra las que ya no están y
hace `update_or_create` del resto, todo dentro de la transacción. Es más simple
que rastrear qué cambió y garantiza que lo almacenado coincida exactamente con
el agregado en memoria.

La lectura usa `prefetch_related` para traer todo el agregado sin el problema
N+1.

### La búsqueda se traduce a SQL

`BuscadorRecetas` (dominio) define qué significa cada criterio; el repositorio lo
expresa como `QuerySet` para no traer el recetario entero a memoria. La regla
vive en un solo lugar, la eficiencia en el otro.

---

## 6. API REST

Base: `https://tu-backend.onrender.com/api`

Autenticación JWT: el token va en `Authorization: Bearer <token>`.

### Autenticación

| Método | Ruta | Qué hace |
|---|---|---|
| POST | `/auth/token/` | Devuelve `access` y `refresh` |
| POST | `/auth/refrescar/` | Renueva el `access` |
| GET | `/perfil/` | Datos del usuario en sesión |

### Recetas

| Método | Ruta | Qué hace |
|---|---|---|
| GET | `/recetas/` | Lista o busca |
| POST | `/recetas/` | Crea |
| GET | `/recetas/{id}/` | Devuelve completa |
| PATCH | `/recetas/{id}/` | Edita datos generales |
| POST | `/recetas/{id}/archivar/` | Archiva |
| DELETE | `/recetas/{id}/archivar/` | Restaura |
| POST | `/recetas/{id}/duplicar/` | Crea una variante |
| POST | `/recetas/{id}/favorita/` | Marca o desmarca |
| POST | `/recetas/{id}/escalar/` | Calcula un rendimiento nuevo |
| POST | `/recetas/{id}/lista-compras/` | Genera la lista |

Parámetros de búsqueda: `texto`, `ingrediente_id`, `categoria_id`,
`etiqueta_id`, `fuente_id`, `solo_favoritas`, `incluir_archivadas`.

`/escalar/` usa POST porque recibe un cuerpo, pero **no modifica nada**.

### Componentes de una receta

Se anidan bajo ella, reflejando que el agregado es la unidad de acceso:

```
/recetas/{id}/preparaciones/
/recetas/{id}/preparaciones/{id}/ingredientes/
/recetas/{id}/preparaciones/{id}/pasos/
/recetas/{id}/preparaciones/{id}/fotografias/
/recetas/{id}/notas/
```

### Catálogos

`/ingredientes/`, `/categorias/`, `/etiquetas/`, `/fuentes/`, `/usuarios/`

GET para cualquier usuario activo; POST sólo para el administrador.

### Códigos de error

Cada excepción del negocio tiene un código HTTP:

| Situación | Código | Ejemplo |
|---|---|---|
| Datos mal formados | 400 | Rendimiento no numérico |
| Sin permisos | 403 | Familiar creando ingredientes |
| No existe | 404 | Receta inexistente |
| Conflicto | 409 | Nombre duplicado, receta archivada |
| Regla de negocio | 422 | Receta sin preparaciones, cuarta foto |

El 422 incluye el código de la regla:

```json
{
  "error": "[RN-005] La receta admite como máximo 2 fotografía(s) de tipo 'proceso'.",
  "regla": "RN-005"
}
```

### Las cantidades viajan como texto

`"cantidad": "500"`, no `"cantidad": 500`. JavaScript no tiene decimales
exactos: convertir a `float` reintroduciría el error que `Decimal` evita en el
backend. El front las muestra tal cual y delega toda la aritmética al servidor.

---

## 7. Interfaz

React + TypeScript + Tailwind, desplegada en Vercel.

### Identidad visual

El Cap. 6.4 la fija y se sigue al pie de la letra: azul francia principal,
blanco secundario, verde/amarillo/rojo para estados, sans serif de 16 px base.
Los tokens están en `tailwind.config.js` con nombres del lenguaje ubicuo, de
modo que una clase se lea igual que la especificación.

### Decisiones de interfaz

**El control de rendimiento es lo primero que se ve al abrir una receta.** Es la
acción central del sistema y el Cap. 6.12 pide que Escalar sea visible.

**Las cantidades usan tipografía mayor que los nombres de ingrediente.** Se leen
cocinando, muchas veces a distancia. El Cap. 6.12 pide que los ingredientes
tengan más protagonismo que los datos administrativos.

**Escalar avisa que la receta no cambia.** Cuando el rendimiento difiere del
base, aparece una barra que lo aclara y ofrece volver al original. La regla más
importante del sistema no debería ser un supuesto invisible.

**La navegación baja al pie en teléfonos**, donde el pulgar la alcanza.

**Los ingredientes se marcan tocando toda la fila**, no sólo la casilla: el
objetivo es usarlo con las manos ocupadas.

### Pantallas

| Pantalla | Qué resuelve |
|---|---|
| Ingresar | Acceso con correo y contraseña |
| Recetas / Favoritas | Listado y búsqueda |
| Nueva receta | Alta completa en un formulario |
| Detalle | Escalado, marcado de faltantes, lista de compras |
| Editar | Preparaciones, ingredientes, pasos, fotos, notas y clasificación |
| Lista de compras | Lo pendiente de todas las listas |
| Administración | Catálogos y usuarios (sólo administrador) |

### Alta y edición funcionan distinto

El **alta** junta todo y guarda una sola vez: la receta no existe hasta que está
completa, y `ValidadorRecetas` la revisa entera antes de persistirla.

La **edición** guarda cada cambio por separado. Editar una receta cargada es una
tarea de a ratos —se corrige un paso, se ajusta una cantidad—, y perder todo por
cerrar la pestaña sería peor que la molestia de no tener un botón único.

### Reordenar con flechas, no arrastrando

Reordenar preparaciones y pasos usa flechas arriba/abajo en lugar de arrastrar y
soltar. Arrastrar sería más vistoso, pero no funciona con teclado ni con lector
de pantalla, y en un teléfono compite con el desplazamiento vertical de la
página. El Cap. 6.9 pide accesibilidad y el 6.10 prioriza el móvil.

### Subida de fotografías

El archivo va **directo del navegador a Cloudinary**, con una firma que emite el
backend (`POST /api/fotografias/firma/`). Dos motivos: la imagen no atraviesa
Render, cuyo plan gratuito tiene poca memoria, y el secreto de la cuenta nunca
sale del servidor. La firma caduca a la hora y limita carpeta y formato, así que
no puede reutilizarse para subir cualquier cosa.

La pantalla oculta los tipos de foto ya ocupados para no ofrecer algo que el
dominio va a rechazar por RN-005.

### Manejo de sesión

El cliente refresca el token automáticamente una vez ante un 401 y reintenta. Un
segundo fallo significa que la sesión terminó de verdad.

---

## 8. Pruebas

| Capa | Pruebas | Necesita BD | Cubre |
|---|---|---|---|
| Dominio | 79 | No | Objetos de valor, agregado, servicios |
| Aplicación | 60 | No | Casos de uso, permisos, transacciones |
| Infraestructura | 15 | Sí | Ida y vuelta contra PostgreSQL |
| Presentación | 38 | Sí | Contrato HTTP, códigos de error |

**Total: 192 pruebas.**

```bash
cd backend
pytest                              # todo
pytest tests/dominio tests/aplicacion   # sin base de datos, segundos
```

Las pruebas de aplicación usan repositorios en memoria que implementan los
contratos del dominio. Que los casos de uso corran completos sin Django es la
verificación de que la arquitectura funciona.

### Integración continua

`.github/workflows/pruebas.yml` corre en cada push, en tres trabajos paralelos:
reglas del negocio (sin base de datos, segundos), persistencia y API (levanta
PostgreSQL) y compilación del front (verifica los tipos de TypeScript).

Existe porque el proyecto se trabaja directamente en producción: conviene
enterarse de un error antes del despliegue y no con la familia usando la
aplicación.

### Bugs encontrados por las pruebas

**Notación científica en las cantidades.** Las pruebas del flujo completo
detectaron que `Decimal.normalize()` expresa los enteros grandes en notación
científica: al escalar 500 g al triple, el resultado se mostraba como
**`1E+3 g`** en lugar de `1000 g`. Corregido en el momento, con pruebas de
regresión.

**El rendimiento se leía como miles.** Reportado en producción: una receta de
"50 porciones" se mostraba como "50000" en la tarjeta del listado. La causa:
PostgreSQL devuelve siempre la precisión completa de la columna
(`decimal_places=3`), así que un rendimiento guardado como 50 vuelve de la base
como `Decimal('50.000')`. El dato interno era correcto, pero en formato
argentino el punto es separador de miles — "50.000" se lee como cincuenta mil.

El arreglo de notación científica se había aplicado únicamente a `Cantidad`,
nunca a `Rendimiento`, que es donde vivía este caso. Ahora ambos comparten la
misma normalización (`objetos_valor/_decimal.py`), así que la corrección no
puede volver a aplicarse de un lado y olvidarse del otro.

Ninguna prueba existente lo había detectado porque comparaba con `==`, y
`Decimal("4") == Decimal("4.000")` da `True` en Python: la igualdad ignora los
ceros de más. El problema era exclusivamente de **texto mostrado**. Se agregaron
pruebas que comparan `str()` en las tres capas — dominio, persistencia y API —
para que un problema de visualización no vuelva a esconderse detrás de una
comparación numérica que no lo detecta.

**`CLOUDINARY_URL` con el correo pegado en vez del nombre de cuenta.** Reportado
en producción: la subida de fotos fallaba con un error de CORS apuntando a
`api.cloudinary.com/v1_1/gmail.com/...`. La causa: el valor de la variable tenía
dos `@` en vez de uno (se había pegado el correo de la cuenta donde iba el
"Cloud name" del Dashboard), y la biblioteca de Cloudinary toma todo lo que
sigue al último `@` como nombre de cuenta — en este caso, `gmail.com`.

La primera versión de la validación sólo chequeaba el prefijo `cloudinary://`,
así que no detectaba este caso: el valor mal armado igual empezaba bien. Se
extrajo la validación a `config/validacion_cloudinary.py`, con una función pura
testeable sin Django, que ahora también verifica que haya un único `@` y que
existan las dos partes separadas por `:` (clave y secreto). Cinco pruebas en
`tests/config/` cubren el formato correcto y los errores más frecuentes,
incluido este exacto.

---

## 9. Trazabilidad

### Reglas de negocio

| Regla | Enunciado | Dónde se garantiza |
|---|---|---|
| RN-001 | Rendimiento base único | `Receta.__post_init__`, `Rendimiento` |
| RN-002 | Fuente única y obligatoria | `Receta.__post_init__`, `CrearReceta` |
| RN-003 | Una o más preparaciones | `Receta.quitar_preparacion`, `ValidadorRecetas` |
| RN-004 | La receta base nunca se modifica | `Cantidad` inmutable + `RecetaEscalada` |
| RN-005 | Máx. 2 fotos proceso + 1 final | `Receta._validar_limite_fotografias` |
| RN-006 | Lista sólo con lo seleccionado | `GeneradorListaCompras.generar` |

### Requisitos funcionales

Los 43 RF del Cap. 4, con dónde se resuelve cada uno en la interfaz:

| RF | Requisito | Pantalla |
|---|---|---|
| RF-001 a RF-004 | Gestión de usuarios | Administración › Familia |
| RF-005 | Crear receta | Nueva receta |
| RF-006 | Editar información general | Editar › Datos generales |
| RF-007 | Consultar receta | Detalle |
| RF-008 / RF-009 | Archivar y restaurar | Detalle / Editar |
| RF-010 | Duplicar | Detalle › Duplicar |
| RF-011 a RF-013 | Agregar, modificar, eliminar preparaciones | Editar |
| RF-014 | Reordenar preparaciones | Editar › flechas |
| RF-015 | Catálogo de ingredientes | Administración › Ingredientes |
| RF-016 a RF-018 | Ingredientes de una preparación | Editar |
| RF-019 a RF-021 | Agregar, modificar, eliminar pasos | Editar |
| RF-022 | Reordenar pasos | Editar › flechas |
| RF-023 / RF-024 | Fotografías | Editar › subida a Cloudinary |
| RF-025 / RF-026 | Notas | Editar › Notas |
| RF-027 / RF-028 | Asignar categorías y etiquetas | Editar › Clasificación |
| RF-029 / RF-030 | Administrar categorías y fuentes | Administración |
| RF-031 a RF-033 | Escalado | Detalle › control de rendimiento |
| RF-034 / RF-035 | Lista de compras | Detalle › Armar lista |
| RF-036 | Ver en el móvil | Diseño responsive |
| RF-037 | Compartir o imprimir | **Diferido por el análisis** a versiones futuras |
| RF-038 | Buscar por nombre | Recetas |
| RF-039 a RF-042 | Buscar por ingrediente, categoría, etiqueta, fuente | Recetas › Más filtros |
| RF-043 | Filtrar favoritas y archivadas | Recetas / Favoritas |

RF-037 es el único sin implementar, y por indicación del propio análisis
(Cap. 4.10: "en futuras versiones").

### Decisiones arquitectónicas

| ADR | Enunciado | Dónde se ve |
|---|---|---|
| ADR-001 | La Receta es Aggregate Root | Todo pasa por `Receta` |
| ADR-002 | La Preparación es la unidad funcional | Estructura de la entidad y de la UI |
| ADR-003 | El escalado no persiste | `RecetaEscalada` sin repositorio |
| ADR-004 | Ingredientes en catálogo reutilizable | `IngredienteRepositorio` |
| ADR-005 | Documentación independiente de la tecnología | El dominio no importa Django |

---

## 10. Decisiones tomadas

Estas resuelven puntos que el análisis no detalla. Se documentan porque
`PROMPT_CODEX.md` prohíbe inventar reglas: **conviene revisarlas y confirmarlas.**

| # | Decisión | Razón |
|---|---|---|
| D-1 | "A gusto" y "cantidad necesaria" no llevan cantidad | Se definen por la ausencia de cantidad |
| D-2 | La lista consolida por (ingrediente, unidad) | El análisis dice "mantener unidades" |
| D-3 | "Fijo" conserva la cantidad al escalar | Interpretación literal del término |
| D-4 | Receta archivada no se edita hasta restaurarla | Preserva el valor del archivado |
| D-5 | El límite de fotos se valida en `Receta` | Cap. 3.9 las asocia a Preparación, RN-005 fija el límite por Receta |
| D-6 | `Rendimiento` sólo escala entre iguales | Evita convertir "4 porciones" en "8 tortas" |
| D-7 | Un ingrediente no se repite en una preparación | Mitiga duplicados (Cap. 2.11) |
| D-8 | `Decimal`, nunca `float` | Precisión en las cantidades |
| D-9 | Catálogos y usuarios: sólo administrador | Cap. 1.7; el recetario es compartido (Cap. 1.5) |
| D-10 | Duplicar hace copia profunda, sin fotos | Las fotos son de la elaboración original |
| D-11 | Una receta archivada sí puede escalarse | Escalar es sólo lectura |
| D-12 | JWT para autenticación | Front y back en dominios distintos |
| D-13 | Usuario identificado por correo | El análisis no menciona nombre de usuario |
| D-14 | Fotos en Cloudinary | El disco de Render es efímero |
| D-15 | Guardar reescribe las preparaciones | Más simple y seguro que rastrear cambios |
| D-16 | Admin de Django: recetas en sólo lectura | Editarlas ahí saltearía las validaciones |
| D-17 | El marcado de "comprado" no se persiste | El análisis no lo pide |
| D-18 | Las listas de compras son personales | Cap. 1.5 comparte el recetario, no las listas |
| D-19 | Cualquier usuario activo crea ingredientes; categorías y fuentes siguen siendo del administrador | Evita que cargar una receta dependa de un tercero; el resto de los catálogos define la clasificación de todo el recetario |

---

## 11. Qué falta

El alcance de la versión 1.0 está completo. Quedan sin implementar únicamente
funciones que el propio análisis difiere:

### Diferido por el propio análisis

Cap. 7.7: exportación y mejoras de búsqueda en la 1.1; OCR, IA, temporizadores e
importación automática en la 2.0.

La arquitectura los admite sin tocar el dominio, que es lo que pide el Cap. 5.11.

---

## Cómo seguir trabajando

Al agregar una funcionalidad, el orden es el mismo que se usó acá:

1. **Dominio** primero: ¿hay una regla nueva? Va en la entidad o el servicio,
   con pruebas.
2. **Caso de uso**: orquesta, no decide.
3. **Persistencia**: si aparece un dato nuevo, modelo y migración.
4. **API**: serializador de entrada, vista, ruta.
5. **Front**: tipo en TypeScript, llamada, pantalla.

Ante una contradicción o ambigüedad del análisis: **detenerse, explicar, proponer
y esperar confirmación.** No inventar reglas.
