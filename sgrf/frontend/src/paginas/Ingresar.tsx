/**
 * Pantalla de ingreso.
 *
 * El sistema es un recetario familiar cerrado: el alta de usuarios la hace
 * el Administrador, de modo que acá no hay registro público.
 */

import { useState, type FormEvent } from "react";
import { Navigate, useLocation } from "react-router-dom";

import { ErrorApi } from "../api/cliente";
import { Aviso } from "../componentes/Comunes";
import { useAutenticacion } from "../contexto/Autenticacion";

export default function Ingresar() {
  const { perfil, ingresar } = useAutenticacion();
  const ubicacion = useLocation() as { state?: { desde?: { pathname: string } } };

  const [correo, setCorreo] = useState("");
  const [clave, setClave] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  if (perfil) {
    return <Navigate to={ubicacion.state?.desde?.pathname ?? "/recetas"} replace />;
  }

  async function enviar(evento: FormEvent) {
    evento.preventDefault();
    setError(null);
    setEnviando(true);
    try {
      await ingresar(correo, clave);
    } catch (fallo) {
      setError(mensajeDeFallo(fallo));
    } finally {
      setEnviando(false);
    }
  }

  return (
    <div className="mx-auto mt-10 max-w-sm">
      <div className="mb-8 text-center">
        <span className="mx-auto grid h-14 w-14 place-items-center rounded-pieza bg-azul text-white">
          <svg viewBox="0 0 24 24" className="h-7 w-7" aria-hidden="true">
            <path
              d="M8 3v7a3 3 0 006 0V3M11 3v7M8 3h6M11 10v11"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.6"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </span>
        <h1 className="mt-4 text-2xl font-semibold tracking-tight">
          Recetario familiar
        </h1>
        <p className="mt-1 text-tinta-suave">
          Las recetas de la familia, en un solo lugar.
        </p>
      </div>

      <form onSubmit={enviar} className="tarjeta space-y-4 p-6">
        <div>
          <label htmlFor="correo" className="etiqueta-campo">
            Correo
          </label>
          <input
            id="correo"
            type="email"
            autoComplete="email"
            required
            className="campo"
            value={correo}
            onChange={(e) => setCorreo(e.target.value)}
          />
        </div>

        <div>
          <label htmlFor="clave" className="etiqueta-campo">
            Contraseña
          </label>
          <input
            id="clave"
            type="password"
            autoComplete="current-password"
            required
            className="campo"
            value={clave}
            onChange={(e) => setClave(e.target.value)}
          />
        </div>

        {error && <Aviso>{error}</Aviso>}

        <button type="submit" className="boton-primario w-full" disabled={enviando}>
          {enviando ? "Ingresando…" : "Ingresar"}
        </button>
      </form>

      <p className="mt-4 text-center text-sm text-tinta-tenue">
        ¿No tenés cuenta? Pedísela a quien administra el recetario.
      </p>
    </div>
  );
}

/**
 * Traduce el fallo al mensaje que corresponde en esta pantalla.
 *
 * Un 401 durante el ingreso significa credenciales incorrectas, no sesión
 * vencida: el mensaje genérico del cliente confundiría acá.
 */
function mensajeDeFallo(fallo: unknown): string {
  if (fallo instanceof ErrorApi) {
    if (fallo.codigo === 401) return "El correo o la contraseña no coinciden.";
    return fallo.message;
  }
  return "No se pudo conectar con el servidor. Revisá tu conexión.";
}
