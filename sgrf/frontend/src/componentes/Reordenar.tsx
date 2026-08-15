/**
 * Control de reordenamiento.
 *
 * Usa flechas en lugar de arrastrar y soltar: funciona con el teclado, con
 * un lector de pantalla y con el dedo en un teléfono, que es donde más se
 * usa la aplicación (Capítulo 6.10). Arrastrar sería más vistoso y menos
 * accesible.
 */

export default function Reordenar({
  posicion,
  total,
  onMover,
  etiqueta,
}: {
  posicion: number;
  total: number;
  onMover: (destino: number) => void;
  etiqueta: string;
}) {
  if (total < 2) return null;

  return (
    <span className="flex shrink-0 flex-col">
      <button
        type="button"
        className="px-1.5 text-tinta-tenue transition-colors hover:text-azul disabled:opacity-25"
        disabled={posicion === 0}
        onClick={() => onMover(posicion - 1)}
        aria-label={`Subir ${etiqueta}`}
      >
        ▲
      </button>
      <button
        type="button"
        className="px-1.5 text-tinta-tenue transition-colors hover:text-azul disabled:opacity-25"
        disabled={posicion === total - 1}
        onClick={() => onMover(posicion + 1)}
        aria-label={`Bajar ${etiqueta}`}
      >
        ▼
      </button>
    </span>
  );
}

/** Devuelve una copia del arreglo con el elemento movido de lugar. */
export function moverElemento<T>(items: T[], desde: number, hasta: number): T[] {
  const copia = [...items];
  const [movido] = copia.splice(desde, 1);
  copia.splice(hasta, 0, movido);
  return copia;
}
