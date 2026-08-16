/**
 * Administración de catálogos y usuarios.
 *
 * Sólo accesible para el perfil Administrador (decisión D-9). Reemplaza al
 * panel de Django para las tareas cotidianas: cargar ingredientes y
 * fuentes es lo primero que hace falta para poder registrar recetas.
 *
 * Los elementos de catálogo no se eliminan: una receta cargada puede
 * depender de ellos, y la base lo impide con `PROTECT`. Los usuarios se
 * desactivan, nunca se borran (RF-003).
 */

import { useCallback, useEffect, useState } from "react";
import { Navigate } from "react-router-dom";

import { ErrorApi, pedir } from "../api/cliente";
import type { ElementoCatalogo, UsuarioResumen } from "../api/tipos";
import { Aviso, Cargando } from "../componentes/Comunes";
import { useAutenticacion } from "../contexto/Autenticacion";

type Seccion = "ingredientes" | "fuentes" | "categorias" | "etiquetas" | "usuarios";

const SECCIONES: { clave: Seccion; texto: string }[] = [
  { clave: "ingredientes", texto: "Ingredientes" },
  { clave: "fuentes", texto: "Fuentes" },
  { clave: "categorias", texto: "Categorías" },
  { clave: "etiquetas", texto: "Etiquetas" },
  { clave: "usuarios", texto: "Familia" },
];

export default function Administracion() {
  const { esAdministrador, cargando: cargandoPerfil } = useAutenticacion();
  const [seccion, setSeccion] = useState<Seccion>("ingredientes");

  if (cargandoPerfil) return <Cargando />;
  if (!esAdministrador) return <Navigate to="/recetas" replace />;

  return (
    <div className="space-y-5">
      <h1 className="text-2xl font-semibold tracking-tight">Administración</h1>

      <div className="flex flex-wrap gap-2" role="tablist">
        {SECCIONES.map((item) => (
          <button
            key={item.clave}
            type="button"
            role="tab"
            aria-selected={seccion === item.clave}
            onClick={() => setSeccion(item.clave)}
            className={`rounded-pieza px-4 py-2 text-sm font-medium transition-colors ${
              seccion === item.clave
                ? "bg-azul text-white"
                : "border border-borde bg-white text-tinta-suave hover:text-azul"
            }`}
          >
            {item.texto}
          </button>
        ))}
      </div>

      {seccion === "usuarios" ? <Familia /> : <Catalogo seccion={seccion} />}
    </div>
  );
}

/** Campos que pide cada catálogo además del nombre. */
const CAMPOS_EXTRA: Record<string, { clave: string; etiqueta: string } | null> = {
  ingredientes: { clave: "descripcion", etiqueta: "Descripción (opcional)" },
  fuentes: { clave: "detalle", etiqueta: "Detalle (opcional)" },
  categorias: null,
  etiquetas: null,
};

const AYUDA_CATALOGO: Record<string, string> = {
  ingredientes:
    "El catálogo compartido del que salen los ingredientes de las recetas. Las cantidades no se guardan acá.",
  fuentes: "De dónde viene cada receta. Toda receta necesita una.",
  categorias:
    "Organizá las recetas en categorías. Una categoría puede tener " +
    "subcategorías adentro: por ejemplo, 'Panadería' como categoría, y " +
    "'Panes dulces' como subcategoría dentro de ella.",
  etiquetas: "Clasificación transversal: sin gluten, rápido, de fiesta…",
};

function Catalogo({ seccion }: { seccion: Exclude<Seccion, "usuarios"> }) {
  const [elementos, setElementos] = useState<ElementoCatalogo[]>([]);
  const [nombre, setNombre] = useState("");
  const [extra, setExtra] = useState("");
  const [padreId, setPadreId] = useState("");
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const campoExtra = CAMPOS_EXTRA[seccion];

  const cargar = useCallback(async () => {
    setCargando(true);
    setError(null);
    try {
      setElementos(await pedir<ElementoCatalogo[]>(`/${seccion}/`));
    } catch (fallo) {
      setError(
        fallo instanceof ErrorApi ? fallo.message : "No se pudo cargar el catálogo.",
      );
    } finally {
      setCargando(false);
    }
  }, [seccion]);

  useEffect(() => {
    void cargar();
    setNombre("");
    setExtra("");
    setPadreId("");
  }, [cargar]);

  async function crear() {
    setError(null);
    try {
      const cuerpo: Record<string, unknown> = { nombre };
      if (campoExtra && extra) cuerpo[campoExtra.clave] = extra;
      if (seccion === "categorias" && padreId) cuerpo.categoria_padre_id = padreId;

      await pedir(`/${seccion}/`, { metodo: "POST", cuerpo });
      setNombre("");
      setExtra("");
      await cargar();
    } catch (fallo) {
      setError(fallo instanceof ErrorApi ? fallo.message : "No se pudo crear.");
    }
  }

  /** Muestra la jerarquía de categorías con el nombre del padre. */
  function textoElemento(elemento: ElementoCatalogo): string {
    if (seccion !== "categorias" || !elemento.categoria_padre_id) {
      return elemento.nombre;
    }
    const padre = elementos.find((e) => e.id === elemento.categoria_padre_id);
    return padre ? `${padre.nombre} › ${elemento.nombre}` : elemento.nombre;
  }

  return (
    <div className="space-y-4">
      <p className="text-tinta-suave">{AYUDA_CATALOGO[seccion]}</p>

      {error && <Aviso>{error}</Aviso>}

      <section className="tarjeta space-y-3 p-4">
        <div>
          <label htmlFor="nombre" className="etiqueta-campo">
            Nombre
          </label>
          <input
            id="nombre"
            className="campo"
            value={nombre}
            onChange={(e) => setNombre(e.target.value)}
          />
        </div>

        {campoExtra && (
          <div>
            <label htmlFor="extra" className="etiqueta-campo">
              {campoExtra.etiqueta}
            </label>
            <input
              id="extra"
              className="campo"
              value={extra}
              onChange={(e) => setExtra(e.target.value)}
            />
          </div>
        )}

        {seccion === "categorias" && (
          <div>
            <label htmlFor="padre" className="etiqueta-campo">
              ¿Va dentro de otra categoría?
            </label>
            <select
              id="padre"
              className="campo"
              value={padreId}
              onChange={(e) => setPadreId(e.target.value)}
            >
              <option value="">No, es una categoría nueva e independiente</option>
              {elementos
                .filter((e) => !e.categoria_padre_id)
                .map((e) => (
                  <option key={e.id} value={e.id}>
                    Sí, va dentro de "{e.nombre}"
                  </option>
                ))}
            </select>
            <p className="mt-1.5 text-sm text-tinta-tenue">
              {padreId ? (
                <>
                  Va a quedar como <strong>subcategoría</strong>, agrupada bajo la
                  categoría que elegiste. Por ejemplo: "Panadería" › lo que estás
                  creando ahora.
                </>
              ) : (
                <>
                  Dejalo así si es una categoría de primer nivel, como
                  "Panadería" o "Postres". Después vas a poder crear
                  subcategorías adentro de ella.
                </>
              )}
            </p>
          </div>
        )}

        <button
          type="button"
          className="boton-primario"
          disabled={!nombre.trim()}
          onClick={crear}
        >
          Agregar
        </button>
      </section>

      {cargando ? (
        <Cargando />
      ) : (
        <section className="tarjeta overflow-hidden">
          {elementos.length === 0 ? (
            <p className="px-4 py-8 text-center text-tinta-suave">
              Todavía no hay nada cargado acá.
            </p>
          ) : (
            <ul className="divide-y divide-borde">
              {elementos.map((elemento) => (
                <li key={elemento.id} className="px-4 py-3">
                  <span className="font-medium">{textoElemento(elemento)}</span>
                  {(elemento.descripcion || elemento.detalle) && (
                    <span className="ml-2 text-sm text-tinta-suave">
                      {elemento.descripcion || elemento.detalle}
                    </span>
                  )}
                </li>
              ))}
            </ul>
          )}
        </section>
      )}
    </div>
  );
}

function Familia() {
  const { perfil } = useAutenticacion();
  const [usuarios, setUsuarios] = useState<UsuarioResumen[]>([]);
  const [nombre, setNombre] = useState("");
  const [correo, setCorreo] = useState("");
  const [clave, setClave] = useState("");
  const [rol, setRol] = useState("usuario_familiar");
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const cargar = useCallback(async () => {
    setCargando(true);
    try {
      setUsuarios(
        await pedir<UsuarioResumen[]>("/usuarios/?incluir_inactivos=true"),
      );
    } catch (fallo) {
      setError(
        fallo instanceof ErrorApi
          ? fallo.message
          : "No se pudieron cargar los usuarios.",
      );
    } finally {
      setCargando(false);
    }
  }, []);

  useEffect(() => {
    void cargar();
  }, [cargar]);

  async function crear() {
    setError(null);
    try {
      await pedir("/usuarios/", {
        metodo: "POST",
        cuerpo: { nombre, correo, clave, rol },
      });
      setNombre("");
      setCorreo("");
      setClave("");
      await cargar();
    } catch (fallo) {
      setError(
        fallo instanceof ErrorApi ? fallo.message : "No se pudo crear el usuario.",
      );
    }
  }

  async function desactivar(id: string) {
    setError(null);
    try {
      await pedir(`/usuarios/${id}/`, { metodo: "DELETE" });
      await cargar();
    } catch (fallo) {
      setError(
        fallo instanceof ErrorApi ? fallo.message : "No se pudo desactivar.",
      );
    }
  }

  return (
    <div className="space-y-4">
      <p className="text-tinta-suave">
        Quienes pueden entrar al recetario. Los usuarios se desactivan, nunca se
        eliminan: así se conserva quién cargó cada receta.
      </p>

      {error && <Aviso>{error}</Aviso>}

      <section className="tarjeta space-y-3 p-4">
        <div className="grid gap-3 sm:grid-cols-2">
          <div>
            <label htmlFor="unombre" className="etiqueta-campo">
              Nombre
            </label>
            <input
              id="unombre"
              className="campo"
              value={nombre}
              onChange={(e) => setNombre(e.target.value)}
            />
          </div>
          <div>
            <label htmlFor="ucorreo" className="etiqueta-campo">
              Correo
            </label>
            <input
              id="ucorreo"
              type="email"
              className="campo"
              value={correo}
              onChange={(e) => setCorreo(e.target.value)}
            />
          </div>
          <div>
            <label htmlFor="uclave" className="etiqueta-campo">
              Contraseña
            </label>
            <input
              id="uclave"
              type="text"
              className="campo"
              value={clave}
              onChange={(e) => setClave(e.target.value)}
              placeholder="Mínimo 8 caracteres"
            />
          </div>
          <div>
            <label htmlFor="urol" className="etiqueta-campo">
              Rol
            </label>
            <select
              id="urol"
              className="campo"
              value={rol}
              onChange={(e) => setRol(e.target.value)}
            >
              <option value="usuario_familiar">
                Usuario familiar — usa el recetario
              </option>
              <option value="administrador">
                Administrador — además gestiona catálogos
              </option>
            </select>
          </div>
        </div>

        <button
          type="button"
          className="boton-primario"
          disabled={!nombre.trim() || !correo.trim() || clave.length < 8}
          onClick={crear}
        >
          Sumar a la familia
        </button>
      </section>

      {cargando ? (
        <Cargando />
      ) : (
        <section className="tarjeta overflow-hidden">
          <ul className="divide-y divide-borde">
            {usuarios.map((usuario) => (
              <li key={usuario.id} className="flex items-center gap-3 px-4 py-3">
                <div className="min-w-0 flex-1">
                  <p className="truncate font-medium">
                    {usuario.nombre}
                    {usuario.id === perfil?.id && (
                      <span className="ml-2 text-sm text-tinta-tenue">(vos)</span>
                    )}
                  </p>
                  <p className="truncate text-sm text-tinta-suave">
                    {usuario.correo}
                  </p>
                </div>

                <span className="chip">
                  {usuario.rol === "administrador" ? "Admin" : "Familiar"}
                </span>

                {!usuario.activo ? (
                  <span className="text-sm font-medium text-advertencia">
                    Inactivo
                  </span>
                ) : (
                  usuario.id !== perfil?.id && (
                    <button
                      type="button"
                      className="text-sm font-medium text-error"
                      onClick={() => desactivar(usuario.id)}
                    >
                      Desactivar
                    </button>
                  )
                )}
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
