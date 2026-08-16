/**
 * Selector de ingrediente con alta al vuelo.
 *
 * Decisión D-19: cualquier usuario activo puede sumar un ingrediente al
 * catálogo, a diferencia de categorías y fuentes, que siguen siendo del
 * Administrador. Este componente evita que cargar una receta se trabe
 * esperando que otra persona cree el ingrediente que falta.
 *
 * El desplegable ya incluye la opción "Crear…" al final: no hace falta un
 * botón aparte ni una pantalla nueva.
 */

import { useState } from "react";

import { ErrorApi, pedir } from "../api/cliente";
import type { ElementoCatalogo } from "../api/tipos";

const OPCION_CREAR = "__crear__";

export default function SelectorIngrediente({
  ingredientes,
  valor,
  onCambiar,
  onCreado,
}: {
  ingredientes: ElementoCatalogo[];
  valor: string;
  onCambiar: (id: string) => void;
  /** Se dispara cuando se crea un ingrediente nuevo, para sumarlo a la lista del formulario. */
  onCreado: (nuevo: ElementoCatalogo) => void;
}) {
  const [creando, setCreando] = useState(false);
  const [nombre, setNombre] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [guardando, setGuardando] = useState(false);

  async function crear() {
    if (!nombre.trim()) return;
    setError(null);
    setGuardando(true);
    try {
      const nuevo = await pedir<{ id: string; nombre: string }>("/ingredientes/", {
        metodo: "POST",
        cuerpo: { nombre: nombre.trim() },
      });
      onCreado({ id: nuevo.id, nombre: nuevo.nombre });
      onCambiar(nuevo.id);
      setCreando(false);
      setNombre("");
    } catch (fallo) {
      setError(
        fallo instanceof ErrorApi
          ? fallo.message
          : "No se pudo crear el ingrediente.",
      );
    } finally {
      setGuardando(false);
    }
  }

  if (creando) {
    return (
      <div className="space-y-2 rounded-pieza border border-azul bg-azul-claro/30 p-2">
        <div className="flex gap-2">
          <input
            autoFocus
            className="campo flex-1"
            value={nombre}
            onChange={(e) => setNombre(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && crear()}
            placeholder="Nombre del ingrediente nuevo"
            aria-label="Nombre del ingrediente nuevo"
          />
          <button
            type="button"
            className="boton-primario"
            disabled={!nombre.trim() || guardando}
            onClick={crear}
          >
            {guardando ? "Creando…" : "Crear"}
          </button>
          <button
            type="button"
            className="boton-secundario"
            onClick={() => {
              setCreando(false);
              setNombre("");
              setError(null);
            }}
          >
            Cancelar
          </button>
        </div>
        {error && <p className="text-sm text-error">{error}</p>}
      </div>
    );
  }

  return (
    <select
      className="campo flex-1"
      value={valor}
      onChange={(e) => {
        if (e.target.value === OPCION_CREAR) {
          setCreando(true);
          return;
        }
        onCambiar(e.target.value);
      }}
      aria-label="Ingrediente"
    >
      <option value="">Elegí un ingrediente…</option>
      {ingredientes.map((item) => (
        <option key={item.id} value={item.id}>
          {item.nombre}
        </option>
      ))}
      <option value={OPCION_CREAR}>+ Crear un ingrediente nuevo…</option>
    </select>
  );
}
