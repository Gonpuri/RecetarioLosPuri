# Tutorial de despliegue — SGRF

Guía paso a paso para poner el Sistema de Gestión de Recetas Familiares en
producción. Backend en **Render**, front en **Vercel**, base de datos
**PostgreSQL**, fotografías en **Cloudinary**.

No hace falta instalar nada en tu computadora salvo Git.

---

## Índice

1. [Antes de empezar](#1-antes-de-empezar)
2. [Subir el proyecto a GitHub](#2-subir-el-proyecto-a-github)
3. [Desplegar el backend en Render](#3-desplegar-el-backend-en-render)
4. [Configurar Cloudinary](#4-configurar-cloudinary)
5. [Desplegar el front en Vercel](#5-desplegar-el-front-en-vercel)
6. [Conectar las dos puntas](#6-conectar-las-dos-puntas)
7. [Primera carga de datos](#7-primera-carga-de-datos)
8. [Verificación final](#8-verificación-final)
9. [Trabajo diario](#9-trabajo-diario)
10. [Problemas frecuentes](#10-problemas-frecuentes)

---

## 1. Antes de empezar

Necesitás cuentas gratuitas en:

| Servicio | Para qué | Dirección |
|---|---|---|
| GitHub | Guardar el código | github.com |
| Render | Backend + base de datos | render.com |
| Vercel | Front | vercel.com |
| Cloudinary | Fotografías | cloudinary.com |

Creá las cuatro antes de seguir. En las tres últimas conviene registrarse
**con la cuenta de GitHub**: así quedan conectadas solas.

### Dos advertencias del plan gratuito de Render

Leelas ahora, no después:

- **El backend se duerme a los 15 minutos sin uso.** La primera visita después
  tarda unos 50 segundos en responder. Es el comportamiento normal del plan
  gratuito, no un error.
- **La base de datos vence a los 90 días.** Anotá la fecha en el calendario.
  Antes de que venza tenés que hacer backup o pasar al plan pago (unos USD 7 por
  mes). Si vence sin backup, se pierden los datos.

---

## 2. Subir el proyecto a GitHub

### 2.1 Crear el repositorio

En GitHub: **New repository** → nombre `sgrf` → **Private** → **Create**.

No marques ninguna casilla de inicialización (ni README ni .gitignore): el
proyecto ya los trae.

### 2.2 Subir el código

Descomprimí el ZIP del proyecto y desde esa carpeta:

```bash
cd sgrf
git init
git add .
git commit -m "SGRF: versión inicial"
git branch -M main
git remote add origin https://github.com/TU-USUARIO/sgrf.git
git push -u origin main
```

Reemplazá `TU-USUARIO` por tu nombre de usuario de GitHub. Si te pide
contraseña, GitHub ya no acepta la de la cuenta: generá un token en
**Settings → Developer settings → Personal access tokens** y usalo como
contraseña.

---

## 3. Desplegar el backend en Render

### 3.1 Crear el Blueprint

El archivo `render.yaml` describe toda la infraestructura, así que Render la
arma sola.

1. En Render: **New +** → **Blueprint**
2. **Connect a repository** → elegí `sgrf`
3. Render lee `render.yaml` y muestra dos servicios:
   - `sgrf-postgres` — la base de datos
   - `sgrf-backend` — la aplicación
4. **Apply**

El primer despliegue tarda entre 3 y 5 minutos. Va a **fallar**, y está bien:
todavía faltan las variables de entorno.

### 3.2 Cargar las variables de entorno

Entrá al servicio `sgrf-backend` en Render y buscá la sección **Environment**.
En la mayoría de las vistas está en la barra lateral izquierda del servicio; si
no aparece, entrá en **Settings** y luego en **Environment Variables** o
**Environment** según la interfaz.

Luego hacé clic en **Add Environment Variable**.

Agregá estas cinco:

| Clave | Valor | Para qué |
|---|---|---|
| `ADMIN_CORREO` | tu correo | Tu usuario administrador |
| `ADMIN_CLAVE` | una clave de 8+ caracteres | Tu contraseña |
| `ADMIN_NOMBRE` | tu nombre | Cómo te muestra el sistema |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:5173` | Provisorio, se corrige en el paso 6 |
| `CSRF_TRUSTED_ORIGINS` | `http://localhost:5173` | Provisorio, se corrige en el paso 6 |

`SECRET_KEY` y `DATABASE_URL` ya están cargadas: las generó Render.

**Guardá el correo y la clave del administrador.** Son tu acceso al sistema.

### 3.3 Volver a desplegar

**Manual Deploy** → **Deploy latest commit**.

Mirá los logs. Al final tendrían que aparecer:

```
Running migrations: ... OK
Administrador tu-correo@ejemplo.com creado.
Build successful
```

### 3.4 Comprobar que anda

Copiá la dirección de tu servicio (arriba de todo, algo como
`https://sgrf-backend.onrender.com`) y abrila con `/api/estado/` al final:

```
https://sgrf-backend.onrender.com/api/estado/
```

Tiene que responder:

```json
{"estado": "operativo", "sistema": "SGRF", "version": "0.1.0"}
```

**Anotá esa dirección**, la necesitás en el paso 5.

---

## 4. Configurar Cloudinary

Las fotos no pueden guardarse en Render: su disco se borra en cada
despliegue.

1. Entrá a cloudinary.com → **Dashboard**
2. Buscá **API Environment variable**, que se ve así:
   `cloudinary://123456789:abcdef@tu-cuenta`
3. Copiala completa
4. En Render → `sgrf-backend` → **Environment** → agregá:

| Clave | Valor |
|---|---|
| `CLOUDINARY_URL` | lo que copiaste |

---

## 5. Desplegar el front en Vercel

1. En Vercel: **Add New** → **Project**
2. **Import** el repositorio `sgrf`
3. Configurá:

| Campo | Valor |
|---|---|
| Framework Preset | Vite |
| Root Directory | `frontend` |
| Build Command | `npm run build` |
| Output Directory | `dist` |

**El Root Directory es lo que más se olvida.** Tiene que decir `frontend`, no
quedar vacío.

4. Abrí **Environment Variables** y agregá:

| Clave | Valor |
|---|---|
| `VITE_API_URL` | `https://sgrf-backend.onrender.com/api` |

Usá tu dirección real de Render, y **terminala en `/api`**.

5. **Deploy**

Al terminar, Vercel te da una dirección como `https://sgrf.vercel.app`.
**Anotala.**

---

## 6. Conectar las dos puntas

El navegador bloquea las llamadas entre dominios distintos salvo que el
backend las autorice. Hay que decirle a Render cuál es el front.

En Render → `sgrf-backend` → **Environment**, corregí las dos variables
provisorias del paso 3.2:

| Clave | Valor |
|---|---|
| `CORS_ALLOWED_ORIGINS` | `https://sgrf.vercel.app` |
| `CSRF_TRUSTED_ORIGINS` | `https://sgrf.vercel.app` |

Sin barra al final. Con tu dirección real de Vercel.

Guardá: Render vuelve a desplegar solo.

---

## 7. Primera carga de datos

El recetario arranca vacío. Antes de cargar recetas hacen falta al menos una
**fuente** y algunos **ingredientes**, porque toda receta necesita una fuente
(RN-002) y sus ingredientes salen de un catálogo compartido.

Entrá a tu aplicación en Vercel con el correo y la clave del paso 3.2, y abrí
**Administrar** en el menú. Esa sección sólo la ve el administrador.

> También existe el panel de Django en `/admin/` del backend, útil si algún día
> el front no está disponible.

### 7.1 Cargar fuentes

Pestaña **Fuentes**. Por ejemplo:

- Cuaderno de la abuela
- Recetas de mamá
- Internet

### 7.2 Cargar ingredientes

Pestaña **Ingredientes**. Cargá los que más usás:

Harina 000 · Azúcar · Sal fina · Aceite · Huevos · Leche · Manteca · Levadura

No hace falta cargarlos todos ahora: se pueden agregar en cualquier momento.

### 7.3 Cargar categorías (opcional)

Pestaña **Categorías**: Panadería, Pastas, Postres, Guisos.

Para crear una subcategoría, elegí una categoría padre.

### 7.4 Sumar a la familia

Pestaña **Familia**. Para cada integrante: nombre, correo, contraseña y rol.

Dejá **Usuario familiar** salvo para quien vaya a manejar los catálogos.

---

## 8. Verificación final

Entrá a `https://sgrf.vercel.app` y recorré el circuito completo:

- [ ] Ingresás con tu correo y clave
- [ ] Aparece la pantalla de recetas vacía
- [ ] **Nueva receta** muestra tus fuentes e ingredientes en las listas
- [ ] Cargás una receta con nombre, rendimiento, una preparación con
      ingredientes y pasos
- [ ] Al guardar se abre la receta
- [ ] Subís el rendimiento con **+** y las cantidades se recalculan
- [ ] Aparece el aviso "la receta guardada no cambia"
- [ ] **Volver al original** devuelve las cantidades base
- [ ] Marcás ingredientes y **Armar lista** genera la lista de compras
- [ ] La lista aparece también en **Lista de compras**
- [ ] **Editar** permite agregar un paso y un ingrediente
- [ ] Las flechas ▲▼ reordenan pasos y preparaciones
- [ ] **Cambiar** en un ingrediente actualiza la cantidad
- [ ] En **Clasificación** se asignan categorías y etiquetas
- [ ] Se sube una foto y aparece en la receta
- [ ] Al intentar una cuarta foto, avisa que llegaste al límite
- [ ] **Duplicar** crea una variante independiente
- [ ] **Más filtros** busca por ingrediente, categoría, etiqueta y fuente
- [ ] Desde el celular se ve bien y los botones se tocan cómodos

Si todo eso funciona, está desplegado.

---

## 9. Trabajo diario

### Publicar un cambio

```bash
git add .
git commit -m "Descripción del cambio"
git push
```

Render y Vercel despliegan solos. Render tarda 2 o 3 minutos; Vercel, menos de
uno.

### Revisar antes de publicar

Ya está configurado: `.github/workflows/pruebas.yml` corre solo en cada `push`.
No hay que hacer nada, salvo mirar el resultado.

Son tres trabajos en paralelo:

| Trabajo | Qué verifica | Tarda |
|---|---|---|
| Dominio y casos de uso | Las 139 pruebas sin base de datos | segundos |
| Persistencia y API | Las 53 restantes, contra PostgreSQL | ~1 minuto |
| Compilación del front | Que TypeScript compile sin errores | ~1 minuto |

Si algo falla, GitHub te marca el commit con una cruz roja. Render y Vercel
igual despliegan, así que **mirá el resultado antes de dar por bueno un
cambio.**

### Backup de la base de datos

**Hacelo antes del día 90.** En Render → `sgrf-postgres` → **Connect** copiá la
`External Database URL`, y desde cualquier máquina con PostgreSQL instalado:

```bash
pg_dump "LA-URL-EXTERNA" > respaldo-$(date +%Y-%m-%d).sql
```

Guardá ese archivo en un lugar seguro.

---

## 10. Problemas frecuentes

### "Failed to fetch" o "No se pudo conectar con el servidor"

Casi siempre es CORS. Revisá que `CORS_ALLOWED_ORIGINS` en Render tenga la
dirección **exacta** de Vercel: con `https://`, sin barra al final.

También puede ser que el backend esté dormido: esperá un minuto y recargá.

### La primera visita del día tarda muchísimo

Es el plan gratuito de Render. El servicio se duerme y tarda unos 50 segundos en
despertar. No es un error.

### "No se pudieron cargar los ingredientes y las fuentes"

Todavía no cargaste catálogos. Volvé al paso 7.

### "El almacenamiento de fotografías no está configurado"

Falta `CLOUDINARY_URL` en las variables de Render. Volvé al paso 4.

### La imagen no sube y el navegador muestra un error de Cloudinary

Revisá que el `CLOUDINARY_URL` esté completo, incluyendo `cloudinary://` al
principio y el nombre de cuenta al final. Se copia entero del Dashboard.

### El front muestra 404 al recargar una receta

Falta `vercel.json`, que redirige todas las rutas a la aplicación. Ya viene en
el proyecto: verificá que esté en `frontend/vercel.json` y que hayas subido todo.

### El build de Vercel falla

Casi siempre el **Root Directory** quedó vacío. Tiene que decir `frontend`.
Se corrige en **Settings** → **General** → **Root Directory**.

### El build de Render falla con "no such file or directory: ./build.sh"

Git no conservó el permiso de ejecución. Desde la carpeta del proyecto:

```bash
git update-index --chmod=+x backend/build.sh
git commit -m "Permiso de ejecución para build.sh"
git push
```

### Django dice que hay migraciones pendientes

La migración inicial se escribió a mano, así que puede haber alguna diferencia
menor. No rompe nada en funcionamiento. Para resolverla, en Render →
`sgrf-backend` → **Shell**:

```bash
python manage.py makemigrations recetario
python manage.py migrate
```

Después copiá el archivo generado a tu repositorio y subilo.

### Olvidé la contraseña del administrador

En Render → `sgrf-backend` → **Shell**:

```bash
python manage.py changepassword tu-correo@ejemplo.com
```

### Necesito ver qué está fallando

Render → `sgrf-backend` → **Logs**. Ahí aparece cada petición y cualquier error.

Para más detalle, poné la variable `LOG_LEVEL` en `DEBUG` — pero **nunca**
pongas `DEBUG=True` en producción: expone información sensible.
