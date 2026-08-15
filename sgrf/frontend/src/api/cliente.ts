/**
 * Cliente de la API del SGRF.
 *
 * Concentra el manejo del token, el refresco automatico y la traduccion de
 * los errores del backend a mensajes legibles. Ninguna pantalla llama a
 * `fetch` directamente.
 */

const BASE = import.meta.env.VITE_API_URL ?? "/api";

const CLAVE_ACCESO = "sgrf.acceso";
const CLAVE_REFRESCO = "sgrf.refresco";

export const almacen = {
  acceso: () => localStorage.getItem(CLAVE_ACCESO),
  refresco: () => localStorage.getItem(CLAVE_REFRESCO),
  guardar(acceso: string, refresco: string) {
    localStorage.setItem(CLAVE_ACCESO, acceso);
    localStorage.setItem(CLAVE_REFRESCO, refresco);
  },
  guardarAcceso(acceso: string) {
    localStorage.setItem(CLAVE_ACCESO, acceso);
  },
  limpiar() {
    localStorage.removeItem(CLAVE_ACCESO);
    localStorage.removeItem(CLAVE_REFRESCO);
  },
};

/** Error de la API con el mensaje que el backend redacto para el usuario. */
export class ErrorApi extends Error {
  constructor(
    mensaje: string,
    public readonly codigo: number,
    public readonly regla?: string,
  ) {
    super(mensaje);
    this.name = "ErrorApi";
  }
}

/** Traduce una respuesta fallida al mensaje que se muestra en pantalla. */
async function comoError(respuesta: Response): Promise<ErrorApi> {
  let mensaje = "No se pudo completar la operación.";
  let regla: string | undefined;

  try {
    const cuerpo = await respuesta.json();
    if (typeof cuerpo?.error === "string") {
      mensaje = cuerpo.error;
      regla = cuerpo.regla;
    } else if (typeof cuerpo?.detail === "string") {
      mensaje = cuerpo.detail;
    } else if (cuerpo && typeof cuerpo === "object") {
      // Errores de validación de DRF: { campo: ["mensaje"] }
      const primero = Object.entries(cuerpo)[0];
      if (primero) {
        const [campo, detalles] = primero;
        const texto = Array.isArray(detalles) ? detalles[0] : String(detalles);
        mensaje = campo === "non_field_errors" ? texto : `${campo}: ${texto}`;
      }
    }
  } catch {
    if (respuesta.status === 401) mensaje = "Tu sesión venció. Ingresá de nuevo.";
    if (respuesta.status >= 500) {
      mensaje = "El servidor no responde. Probá de nuevo en un momento.";
    }
  }

  return new ErrorApi(mensaje, respuesta.status, regla);
}

/** Pide un token de acceso nuevo usando el de refresco. */
async function refrescarToken(): Promise<boolean> {
  const refresco = almacen.refresco();
  if (!refresco) return false;

  const respuesta = await fetch(`${BASE}/auth/refrescar/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh: refresco }),
  });

  if (!respuesta.ok) return false;

  const datos = await respuesta.json();
  almacen.guardarAcceso(datos.access);
  if (datos.refresh) almacen.guardar(datos.access, datos.refresh);
  return true;
}

interface Opciones {
  metodo?: "GET" | "POST" | "PATCH" | "DELETE";
  cuerpo?: unknown;
  sinAutenticar?: boolean;
}

/**
 * Ejecuta una petición contra la API.
 *
 * Si el token venció, lo refresca una sola vez y reintenta. Un segundo
 * fallo significa que la sesión terminó de verdad.
 */
export async function pedir<T>(ruta: string, opciones: Opciones = {}): Promise<T> {
  const { metodo = "GET", cuerpo, sinAutenticar = false } = opciones;

  const ejecutar = async (): Promise<Response> => {
    const cabeceras: Record<string, string> = {
      "Content-Type": "application/json",
    };
    const acceso = almacen.acceso();
    if (!sinAutenticar && acceso) {
      cabeceras.Authorization = `Bearer ${acceso}`;
    }
    return fetch(`${BASE}${ruta}`, {
      method: metodo,
      headers: cabeceras,
      body: cuerpo === undefined ? undefined : JSON.stringify(cuerpo),
    });
  };

  let respuesta = await ejecutar();

  if (respuesta.status === 401 && !sinAutenticar) {
    if (await refrescarToken()) {
      respuesta = await ejecutar();
    } else {
      almacen.limpiar();
      throw new ErrorApi("Tu sesión venció. Ingresá de nuevo.", 401);
    }
  }

  if (!respuesta.ok) throw await comoError(respuesta);

  if (respuesta.status === 204) return undefined as T;
  return (await respuesta.json()) as T;
}

/** Inicia sesión y guarda los tokens. */
export async function ingresar(correo: string, clave: string): Promise<void> {
  const datos = await pedir<{ access: string; refresh: string }>("/auth/token/", {
    metodo: "POST",
    cuerpo: { correo, password: clave },
    sinAutenticar: true,
  });
  almacen.guardar(datos.access, datos.refresh);
}
