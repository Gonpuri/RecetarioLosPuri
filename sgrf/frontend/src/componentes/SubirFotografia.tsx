/**
 * Subida de fotografías.
 *
 * El archivo va directo del navegador a Cloudinary usando una firma que
 * emite el backend. La imagen no atraviesa nuestro servidor y el secreto
 * de la cuenta nunca sale de él.
 *
 * RN-005 limita a dos fotos de proceso y una final por receta. El límite
 * lo aplica el dominio: acá sólo se ocultan las opciones que ya están
 * ocupadas, para no ofrecer algo que va a fallar.
 */

import { useRef, useState } from "react";

import { ErrorApi, pedir } from "../api/cliente";
import type { TipoFotografia } from "../api/tipos";
import { Aviso } from "./Comunes";

interface Firma {
  timestamp: number;
  folder: string;
  allowed_formats: string;
  signature: string;
  api_key: string;
  cloud_name: string;
  url_subida: string;
}

const TAMANIO_MAXIMO = 8 * 1024 * 1024;

/** Sube el archivo a Cloudinary y devuelve la URL pública resultante. */
async function subirACloudinary(archivo: File): Promise<string> {
  const firma = await pedir<Firma>("/fotografias/firma/", { metodo: "POST" });

  const formulario = new FormData();
  formulario.append("file", archivo);
  formulario.append("api_key", firma.api_key);
  formulario.append("timestamp", String(firma.timestamp));
  formulario.append("folder", firma.folder);
  formulario.append("allowed_formats", firma.allowed_formats);
  formulario.append("signature", firma.signature);

  const respuesta = await fetch(firma.url_subida, {
    method: "POST",
    body: formulario,
  });

  if (!respuesta.ok) {
    throw new Error("Cloudinary rechazó la imagen.");
  }

  const datos = await respuesta.json();
  return datos.secure_url as string;
}

export default function SubirFotografia({
  recetaId,
  preparacionId,
  tiposDisponibles,
  onSubida,
}: {
  recetaId: string;
  preparacionId: string;
  tiposDisponibles: TipoFotografia[];
  onSubida: () => void;
}) {
  const entrada = useRef<HTMLInputElement>(null);
  const [tipo, setTipo] = useState<TipoFotografia>(
    tiposDisponibles[0] ?? "proceso",
  );
  const [subiendo, setSubiendo] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (tiposDisponibles.length === 0) {
    return (
      <p className="text-sm text-tinta-tenue">
        Esta receta ya tiene sus tres fotografías. Eliminá una para agregar otra.
      </p>
    );
  }

  async function elegir(archivo: File | undefined) {
    if (!archivo) return;
    setError(null);

    if (archivo.size > TAMANIO_MAXIMO) {
      setError("La imagen supera los 8 MB. Probá con una más liviana.");
      return;
    }

    setSubiendo(true);
    try {
      const url = await subirACloudinary(archivo);
      await pedir(
        `/recetas/${recetaId}/preparaciones/${preparacionId}/fotografias/`,
        { metodo: "POST", cuerpo: { ruta: url, tipo } },
      );
      onSubida();
      if (entrada.current) entrada.current.value = "";
    } catch (fallo) {
      setError(
        fallo instanceof ErrorApi
          ? fallo.message
          : "No se pudo subir la imagen. Probá de nuevo.",
      );
    } finally {
      setSubiendo(false);
    }
  }

  return (
    <div className="space-y-2">
      <div className="flex flex-wrap items-center gap-2">
        <select
          className="campo w-40"
          value={tipo}
          onChange={(e) => setTipo(e.target.value as TipoFotografia)}
          disabled={subiendo}
          aria-label="Tipo de fotografía"
        >
          {tiposDisponibles.map((opcion) => (
            <option key={opcion} value={opcion}>
              {opcion === "final" ? "Foto final" : "Foto del proceso"}
            </option>
          ))}
        </select>

        <input
          ref={entrada}
          type="file"
          accept="image/jpeg,image/png,image/webp"
          className="hidden"
          onChange={(e) => void elegir(e.target.files?.[0])}
        />

        <button
          type="button"
          className="boton-secundario"
          onClick={() => entrada.current?.click()}
          disabled={subiendo}
        >
          {subiendo ? "Subiendo…" : "Elegir imagen"}
        </button>
      </div>

      {error && <Aviso>{error}</Aviso>}
    </div>
  );
}
