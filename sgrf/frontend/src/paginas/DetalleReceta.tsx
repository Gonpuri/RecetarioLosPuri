/**
 * Detalle de una receta: la pantalla donde se cocina.
 *
 * Concentra el recorrido del Capítulo 6.8 completo. El control de
 * rendimiento está siempre visible (Capítulo 6.12) y los ingredientes
 * tienen más peso visual que los datos administrativos.
 *
 * El escalado no altera nada: pide el cálculo al servidor y muestra el
 * resultado. La receta guardada conserva siempre su rendimiento base
 * (RN-004), y así lo indica la pantalla cuando se está viendo escalada.
 */

import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { ErrorApi, pedir } from "../api/cliente";
import type {
  ListaCompra,
  Preparacion,
  Receta,
  RecetaEscalada,
} from "../api/tipos";
import { Aviso, Cargando, Estrella } from "../componentes/Comunes";

/** Control de rendimiento. Es el corazón de la pantalla. */
function Rendimiento({
  valor,
  descripcion,
  base,
  onCambiar,
  onRestablecer,
}: {
  valor: number;
  descripcion: string;
  base: number;
  onCambiar: (nuevo: number) => void;
  onRestablecer: () => void;
}) {
  const escalada = valor !== base;

  return (
    <section className="tarjeta overflow-hidden">
      <div className="flex flex-wrap items-center gap-4 p-4">
        <div className="mr-auto">
          <p className="text-sm font-medium text-tinta-suave">Preparar para</p>
          <p className="mt-0.5 text-sm text-tinta-tenue">
            La receta original rinde {base} {descripcion}
          </p>
        </div>

        <div className="flex items-center gap-1 rounded-pieza border border-borde p-1">
          <button
            type="button"
            className="h-11 w-11 rounded-md text-xl font-semibold text-azul transition-colors hover:bg-azul-claro disabled:opacity-30"
            onClick={() => onCambiar(valor - 1)}
            disabled={valor <= 1}
            aria-label="Reducir el rendimiento"
          >
            −
          </button>

          <label className="sr-only" htmlFor="rendimiento">
            Rendimiento deseado
          </label>
          <input
            id="rendimiento"
            type="number"
            min={1}
            inputMode="numeric"
            className="w-16 border-0 bg-transparent text-center text-xl font-semibold text-tinta focus:outline-none"
            value={valor}
            onChange={(e) => onCambiar(Number(e.target.value) || 1)}
          />

          <button
            type="button"
            className="h-11 w-11 rounded-md text-xl font-semibold text-azul transition-colors hover:bg-azul-claro"
            onClick={() => onCambiar(valor + 1)}
            aria-label="Aumentar el rendimiento"
          >
            +
          </button>
        </div>

        <span className="text-base font-medium text-tinta-suave">{descripcion}</span>
      </div>

      {escalada && (
        <p className="flex flex-wrap items-center gap-2 border-t border-azul/20 bg-azul-claro px-4 py-2.5 text-sm text-azul-oscuro">
          Estás viendo las cantidades ajustadas. La receta guardada no cambia.
          <button
            type="button"
            onClick={onRestablecer}
            className="font-semibold underline underline-offset-2"
          >
            Volver al original
          </button>
        </p>
      )}
    </section>
  );
}

/** Preparación con sus ingredientes marcables y sus pasos. */
function BloquePreparacion({
  preparacion,
  seleccionados,
  alternar,
}: {
  preparacion: Preparacion;
  seleccionados: Set<string>;
  alternar: (id: string) => void;
}) {
  return (
    <section className="tarjeta overflow-hidden">
      <h2 className="border-b border-borde bg-papel px-4 py-3 font-semibold tracking-tight">
        {preparacion.nombre}
      </h2>

      <ul className="divide-y divide-borde">
        {preparacion.ingredientes.map((ingrediente) => {
          const marcado = seleccionados.has(
            ingrediente.ingrediente_preparacion_id,
          );
          return (
            <li key={ingrediente.ingrediente_preparacion_id}>
              <label className="flex cursor-pointer items-center gap-3 px-4 py-3 transition-colors hover:bg-azul-claro/40">
                <input
                  type="checkbox"
                  className="h-5 w-5 shrink-0 rounded border-borde text-azul focus:ring-azul"
                  checked={marcado}
                  onChange={() => alternar(ingrediente.ingrediente_preparacion_id)}
                />
                <span className="min-w-0 flex-1">
                  <span className="block truncate font-medium">
                    {ingrediente.nombre}
                  </span>
                  {ingrediente.observacion && (
                    <span className="block truncate text-sm text-tinta-suave">
                      {ingrediente.observacion}
                    </span>
                  )}
                </span>
                {/* Las cantidades son lo que se lee cocinando: tipografía mayor. */}
                <span className="shrink-0 text-cantidad tabular-nums text-azul-oscuro">
                  {ingrediente.texto_cantidad}
                </span>
              </label>
            </li>
          );
        })}
      </ul>

      {preparacion.pasos.length > 0 && (
        <ol className="space-y-3 border-t border-borde px-4 py-4">
          {preparacion.pasos.map((paso) => (
            <li key={paso.id} className="flex gap-3">
              <span className="grid h-7 w-7 shrink-0 place-items-center rounded-full bg-azul-claro text-sm font-semibold text-azul-oscuro">
                {paso.orden}
              </span>
              <p className="pt-0.5 leading-relaxed">{paso.descripcion}</p>
            </li>
          ))}
        </ol>
      )}

      {preparacion.fotografias.length > 0 && (
        <div className="flex gap-2 overflow-x-auto border-t border-borde px-4 py-3">
          {preparacion.fotografias
            .filter((foto) => foto.tipo === "proceso")
            .map((foto) => (
              <a
                key={foto.id}
                href={foto.ruta}
                target="_blank"
                rel="noreferrer"
                className="shrink-0"
              >
                <img
                  src={foto.ruta}
                  alt={foto.descripcion || `Foto del proceso de ${preparacion.nombre}`}
                  loading="lazy"
                  className="h-20 w-20 rounded-pieza object-cover"
                />
              </a>
            ))}
        </div>
      )}
    </section>
  );
}

export default function DetalleReceta() {
  const { recetaId = "" } = useParams();
  const navegar = useNavigate();

  const [receta, setReceta] = useState<Receta | null>(null);
  const [escalada, setEscalada] = useState<RecetaEscalada | null>(null);
  const [rendimiento, setRendimiento] = useState<number | null>(null);
  const [seleccionados, setSeleccionados] = useState<Set<string>>(new Set());
  const [lista, setLista] = useState<ListaCompra | null>(null);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [nombresCategorias, setNombresCategorias] = useState<Record<string, string>>(
    {},
  );
  const [nombresEtiquetas, setNombresEtiquetas] = useState<Record<string, string>>(
    {},
  );

  const base = receta ? Number(receta.rendimiento_base) : 0;

  useEffect(() => {
    let vigente = true;
    setCargando(true);
    pedir<Receta>(`/recetas/${recetaId}/`)
      .then((datos) => {
        if (!vigente) return;
        setReceta(datos);
        setRendimiento(Number(datos.rendimiento_base));
      })
      .catch((fallo) =>
        setError(
          fallo instanceof ErrorApi ? fallo.message : "No se pudo abrir la receta.",
        ),
      )
      .finally(() => vigente && setCargando(false));
    return () => {
      vigente = false;
    };
  }, [recetaId]);

  // Resuelve los nombres de categorías y etiquetas para mostrarlos en la
  // receta, no solo usarlos como filtro en el listado.
  useEffect(() => {
    let vigente = true;
    Promise.all([
      pedir<{ id: string; nombre: string }[]>("/categorias/"),
      pedir<{ id: string; nombre: string }[]>("/etiquetas/"),
    ])
      .then(([categorias, etiquetas]) => {
        if (!vigente) return;
        setNombresCategorias(
          Object.fromEntries(categorias.map((c) => [c.id, c.nombre])),
        );
        setNombresEtiquetas(
          Object.fromEntries(etiquetas.map((e) => [e.id, e.nombre])),
        );
      })
      .catch(() => {
        // La clasificación es un detalle adicional: si no se puede cargar,
        // el resto de la receta sigue siendo utilizable.
      });
    return () => {
      vigente = false;
    };
  }, []);

  // Pide el cálculo al servidor sólo cuando el rendimiento difiere del base.
  useEffect(() => {
    if (!receta || rendimiento === null || rendimiento === base) {
      setEscalada(null);
      return;
    }
    let vigente = true;
    const temporizador = setTimeout(() => {
      pedir<RecetaEscalada>(`/recetas/${recetaId}/escalar/`, {
        metodo: "POST",
        cuerpo: { rendimiento_objetivo: rendimiento },
      })
        .then((datos) => vigente && setEscalada(datos))
        .catch((fallo) =>
          setError(
            fallo instanceof ErrorApi ? fallo.message : "No se pudo escalar la receta.",
          ),
        );
    }, 250);
    return () => {
      vigente = false;
      clearTimeout(temporizador);
    };
  }, [rendimiento, base, receta, recetaId]);

  const preparaciones = useMemo(
    () => escalada?.preparaciones ?? receta?.preparaciones ?? [],
    [escalada, receta],
  );

  const fotoFinal = useMemo(
    () =>
      preparaciones
        .flatMap((p) => p.fotografias)
        .find((foto) => foto.tipo === "final"),
    [preparaciones],
  );

  const alternar = useCallback((id: string) => {
    setSeleccionados((previos) => {
      const copia = new Set(previos);
      copia.has(id) ? copia.delete(id) : copia.add(id);
      return copia;
    });
  }, []);

  async function generarLista() {
    setError(null);
    try {
      const resultado = await pedir<ListaCompra>(
        `/recetas/${recetaId}/lista-compras/`,
        {
          metodo: "POST",
          cuerpo: {
            ingredientes_seleccionados: [...seleccionados],
            rendimiento_objetivo: rendimiento,
            persistir: true,
          },
        },
      );
      setLista(resultado);
    } catch (fallo) {
      setError(
        fallo instanceof ErrorApi
          ? fallo.message
          : "No se pudo armar la lista de compras.",
      );
    }
  }

  async function alternarFavorita() {
    if (!receta) return;
    const nuevo = !receta.favorita;
    setReceta({ ...receta, favorita: nuevo });
    try {
      await pedir(`/recetas/${recetaId}/favorita/`, {
        metodo: "POST",
        cuerpo: { favorita: nuevo },
      });
    } catch {
      setReceta({ ...receta, favorita: !nuevo });
    }
  }

  async function archivar() {
    try {
      await pedir(`/recetas/${recetaId}/archivar/`, { metodo: "POST" });
      navegar("/recetas");
    } catch (fallo) {
      setError(
        fallo instanceof ErrorApi ? fallo.message : "No se pudo archivar la receta.",
      );
    }
  }

  /**
   * Crea una variante de la receta (RF-010).
   *
   * La copia es independiente: editarla jamás afecta a la original
   * (RN-004). Se pide el nombre porque no puede repetirse.
   */
  async function duplicar() {
    if (!receta) return;
    const nombre = window.prompt(
      "¿Cómo se va a llamar la variante?",
      `${receta.nombre} (variante)`,
    );
    if (!nombre?.trim()) return;

    setError(null);
    try {
      const variante = await pedir<Receta>(`/recetas/${recetaId}/duplicar/`, {
        metodo: "POST",
        cuerpo: { nombre: nombre.trim() },
      });
      navegar(`/recetas/${variante.id}/editar`);
    } catch (fallo) {
      setError(
        fallo instanceof ErrorApi ? fallo.message : "No se pudo duplicar la receta.",
      );
    }
  }

  if (cargando) return <Cargando texto="Abriendo la receta…" />;
  if (!receta) return <Aviso>{error ?? "No se encontró la receta."}</Aviso>;

  return (
    <div className="space-y-5">
      <div>
        <Link
          to="/recetas"
          className="text-sm font-medium text-tinta-suave hover:text-azul"
        >
          ← Volver a las recetas
        </Link>

        <div className="mt-2 flex items-start gap-3">
          <div className="min-w-0 flex-1">
            <h1 className="text-2xl font-semibold tracking-tight">{receta.nombre}</h1>
            {receta.descripcion && (
              <p className="mt-1 text-tinta-suave">{receta.descripcion}</p>
            )}
            <p className="mt-1 text-sm text-tinta-tenue">
              Fuente: {receta.fuente_nombre || "sin registrar"}
            </p>

            {(receta.categorias_ids.length > 0 || receta.etiquetas_ids.length > 0) && (
              <div className="mt-2 flex flex-wrap gap-1.5">
                {receta.categorias_ids.map((id) => (
                  <span key={id} className="chip">
                    {nombresCategorias[id] ?? "…"}
                  </span>
                ))}
                {receta.etiquetas_ids.map((id) => (
                  <span
                    key={id}
                    className="inline-flex items-center rounded-full border border-borde px-3 py-1 text-sm text-tinta-suave"
                  >
                    {nombresEtiquetas[id] ?? "…"}
                  </span>
                ))}
              </div>
            )}
          </div>

          <button
            type="button"
            onClick={alternarFavorita}
            className={`rounded-pieza border border-borde p-2.5 transition-colors ${
              receta.favorita ? "text-advertencia" : "text-tinta-tenue hover:text-azul"
            }`}
            aria-pressed={receta.favorita}
            aria-label={
              receta.favorita ? "Quitar de favoritas" : "Marcar como favorita"
            }
          >
            <Estrella activa={receta.favorita} />
          </button>
        </div>
      </div>

      {error && <Aviso>{error}</Aviso>}

      {fotoFinal && (
        <img
          src={fotoFinal.ruta}
          alt={fotoFinal.descripcion || `Foto final de ${receta.nombre}`}
          className="h-56 w-full rounded-pieza object-cover sm:h-72"
        />
      )}

      {rendimiento !== null && (
        <Rendimiento
          valor={rendimiento}
          descripcion={receta.rendimiento_descripcion}
          base={base}
          onCambiar={(nuevo) => setRendimiento(Math.max(1, nuevo))}
          onRestablecer={() => setRendimiento(base)}
        />
      )}

      <p className="text-sm text-tinta-suave">
        Marcá lo que te falta para armar la lista de compras.
      </p>

      {preparaciones.map((preparacion) => (
        <BloquePreparacion
          key={preparacion.id}
          preparacion={preparacion}
          seleccionados={seleccionados}
          alternar={alternar}
        />
      ))}

      {receta.notas.length > 0 && (
        <section className="tarjeta p-4">
          <h2 className="mb-2 font-semibold tracking-tight">Notas</h2>
          <ul className="space-y-2">
            {receta.notas.map((nota) => (
              <li key={nota.id} className="text-tinta-suave">
                {nota.texto}
              </li>
            ))}
          </ul>
        </section>
      )}

      {lista && (
        <section className="tarjeta overflow-hidden">
          <h2 className="border-b border-borde bg-exito/5 px-4 py-3 font-semibold text-exito">
            Lista de compras
          </h2>
          <ul className="divide-y divide-borde">
            {lista.items.map((item) => (
              <li key={item.id} className="flex items-center gap-3 px-4 py-3">
                <span className="flex-1 font-medium">{item.nombre}</span>
                <span className="text-cantidad tabular-nums text-azul-oscuro">
                  {item.texto_cantidad}
                </span>
              </li>
            ))}
          </ul>
          <div className="px-4 py-3">
            <Link to="/lista-compras" className="boton-secundario w-full">
              Ver todas mis listas
            </Link>
          </div>
        </section>
      )}

      <div className="flex flex-wrap gap-3 pb-4">
        <button
          type="button"
          className="boton-primario flex-1"
          onClick={generarLista}
          disabled={seleccionados.size === 0}
        >
          {seleccionados.size === 0
            ? "Marcá lo que te falta"
            : `Armar lista (${seleccionados.size})`}
        </button>
        <Link to={`/recetas/${recetaId}/editar`} className="boton-secundario">
          Editar
        </Link>
        <button type="button" className="boton-secundario" onClick={duplicar}>
          Duplicar
        </button>
        <button type="button" className="boton-secundario" onClick={archivar}>
          Archivar
        </button>
      </div>
    </div>
  );
}
