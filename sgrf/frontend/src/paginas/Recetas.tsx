/**
 * Listado y búsqueda de recetas.
 *
 * Es la puerta de entrada al recetario. El Capítulo 6.12 pide no más de
 * tres toques para abrir una receta: desde acá es uno solo.
 *
 * Los filtros por ingrediente, categoría, etiqueta y fuente (RF-039 a
 * RF-042) están plegados detrás de "Más filtros": la búsqueda por nombre
 * resuelve la mayoría de los casos, y ocupar la pantalla con cuatro listas
 * desplegables iría contra la simplicidad que pide el Capítulo 6.3.
 */

import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { ErrorApi, pedir } from "../api/cliente";
import type { ElementoCatalogo, RecetaResumen } from "../api/tipos";
import { Aviso, Cargando, Estrella, Vacio } from "../componentes/Comunes";

/** Espera a que la persona deje de escribir antes de consultar al servidor. */
function useTextoDemorado(texto: string, milisegundos = 300): string {
  const [demorado, setDemorado] = useState(texto);
  useEffect(() => {
    const temporizador = setTimeout(() => setDemorado(texto), milisegundos);
    return () => clearTimeout(temporizador);
  }, [texto, milisegundos]);
  return demorado;
}

interface Filtros {
  ingrediente_id: string;
  categoria_id: string;
  etiqueta_id: string;
  fuente_id: string;
}

const FILTROS_VACIOS: Filtros = {
  ingrediente_id: "",
  categoria_id: "",
  etiqueta_id: "",
  fuente_id: "",
};

const CAMPOS_FILTRO: { clave: keyof Filtros; etiqueta: string; ruta: string }[] = [
  { clave: "ingrediente_id", etiqueta: "Lleva el ingrediente", ruta: "ingredientes" },
  { clave: "categoria_id", etiqueta: "De la categoría", ruta: "categorias" },
  { clave: "etiqueta_id", etiqueta: "Con la etiqueta", ruta: "etiquetas" },
  { clave: "fuente_id", etiqueta: "De la fuente", ruta: "fuentes" },
];

function TarjetaReceta({ receta }: { receta: RecetaResumen }) {
  return (
    <Link
      to={`/recetas/${receta.id}`}
      className="tarjeta group flex items-center gap-4 p-4 transition-shadow hover:shadow-elevada"
    >
      <div className="h-16 w-16 shrink-0 overflow-hidden rounded-pieza bg-azul-claro">
        {receta.fotografia_final ? (
          <img
            src={receta.fotografia_final}
            alt=""
            loading="lazy"
            className="h-full w-full object-cover"
          />
        ) : (
          <span className="grid h-full w-full place-items-center text-xl font-semibold text-azul-medio">
            {receta.nombre.charAt(0).toUpperCase()}
          </span>
        )}
      </div>

      <div className="min-w-0 flex-1">
        <h2 className="truncate font-semibold text-tinta group-hover:text-azul">
          {receta.nombre}
        </h2>
        <p className="mt-0.5 text-sm text-tinta-suave">
          Rinde {receta.rendimiento_base} {receta.rendimiento_descripcion}
        </p>
        {receta.archivada && (
          <span className="mt-1.5 inline-block text-xs font-medium text-advertencia">
            Archivada
          </span>
        )}
      </div>

      {receta.favorita && (
        <span className="text-advertencia" title="Favorita">
          <Estrella activa />
        </span>
      )}
    </Link>
  );
}

export default function Recetas({
  soloFavoritas = false,
}: {
  soloFavoritas?: boolean;
}) {
  const [texto, setTexto] = useState("");
  const [filtros, setFiltros] = useState<Filtros>(FILTROS_VACIOS);
  const [mostrarFiltros, setMostrarFiltros] = useState(false);
  const [incluirArchivadas, setIncluirArchivadas] = useState(false);

  const [catalogos, setCatalogos] = useState<Record<string, ElementoCatalogo[]>>({});
  const [recetas, setRecetas] = useState<RecetaResumen[]>([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const busqueda = useTextoDemorado(texto);
  const filtrosActivos = Object.values(filtros).filter(Boolean).length;

  // Los catálogos se piden una sola vez, recién al abrir los filtros.
  useEffect(() => {
    if (!mostrarFiltros || Object.keys(catalogos).length > 0) return;
    Promise.all(
      CAMPOS_FILTRO.map((campo) =>
        pedir<ElementoCatalogo[]>(`/${campo.ruta}/`).then(
          (datos) => [campo.ruta, datos] as const,
        ),
      ),
    )
      .then((pares) => setCatalogos(Object.fromEntries(pares)))
      .catch(() => setError("No se pudieron cargar los filtros."));
  }, [mostrarFiltros, catalogos]);

  const buscar = useCallback(async () => {
    setCargando(true);
    setError(null);
    try {
      const parametros = new URLSearchParams();
      if (busqueda.trim()) parametros.set("texto", busqueda.trim());
      if (soloFavoritas) parametros.set("solo_favoritas", "true");
      if (incluirArchivadas) parametros.set("incluir_archivadas", "true");
      for (const [clave, valor] of Object.entries(filtros)) {
        if (valor) parametros.set(clave, valor);
      }

      const consulta = parametros.toString();
      setRecetas(
        await pedir<RecetaResumen[]>(`/recetas/${consulta ? `?${consulta}` : ""}`),
      );
    } catch (fallo) {
      setError(
        fallo instanceof ErrorApi ? fallo.message : "No se pudo cargar el recetario.",
      );
    } finally {
      setCargando(false);
    }
  }, [busqueda, soloFavoritas, incluirArchivadas, filtros]);

  useEffect(() => {
    void buscar();
  }, [buscar]);

  const hayCriterios = Boolean(busqueda.trim()) || filtrosActivos > 0;

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between gap-4">
        <h1 className="text-2xl font-semibold tracking-tight">
          {soloFavoritas ? "Favoritas" : "Recetas"}
        </h1>
        <Link to="/recetas/nueva" className="boton-primario">
          Nueva receta
        </Link>
      </div>

      {/* Capítulo 6.5: la búsqueda está disponible desde la pantalla principal. */}
      <div className="space-y-3">
        <label htmlFor="buscar" className="sr-only">
          Buscar recetas
        </label>
        <input
          id="buscar"
          type="search"
          className="campo"
          placeholder="Buscar por nombre…"
          value={texto}
          onChange={(e) => setTexto(e.target.value)}
        />

        <div className="flex flex-wrap items-center gap-4">
          <button
            type="button"
            onClick={() => setMostrarFiltros((previo) => !previo)}
            className="text-sm font-semibold text-azul"
            aria-expanded={mostrarFiltros}
          >
            {mostrarFiltros ? "Ocultar filtros" : "Más filtros"}
            {filtrosActivos > 0 && ` (${filtrosActivos})`}
          </button>

          <label className="flex items-center gap-2 text-sm text-tinta-suave">
            <input
              type="checkbox"
              className="h-4 w-4 rounded border-borde text-azul focus:ring-azul"
              checked={incluirArchivadas}
              onChange={(e) => setIncluirArchivadas(e.target.checked)}
            />
            Mostrar también las archivadas
          </label>
        </div>

        {mostrarFiltros && (
          <section className="tarjeta space-y-3 p-4">
            {CAMPOS_FILTRO.map((campo) => (
              <div key={campo.clave}>
                <label htmlFor={campo.clave} className="etiqueta-campo">
                  {campo.etiqueta}
                </label>
                <select
                  id={campo.clave}
                  className="campo"
                  value={filtros[campo.clave]}
                  onChange={(e) =>
                    setFiltros((previos) => ({
                      ...previos,
                      [campo.clave]: e.target.value,
                    }))
                  }
                >
                  <option value="">Cualquiera</option>
                  {(catalogos[campo.ruta] ?? []).map((item) => (
                    <option key={item.id} value={item.id}>
                      {item.nombre}
                    </option>
                  ))}
                </select>
              </div>
            ))}

            {filtrosActivos > 0 && (
              <button
                type="button"
                className="text-sm font-semibold text-azul"
                onClick={() => setFiltros(FILTROS_VACIOS)}
              >
                Quitar los filtros
              </button>
            )}
          </section>
        )}
      </div>

      {error && <Aviso>{error}</Aviso>}

      {cargando ? (
        <Cargando texto="Buscando recetas…" />
      ) : recetas.length === 0 ? (
        <Vacio
          titulo={hayCriterios ? "Ninguna receta coincide" : "Todavía no hay recetas"}
          descripcion={
            hayCriterios
              ? "Probá con otras palabras, quitá algún filtro o revisá si la receta está archivada."
              : "Cargá la primera receta de la familia y empezá a construir el recetario."
          }
          accion={
            !hayCriterios && (
              <Link to="/recetas/nueva" className="boton-primario">
                Cargar la primera receta
              </Link>
            )
          }
        />
      ) : (
        <div className="space-y-3">
          {recetas.map((receta) => (
            <TarjetaReceta key={receta.id} receta={receta} />
          ))}
        </div>
      )}
    </div>
  );
}
