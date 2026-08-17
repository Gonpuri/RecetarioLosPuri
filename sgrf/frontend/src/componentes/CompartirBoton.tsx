/**
 * Botón para compartir texto (RF-037).
 *
 * No se integra con ninguna app en particular. Usa la función de compartir
 * nativa del sistema operativo (`navigator.share`): en el celular abre el
 * mismo menú que cualquier otra app, donde Google Keep, WhatsApp, Notas o
 * el correo aparecen como opciones -las que la persona tenga instaladas.
 *
 * Se descartó integrar directamente con Google Keep porque su API oficial
 * es exclusiva de cuentas de Google Workspace (empresariales), no de
 * cuentas personales de Gmail. Existe una vía no oficial, pero exige
 * guardar un token con acceso total a la cuenta de Google del usuario -un
 * riesgo de seguridad que no vale la pena para esto.
 *
 * En equipos donde `navigator.share` no existe (la mayoría de las
 * computadoras de escritorio), el botón copia el texto al portapapeles.
 */

import { useState, type ReactNode } from "react";

export default function CompartirBoton({
  titulo,
  texto,
  className = "boton-secundario",
  children,
  ariaLabel,
}: {
  titulo: string;
  texto: string;
  className?: string;
  /** Contenido del botón (por ejemplo un ícono). Si no se pasa, usa el texto por defecto. */
  children?: ReactNode;
  /** Requerido si `children` es un ícono sin texto visible. */
  ariaLabel?: string;
}) {
  const [copiado, setCopiado] = useState(false);
  const puedeCompartir = typeof navigator !== "undefined" && "share" in navigator;

  async function compartir() {
    if (puedeCompartir) {
      try {
        await navigator.share({ title: titulo, text: texto });
      } catch {
        // La persona cerró el menú de compartir sin elegir nada: no es un error.
      }
      return;
    }

    try {
      await navigator.clipboard.writeText(texto);
      setCopiado(true);
      setTimeout(() => setCopiado(false), 2000);
    } catch {
      // Sin permiso de portapapeles no hay mucho más para ofrecer acá.
    }
  }

  return (
    <button
      type="button"
      className={className}
      onClick={compartir}
      aria-label={children ? ariaLabel ?? "Compartir" : undefined}
    >
      {children ?? (puedeCompartir ? "Compartir" : copiado ? "¡Copiado!" : "Copiar")}
    </button>
  );
}
