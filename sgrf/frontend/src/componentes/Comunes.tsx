/**
 * Componentes compartidos.
 *
 * Cubren los estados que toda pantalla necesita resolver: carga, error,
 * vacío y confirmación. El Capítulo 6.12 pide que los errores sean claros
 * y accionables, de modo que `Aviso` siempre muestra el mensaje que
 * redactó el backend en lugar de un texto genérico.
 */

import type { ReactNode } from "react";

export function Cargando({ texto = "Cargando…" }: { texto?: string }) {
  return (
    <div
      className="flex items-center justify-center gap-3 py-16 text-tinta-suave"
      role="status"
      aria-live="polite"
    >
      <span className="h-4 w-4 animate-spin rounded-full border-2 border-borde border-t-azul" />
      {texto}
    </div>
  );
}

type TonoAviso = "error" | "exito" | "advertencia";

const ESTILOS_AVISO: Record<TonoAviso, string> = {
  error: "border-error/30 bg-error/5 text-error",
  exito: "border-exito/30 bg-exito/5 text-exito",
  advertencia: "border-advertencia/30 bg-advertencia/5 text-advertencia",
};

export function Aviso({
  tono = "error",
  children,
}: {
  tono?: TonoAviso;
  children: ReactNode;
}) {
  return (
    <p
      className={`rounded-pieza border px-4 py-3 text-sm ${ESTILOS_AVISO[tono]}`}
      role={tono === "error" ? "alert" : "status"}
    >
      {children}
    </p>
  );
}

/** Pantalla vacía. El Capítulo 6.12 la trata como una invitación a actuar. */
export function Vacio({
  titulo,
  descripcion,
  accion,
}: {
  titulo: string;
  descripcion: string;
  accion?: ReactNode;
}) {
  return (
    <div className="tarjeta px-6 py-14 text-center">
      <h2 className="text-lg font-semibold text-tinta">{titulo}</h2>
      <p className="mx-auto mt-2 max-w-sm text-tinta-suave">{descripcion}</p>
      {accion && <div className="mt-6">{accion}</div>}
    </div>
  );
}

/** Estrella de favoritas. Comunica el estado por texto además de por color. */
export function Estrella({ activa }: { activa: boolean }) {
  return (
    <svg
      viewBox="0 0 24 24"
      className={`h-5 w-5 ${activa ? "fill-advertencia" : "fill-none"}`}
      stroke="currentColor"
      strokeWidth={1.6}
      aria-hidden="true"
    >
      <path d="M12 3.5l2.6 5.3 5.9.9-4.3 4.1 1 5.8-5.2-2.7-5.2 2.7 1-5.8-4.3-4.1 5.9-.9z" />
    </svg>
  );
}
