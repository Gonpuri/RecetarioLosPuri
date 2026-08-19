/**
 * Importación de recetas desde PDF, foto o dictado (Cap. 7.7, versión 2.0).
 *
 * Los tres terminan igual: un borrador que se revisa en el mismo
 * formulario de "Nueva receta" -reutilizado tal cual, con los campos
 * precompletados- porque el problema de fondo es siempre el mismo: cargar
 * una receta. La importación nunca guarda nada por sí sola.
 *
 * PDF y dictado usan IA para entender el texto (costo pequeño por
 * receta). Foto usa lectura óptica gratuita más reglas simples, sin IA:
 * es menos precisa a propósito, para no generar costo.
 *
 * El dictado transcribe la voz con la función del propio navegador -sin
 * costo ni backend para esa parte- y solo envía texto plano, nunca audio.
 */

import { useRef, useState } from "react";
import { Link } from "react-router-dom";

import { almacen, ErrorApi, pedir } from "../api/cliente";
import type { RecetaImportada } from "../api/tipos";
import { Aviso, Cargando } from "../componentes/Comunes";
import NuevaReceta from "./NuevaReceta";

type Metodo = "pdf" | "foto" | "dictado";

const CONFIGURACION_ARCHIVO: Record<
  "pdf" | "foto",
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

const NOMBRE_PESTANIA: Record<Metodo, string> = {
  pdf: "Desde PDF",
  foto: "Desde foto",
  dictado: "Dictado",
};

/**
 * La API de reconocimiento de voz no tiene tipos oficiales de TypeScript
 * -es un estándar todavía no consolidado entre navegadores-, así que se
 * declara acá lo mínimo que se usa.
 */
interface ReconocedorVoz {
  lang: string;
  continuous: boolean;
  interimResults: boolean;
  onresult:
    | ((evento: { results: ArrayLike<ArrayLike<{ transcript: string }>> }) => void)
    | null;
  onerror: (() => void) | null;
  onend: (() => void) | null;
  start: () => void;
  stop: () => void;
}

function obtenerConstructorReconocedor(): (new () => ReconocedorVoz) | null {
  const global = window as unknown as {
    SpeechRecognition?: new () => ReconocedorVoz;
    webkitSpeechRecognition?: new () => ReconocedorVoz;
  };
  return global.SpeechRecognition ?? global.webkitSpeechRecognition ?? null;
}

export default function ImportarReceta() {
  const [metodo, setMetodo] = useState<Metodo>("pdf");
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [borrador, setBorrador] = useState<RecetaImportada | null>(null);
  const entrada = useRef<HTMLInputElement>(null);

  // Estado propio del dictado: no comparte nada con la subida de archivos.
  const [escuchando, setEscuchando] = useState(false);
  const [transcripcion, setTranscripcion] = useState("");
  const reconocedorRef = useRef<ReconocedorVoz | null>(null);
  const constructorReconocedor = obtenerConstructorReconocedor();

  async function subir(archivo: File | undefined) {
    if (!archivo || metodo === "dictado") return;
    const config = CONFIGURACION_ARCHIVO[metodo];
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

  function iniciarDictado() {
    if (!constructorReconocedor) return;
    const reconocedor = new constructorReconocedor();
    reconocedor.lang = "es-AR";
    reconocedor.continuous = true;
    reconocedor.interimResults = true;
    reconocedor.onresult = (evento) => {
      let texto = "";
      for (let i = 0; i < evento.results.length; i++) {
        texto += evento.results[i][0].transcript;
      }
      setTranscripcion(texto);
    };
    reconocedor.onerror = () => setEscuchando(false);
    reconocedor.onend = () => setEscuchando(false);
    reconocedor.start();
    reconocedorRef.current = reconocedor;
    setEscuchando(true);
    setError(null);
  }

  function detenerDictado() {
    reconocedorRef.current?.stop();
    setEscuchando(false);
  }

  async function enviarDictado() {
    if (!transcripcion.trim()) return;
    setError(null);
    setCargando(true);
    try {
      setBorrador(
        await pedir<RecetaImportada>("/importar/dictado/", {
          metodo: "POST",
          cuerpo: { texto: transcripcion },
        }),
      );
    } catch (fallo) {
      setError(
        fallo instanceof ErrorApi
          ? fallo.message
          : "No se pudo conectar con el servidor. Probá de nuevo.",
      );
    } finally {
      setCargando(false);
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
          Subí un PDF, una foto, o dictala en voz alta, y te armamos un
          borrador para que lo revises.
        </p>
      </div>

      <div className="flex gap-2" role="tablist">
        {(Object.keys(NOMBRE_PESTANIA) as Metodo[]).map((clave) => (
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
            {NOMBRE_PESTANIA[clave]}
          </button>
        ))}
      </div>

      {error && <Aviso>{error}</Aviso>}

      {metodo !== "dictado" ? (
        <section className="tarjeta space-y-4 p-6 text-center">
          <p className="text-sm text-tinta-suave">
            {CONFIGURACION_ARCHIVO[metodo].ayuda}
          </p>

          {cargando ? (
            <Cargando texto="Leyendo la receta… puede tardar unos segundos." />
          ) : (
            <>
              <input
                ref={entrada}
                type="file"
                accept={CONFIGURACION_ARCHIVO[metodo].aceptar}
                className="hidden"
                onChange={(e) => void subir(e.target.files?.[0])}
              />
              <button
                type="button"
                className="boton-primario"
                onClick={() => entrada.current?.click()}
              >
                {CONFIGURACION_ARCHIVO[metodo].etiqueta}
              </button>
            </>
          )}
        </section>
      ) : (
        <section className="tarjeta space-y-4 p-6">
          <p className="text-sm text-tinta-suave">
            Con inteligencia artificial, igual que el PDF: tiene un costo
            pequeño por receta, pero separa mucho mejor los ingredientes de
            los pasos que intentar hacerlo gratis con un dictado hablado de
            corrido.
          </p>

          {!constructorReconocedor ? (
            <Aviso tono="advertencia">
              Tu navegador no admite dictado por voz. Probá con Chrome o
              Edge, o usá alguna de las otras opciones de importación.
            </Aviso>
          ) : cargando ? (
            <Cargando texto="Interpretando la receta… puede tardar unos segundos." />
          ) : (
            <>
              <div className="flex justify-center">
                <button
                  type="button"
                  onClick={escuchando ? detenerDictado : iniciarDictado}
                  className={`flex h-16 w-16 items-center justify-center rounded-full transition-colors ${
                    escuchando
                      ? "animate-pulse bg-error text-white"
                      : "bg-azul text-white hover:bg-azul-oscuro"
                  }`}
                  aria-pressed={escuchando}
                  aria-label={
                    escuchando ? "Detener el dictado" : "Empezar a dictar"
                  }
                >
                  <svg
                    viewBox="0 0 24 24"
                    className="h-7 w-7"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth={1.8}
                    aria-hidden="true"
                  >
                    <rect x="9" y="3" width="6" height="11" rx="3" />
                    <path strokeLinecap="round" d="M5 11a7 7 0 0014 0M12 18v3" />
                  </svg>
                </button>
              </div>
              <p className="text-center text-sm text-tinta-tenue">
                {escuchando
                  ? "Escuchando… decí el nombre, los ingredientes y los pasos."
                  : "Tocá el micrófono y dictá la receta completa, como se la " +
                    "contarías a alguien."}
              </p>

              <label htmlFor="transcripcion" className="etiqueta-campo">
                Lo que se entendió (podés corregirlo antes de continuar)
              </label>
              <textarea
                id="transcripcion"
                className="campo"
                rows={6}
                value={transcripcion}
                onChange={(e) => setTranscripcion(e.target.value)}
                placeholder="Acá va apareciendo el texto a medida que hablás…"
              />

              <button
                type="button"
                className="boton-primario w-full"
                disabled={!transcripcion.trim()}
                onClick={enviarDictado}
              >
                Usar este texto
              </button>
            </>
          )}
        </section>
      )}
    </div>
  );
}
