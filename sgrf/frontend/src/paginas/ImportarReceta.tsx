/**
 * Importación de recetas desde PDF o foto (Cap. 7.7, versión 2.0).
 *
 * Dos pasos: subir el archivo y recibir un borrador, y después revisarlo
 * en el mismo formulario de "Nueva receta" -reutilizado tal cual, con los
 * campos precompletados- porque el problema de fondo es el mismo: cargar
 * una receta. La importación nunca guarda nada por sí sola.
 *
 * PDF usa IA para entender el texto (tiene un costo pequeño por receta).
 * Foto usa lectura óptica gratuita más reglas simples, sin IA: es menos
 * precisa a propósito, para no generar costo.
 */

import { useRef, useState } from "react";
import { Link } from "react-router-dom";

import { almacen, ErrorApi } from "../api/cliente";
import type { RecetaImportada } from "../api/tipos";
import { Aviso, Cargando } from "../componentes/Comunes";
import NuevaReceta from "./NuevaReceta";

type Metodo = "pdf" | "foto";

const CONFIGURACION: Record<
  Metodo,
  { ruta: string; aceptar: string; etiqueta: string; ayuda: string }
> = {
  pdf: {
    ruta: "/importar/pdf/",
    aceptar: "application/pdf",
    etiqueta: "Elegir un PDF",
    ayuda:
      "Funciona con PDF que tienen texto seleccionable -la mayoría de los que se " +
      "generan desde una página web o un procesador de texto-. Un PDF que es una " +
      "foto escaneada no va a funcionar acá: probá con la pestaña Foto.",
  },
  foto: {
    ruta: "/importar/foto/",
    aceptar: "image/*",
    etiqueta: "Elegir una foto",
    ayuda:
      "Gratis, sin inteligencia artificial: lee el texto de la imagen y separa " +
      "ingredientes de pasos con reglas simples. Funciona mejor con letra impresa " +
      "que con manuscrita, y siempre hay que revisar el resultado con cuidado.",
  },
};

export default function ImportarReceta() {
  const [metodo, setMetodo] = useState<Metodo>("pdf");
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [borrador, setBorrador] = useState<RecetaImportada | null>(null);
  const entrada = useRef<HTMLInputElement>(null);

  const config = CONFIGURACION[metodo];

  async function subir(archivo: File | undefined) {
    if (!archivo) return;
    setError(null);
    setCargando(true);
    try {
      const formulario = new FormData();
      formulario.append("archivo", archivo);

      // `pedir` siempre manda JSON; para un archivo hace falta un fetch
      // directo, sin forzar el encabezado Content-Type -el navegador arma
      // el `multipart/form-data` con el separador correcto solo.
      const acceso = almacen.acceso();
      const base = import.meta.env.VITE_API_URL ?? "/api";
      const respuesta = await fetch(`${base}${config.ruta}`, {
        method: "POST",
        headers: acceso ? { Authorization: `Bearer ${acceso}` } : {},
        body: formulario,
      });

      if (!respuesta.ok) {
        const cuerpo = await respuesta.json().catch(() => null);
        throw new ErrorApi(
          cuerpo?.error ?? "No se pudo procesar el archivo.",
          respuesta.status,
        );
      }

      setBorrador(await respuesta.json());
    } catch (fallo) {
      setError(
        fallo instanceof ErrorApi
          ? fallo.message
          : "No se pudo conectar con el servidor. Probá de nuevo.",
      );
    } finally {
      setCargando(false);
      if (entrada.current) entrada.current.value = "";
    }
  }

  // Una vez que hay un borrador, la pantalla se convierte en el formulario
  // de alta común, ya precompletado con lo que se pudo extraer.
  if (borrador) {
    return <NuevaReceta borradorInicial={borrador} titulo="Revisá la receta importada" />;
  }

  return (
    <div className="space-y-5 pb-8">
      <div>
        <Link
          to="/recetas/nueva"
          className="text-sm font-medium text-tinta-suave hover:text-azul"
        >
          ← Cargar con el formulario en blanco
        </Link>
        <h1 className="mt-2 text-2xl font-semibold tracking-tight">
          Importar receta
        </h1>
        <p className="mt-1 text-tinta-suave">
          Subí un PDF o una foto y te armamos un borrador para que lo revises.
        </p>
      </div>

      <div className="flex gap-2" role="tablist">
        {(Object.keys(CONFIGURACION) as Metodo[]).map((clave) => (
          <button
            key={clave}
            type="button"
            role="tab"
            aria-selected={metodo === clave}
            onClick={() => setMetodo(clave)}
            className={`flex-1 rounded-pieza px-4 py-3 text-sm font-semibold transition-colors ${
              metodo === clave
                ? "bg-azul text-white"
                : "border border-borde bg-white text-tinta-suave hover:text-azul"
            }`}
          >
            {clave === "pdf" ? "Desde PDF" : "Desde foto"}
          </button>
        ))}
      </div>

      <section className="tarjeta space-y-4 p-6 text-center">
        <p className="text-sm text-tinta-suave">{config.ayuda}</p>

        {error && <Aviso>{error}</Aviso>}

        {cargando ? (
          <Cargando texto="Leyendo la receta… puede tardar unos segundos." />
        ) : (
          <>
            <input
              ref={entrada}
              type="file"
              accept={config.aceptar}
              className="hidden"
              onChange={(e) => void subir(e.target.files?.[0])}
            />
            <button
              type="button"
              className="boton-primario"
              onClick={() => entrada.current?.click()}
            >
              {config.etiqueta}
            </button>
          </>
        )}
      </section>
    </div>
  );
}
