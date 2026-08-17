/**
 * Vista de impresión de una receta (RF-037).
 *
 * Es, a la vez, la previsualización: al no tener barra de navegación ni
 * botones (salvo el de imprimir, que se oculta solo al imprimir de
 * verdad), lo que se ve en pantalla es exactamente lo que va a salir en
 * papel. No hace falta una ventana ni un modo aparte para "previsualizar".
 *
 * Admite un parámetro `?rendimiento=N` para imprimir la receta ya
 * escalada -si se llega desde el detalle con las porciones ajustadas, la
 * impresión respeta esa cantidad en lugar de siempre la base.
 */

import { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";

import { ErrorApi, pedir } from "../api/cliente";
import type { Receta, RecetaEscalada } from "../api/tipos";
import { Aviso, Cargando } from "../componentes/Comunes";

export default function ImprimirReceta() {
  const { recetaId = "" } = useParams();
  const [parametros] = useSearchParams();
  const navegar = useNavigate();

  const [receta, setReceta] = useState<Receta | null>(null);
  const [escalada, setEscalada] = useState<RecetaEscalada | null>(null);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const rendimientoPedido = parametros.get("rendimiento");

  useEffect(() => {
    let vigente = true;
    setCargando(true);
    pedir<Receta>(`/recetas/${recetaId}/`)
      .then(async (datos) => {
        if (!vigente) return;
        setReceta(datos);

        const distintoDelBase =
          rendimientoPedido && Number(rendimientoPedido) !== Number(datos.rendimiento_base);
        if (distintoDelBase) {
          const resultado = await pedir<RecetaEscalada>(
            `/recetas/${recetaId}/escalar/`,
            { metodo: "POST", cuerpo: { rendimiento_objetivo: rendimientoPedido } },
          );
          if (vigente) setEscalada(resultado);
        }
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
  }, [recetaId, rendimientoPedido]);

  const preparaciones = useMemo(
    () => escalada?.preparaciones ?? receta?.preparaciones ?? [],
    [escalada, receta],
  );

  const fotoFinal = useMemo(
    () =>
      preparaciones.flatMap((p) => p.fotografias).find((f) => f.tipo === "final"),
    [preparaciones],
  );

  if (cargando) return <Cargando texto="Preparando la receta para imprimir…" />;
  if (!receta) return <Aviso>{error ?? "No se encontró la receta."}</Aviso>;

  const rendimiento = escalada?.rendimiento_solicitado ?? receta.rendimiento_base;

  return (
    <div className="mx-auto max-w-2xl px-4 py-8 print:max-w-full print:p-0">
      {/* Esta barra no sale impresa: `print:hidden` la oculta solo al imprimir. */}
      <div className="mb-6 flex items-center justify-between gap-3 print:hidden">
        <button
          type="button"
          className="text-sm font-medium text-tinta-suave hover:text-azul"
          onClick={() => navegar(`/recetas/${recetaId}`)}
        >
          ← Volver a la receta
        </button>
        <button type="button" className="boton-primario" onClick={() => window.print()}>
          Imprimir
        </button>
      </div>

      {error && <Aviso>{error}</Aviso>}

      <article className="space-y-6 text-tinta print:text-black">
        <header>
          <h1 className="text-3xl font-semibold tracking-tight">{receta.nombre}</h1>
          {receta.descripcion && (
            <p className="mt-1.5 text-tinta-suave print:text-black">
              {receta.descripcion}
            </p>
          )}
          <p className="mt-2 text-sm text-tinta-suave print:text-black">
            Rinde {rendimiento} {receta.rendimiento_descripcion}
            {receta.fuente_nombre && ` · Fuente: ${receta.fuente_nombre}`}
          </p>
        </header>

        {fotoFinal && (
          <img
            src={fotoFinal.ruta}
            alt=""
            className="h-56 w-full rounded-pieza object-cover print:hidden"
          />
        )}

        {preparaciones.map((preparacion) => (
          <section key={preparacion.id} className="break-inside-avoid">
            <h2 className="border-b border-borde pb-1.5 text-xl font-semibold print:border-black">
              {preparacion.nombre}
            </h2>

            <ul className="mt-3 space-y-1">
              {preparacion.ingredientes.map((ingrediente) => (
                <li
                  key={ingrediente.ingrediente_preparacion_id}
                  className="flex justify-between gap-4 text-sm"
                >
                  <span>{ingrediente.nombre}</span>
                  <span className="font-medium">{ingrediente.texto_cantidad}</span>
                </li>
              ))}
            </ul>

            {preparacion.pasos.length > 0 && (
              <ol className="mt-3 space-y-2">
                {preparacion.pasos.map((paso) => (
                  <li key={paso.id} className="flex gap-2 text-sm leading-relaxed">
                    <span className="font-semibold">{paso.orden}.</span>
                    <span>{paso.descripcion}</span>
                  </li>
                ))}
              </ol>
            )}
          </section>
        ))}

        {receta.notas.length > 0 && (
          <section className="break-inside-avoid">
            <h2 className="border-b border-borde pb-1.5 text-xl font-semibold print:border-black">
              Notas
            </h2>
            <ul className="mt-3 space-y-1 text-sm">
              {receta.notas.map((nota) => (
                <li key={nota.id}>{nota.texto}</li>
              ))}
            </ul>
          </section>
        )}
      </article>
    </div>
  );
}
