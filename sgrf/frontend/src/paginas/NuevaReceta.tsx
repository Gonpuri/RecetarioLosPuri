/**
 * Alta de una receta.
 *
 * El formulario refleja la estructura del dominio: una receta se compone
 * de preparaciones, y cada preparación tiene sus ingredientes y sus pasos.
 * Por eso arranca con una preparación ya creada: RN-003 exige al menos
 * una, y pedirla como paso aparte sólo agregaría fricción.
 *
 * También sirve como paso de revisión de la importación (Cap. 7.7, v2.0):
 * si se le pasa `borradorInicial`, precompleta todo con lo que la
 * importación entendió, en lugar de arrancar vacío. Es el mismo
 * formulario porque el problema es el mismo -cargar una receta-, solo que
 * una vez arranca en blanco y la otra ya trae una propuesta.
 */

import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { ErrorApi, pedir } from "../api/cliente";
import {
  AYUDA_ESCALADO,
  ETIQUETAS_ESCALADO,
  UNIDADES,
  type ElementoCatalogo,
  type Receta,
  type RecetaImportada,
  type TipoEscalado,
} from "../api/tipos";
import { Aviso } from "../componentes/Comunes";
import SelectorIngrediente from "../componentes/SelectorIngrediente";

interface IngredienteBorrador {
  ingrediente_id: string;
  tipo_escalado: TipoEscalado;
  cantidad: string;
  unidad: string;
  observacion: string;
}

interface PreparacionBorrador {
  nombre: string;
  ingredientes: IngredienteBorrador[];
  pasos: string[];
}

const INGREDIENTE_VACIO: IngredienteBorrador = {
  ingrediente_id: "",
  tipo_escalado: "lineal",
  cantidad: "",
  unidad: "g",
  observacion: "",
};

const PREPARACION_VACIA: PreparacionBorrador = {
  nombre: "",
  ingredientes: [{ ...INGREDIENTE_VACIO }],
  pasos: [""],
};

/** Traduce el borrador de la importación a la forma que usa este formulario. */
function desdeBorradorImportado(borrador: RecetaImportada): {
  preparaciones: PreparacionBorrador[];
} {
  return {
    preparaciones: borrador.preparaciones.map((preparacion) => ({
      nombre: preparacion.nombre,
      pasos: preparacion.pasos.length > 0 ? preparacion.pasos : [""],
      ingredientes:
        preparacion.ingredientes.length > 0
          ? preparacion.ingredientes.map((ingrediente) => ({
              ingrediente_id: ingrediente.ingrediente_id ?? "",
              tipo_escalado: ingrediente.tipo_escalado,
              cantidad: ingrediente.cantidad ?? "",
              unidad: ingrediente.unidad ?? "g",
              observacion: ingrediente.observacion,
            }))
          : [{ ...INGREDIENTE_VACIO }],
    })),
  };
}

export default function NuevaReceta({
  borradorInicial,
  titulo = "Nueva receta",
}: {
  borradorInicial?: RecetaImportada;
  titulo?: string;
}) {
  const navegar = useNavigate();

  const [nombre, setNombre] = useState(borradorInicial?.nombre ?? "");
  const [descripcion, setDescripcion] = useState(borradorInicial?.descripcion ?? "");
  const [rendimiento, setRendimiento] = useState(
    borradorInicial?.rendimiento_base ?? "4",
  );
  const [unidadRendimiento, setUnidadRendimiento] = useState(
    borradorInicial?.rendimiento_descripcion ?? "porciones",
  );
  const [fuenteId, setFuenteId] = useState("");
  const [preparaciones, setPreparaciones] = useState<PreparacionBorrador[]>(
    borradorInicial
      ? desdeBorradorImportado(borradorInicial).preparaciones
      : [{ ...PREPARACION_VACIA, ingredientes: [{ ...INGREDIENTE_VACIO }], pasos: [""] }],
  );

  const [ingredientes, setIngredientes] = useState<ElementoCatalogo[]>([]);
  const [fuentes, setFuentes] = useState<ElementoCatalogo[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  useEffect(() => {
    Promise.all([
      pedir<ElementoCatalogo[]>("/ingredientes/"),
      pedir<ElementoCatalogo[]>("/fuentes/"),
    ])
      .then(([catalogoIngredientes, catalogoFuentes]) => {
        setIngredientes(catalogoIngredientes);
        setFuentes(catalogoFuentes);

        // Si la importación sugirió una fuente, intentamos encontrarla por
        // nombre entre las que ya existen; si no coincide con ninguna,
        // queda la primera del catálogo, igual que en el alta común.
        const sugerida = borradorInicial?.fuente_sugerida?.trim().toLowerCase();
        const coincidencia = sugerida
          ? catalogoFuentes.find((f) => f.nombre.toLowerCase() === sugerida)
          : undefined;
        if (coincidencia) {
          setFuenteId(coincidencia.id);
        } else if (catalogoFuentes.length > 0) {
          setFuenteId(catalogoFuentes[0].id);
        }
      })
      .catch(() =>
        setError(
          "No se pudieron cargar los ingredientes y las fuentes. Recargá la página.",
        ),
      );
    // Solo se ejecuta al montar: el borrador es fijo durante la revisión.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  /** Aplica un cambio sobre una preparación sin mutar el estado anterior. */
  function actualizarPreparacion(
    indice: number,
    cambio: Partial<PreparacionBorrador>,
  ) {
    setPreparaciones((previas) =>
      previas.map((p, i) => (i === indice ? { ...p, ...cambio } : p)),
    );
  }

  function actualizarIngrediente(
    indicePreparacion: number,
    indiceIngrediente: number,
    cambio: Partial<IngredienteBorrador>,
  ) {
    setPreparaciones((previas) =>
      previas.map((preparacion, i) =>
        i !== indicePreparacion
          ? preparacion
          : {
              ...preparacion,
              ingredientes: preparacion.ingredientes.map((ingrediente, j) =>
                j === indiceIngrediente ? { ...ingrediente, ...cambio } : ingrediente,
              ),
            },
      ),
    );
  }

  async function enviar() {
    setError(null);
    setEnviando(true);
    try {
      const cuerpo = {
        nombre,
        descripcion,
        rendimiento_base: rendimiento,
        rendimiento_descripcion: unidadRendimiento,
        fuente_id: fuenteId,
        preparaciones: preparaciones.map((preparacion) => ({
          nombre: preparacion.nombre,
          pasos: preparacion.pasos.filter((paso) => paso.trim()),
          ingredientes: preparacion.ingredientes
            .filter((ingrediente) => ingrediente.ingrediente_id)
            .map((ingrediente) => {
              const llevaCantidad =
                ingrediente.tipo_escalado === "lineal" ||
                ingrediente.tipo_escalado === "fijo";
              return {
                ingrediente_id: ingrediente.ingrediente_id,
                tipo_escalado: ingrediente.tipo_escalado,
                cantidad: llevaCantidad ? ingrediente.cantidad : null,
                unidad: llevaCantidad ? ingrediente.unidad : null,
                observacion: ingrediente.observacion,
              };
            }),
        })),
      };

      const creada = await pedir<Receta>("/recetas/", {
        metodo: "POST",
        cuerpo,
      });
      navegar(`/recetas/${creada.id}`);
    } catch (fallo) {
      setError(
        fallo instanceof ErrorApi ? fallo.message : "No se pudo guardar la receta.",
      );
    } finally {
      setEnviando(false);
    }
  }

  const faltanCatalogos = fuentes.length === 0 || ingredientes.length === 0;

  return (
    <div className="space-y-5 pb-8">
      <div className="flex items-center justify-between gap-3">
        <h1 className="text-2xl font-semibold tracking-tight">{titulo}</h1>
        {!borradorInicial && (
          <Link
            to="/recetas/importar"
            className="text-sm font-semibold text-azul"
          >
            Importar desde PDF o foto
          </Link>
        )}
      </div>

      {borradorInicial?.advertencia && (
        <Aviso tono="advertencia">{borradorInicial.advertencia}</Aviso>
      )}

      {faltanCatalogos && (
        <Aviso tono="advertencia">
          Antes de cargar recetas hacen falta al menos una fuente y un ingrediente en
          el catálogo. Los crea quien administra el recetario.
        </Aviso>
      )}

      {error && <Aviso>{error}</Aviso>}

      <section className="tarjeta space-y-4 p-4">
        <div>
          <label htmlFor="nombre" className="etiqueta-campo">
            Nombre
          </label>
          <input
            id="nombre"
            className="campo"
            value={nombre}
            onChange={(e) => setNombre(e.target.value)}
            placeholder="Pan casero"
          />
        </div>

        <div>
          <label htmlFor="descripcion" className="etiqueta-campo">
            Descripción
          </label>
          <textarea
            id="descripcion"
            className="campo"
            rows={2}
            value={descripcion}
            onChange={(e) => setDescripcion(e.target.value)}
            placeholder="De dónde viene, cuándo se prepara…"
          />
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label htmlFor="rendimiento" className="etiqueta-campo">
              Rinde
            </label>
            <div className="flex gap-2">
              <input
                id="rendimiento"
                type="number"
                min={1}
                className="campo w-24"
                value={rendimiento}
                onChange={(e) => setRendimiento(e.target.value)}
              />
              <input
                className="campo flex-1"
                value={unidadRendimiento}
                onChange={(e) => setUnidadRendimiento(e.target.value)}
                placeholder="porciones"
                aria-label="Unidad del rendimiento"
              />
            </div>
            <p className="mt-1 text-sm text-tinta-tenue">
              Es la cantidad original. Después se puede ajustar sin perderla.
            </p>
          </div>

          <div>
            <label htmlFor="fuente" className="etiqueta-campo">
              Fuente
            </label>
            <select
              id="fuente"
              className="campo"
              value={fuenteId}
              onChange={(e) => setFuenteId(e.target.value)}
            >
              {fuentes.map((fuente) => (
                <option key={fuente.id} value={fuente.id}>
                  {fuente.nombre}
                </option>
              ))}
            </select>
          </div>
        </div>
      </section>

      {preparaciones.map((preparacion, indicePreparacion) => (
        <section key={indicePreparacion} className="tarjeta space-y-4 p-4">
          <div className="flex items-center gap-3">
            <input
              className="campo flex-1 font-semibold"
              value={preparacion.nombre}
              onChange={(e) =>
                actualizarPreparacion(indicePreparacion, { nombre: e.target.value })
              }
              placeholder={`Preparación ${indicePreparacion + 1}: masa, salsa, armado…`}
              aria-label="Nombre de la preparación"
            />
            {preparaciones.length > 1 && (
              <button
                type="button"
                className="text-sm font-medium text-error"
                onClick={() =>
                  setPreparaciones((previas) =>
                    previas.filter((_, i) => i !== indicePreparacion),
                  )
                }
              >
                Quitar
              </button>
            )}
          </div>

          <div className="space-y-3">
            <h3 className="text-sm font-semibold text-tinta-suave">Ingredientes</h3>

            {preparacion.ingredientes.map((ingrediente, indiceIngrediente) => {
              const llevaCantidad =
                ingrediente.tipo_escalado === "lineal" ||
                ingrediente.tipo_escalado === "fijo";
              return (
                <div
                  key={indiceIngrediente}
                  className="space-y-2 rounded-pieza border border-borde p-3"
                >
                  <div className="flex gap-2">
                    <SelectorIngrediente
                      ingredientes={ingredientes}
                      valor={ingrediente.ingrediente_id}
                      onCambiar={(id) =>
                        actualizarIngrediente(indicePreparacion, indiceIngrediente, {
                          ingrediente_id: id,
                        })
                      }
                      onCreado={(nuevo) =>
                        setIngredientes((previos) => [...previos, nuevo])
                      }
                    />

                    {preparacion.ingredientes.length > 1 && (
                      <button
                        type="button"
                        className="px-2 text-sm font-medium text-error"
                        onClick={() =>
                          actualizarPreparacion(indicePreparacion, {
                            ingredientes: preparacion.ingredientes.filter(
                              (_, j) => j !== indiceIngrediente,
                            ),
                          })
                        }
                        aria-label="Quitar ingrediente"
                      >
                        ✕
                      </button>
                    )}
                  </div>

                  <div className="flex flex-wrap gap-2">
                    <select
                      className="campo flex-1 min-w-[10rem]"
                      value={ingrediente.tipo_escalado}
                      onChange={(e) =>
                        actualizarIngrediente(indicePreparacion, indiceIngrediente, {
                          tipo_escalado: e.target.value as TipoEscalado,
                        })
                      }
                      aria-label="Comportamiento al escalar"
                    >
                      {Object.entries(ETIQUETAS_ESCALADO).map(([clave, texto]) => (
                        <option key={clave} value={clave}>
                          {texto}
                        </option>
                      ))}
                    </select>

                    {llevaCantidad && (
                      <>
                        <input
                          type="number"
                          step="0.001"
                          min={0}
                          className="campo w-24"
                          value={ingrediente.cantidad}
                          onChange={(e) =>
                            actualizarIngrediente(
                              indicePreparacion,
                              indiceIngrediente,
                              { cantidad: e.target.value },
                            )
                          }
                          placeholder="500"
                          aria-label="Cantidad"
                        />
                        <select
                          className="campo w-28"
                          value={ingrediente.unidad}
                          onChange={(e) =>
                            actualizarIngrediente(
                              indicePreparacion,
                              indiceIngrediente,
                              { unidad: e.target.value },
                            )
                          }
                          aria-label="Unidad"
                        >
                          {UNIDADES.map((unidad) => (
                            <option key={unidad.simbolo} value={unidad.simbolo}>
                              {unidad.simbolo}
                            </option>
                          ))}
                        </select>
                      </>
                    )}
                  </div>

                  <p className="text-sm text-tinta-tenue">
                    {AYUDA_ESCALADO[ingrediente.tipo_escalado]}
                  </p>
                </div>
              );
            })}

            <button
              type="button"
              className="text-sm font-semibold text-azul"
              onClick={() =>
                actualizarPreparacion(indicePreparacion, {
                  ingredientes: [
                    ...preparacion.ingredientes,
                    { ...INGREDIENTE_VACIO },
                  ],
                })
              }
            >
              + Agregar ingrediente
            </button>
          </div>

          <div className="space-y-2">
            <h3 className="text-sm font-semibold text-tinta-suave">Pasos</h3>
            {preparacion.pasos.map((paso, indicePaso) => (
              <div key={indicePaso} className="flex gap-2">
                <span className="grid h-11 w-8 shrink-0 place-items-center text-sm font-semibold text-tinta-tenue">
                  {indicePaso + 1}
                </span>
                <input
                  className="campo flex-1"
                  value={paso}
                  onChange={(e) =>
                    actualizarPreparacion(indicePreparacion, {
                      pasos: preparacion.pasos.map((valor, j) =>
                        j === indicePaso ? e.target.value : valor,
                      ),
                    })
                  }
                  placeholder="Mezclar los ingredientes secos."
                  aria-label={`Paso ${indicePaso + 1}`}
                />
              </div>
            ))}
            <button
              type="button"
              className="text-sm font-semibold text-azul"
              onClick={() =>
                actualizarPreparacion(indicePreparacion, {
                  pasos: [...preparacion.pasos, ""],
                })
              }
            >
              + Agregar paso
            </button>
          </div>
        </section>
      ))}

      <button
        type="button"
        className="boton-secundario w-full"
        onClick={() =>
          setPreparaciones((previas) => [
            ...previas,
            {
              nombre: "",
              ingredientes: [{ ...INGREDIENTE_VACIO }],
              pasos: [""],
            },
          ])
        }
      >
        + Agregar otra preparación
      </button>

      <div className="flex gap-3">
        <button
          type="button"
          className="boton-primario flex-1"
          onClick={enviar}
          disabled={enviando || faltanCatalogos}
        >
          {enviando ? "Guardando…" : "Guardar receta"}
        </button>
        <button
          type="button"
          className="boton-secundario"
          onClick={() => navegar("/recetas")}
        >
          Cancelar
        </button>
      </div>
    </div>
  );
}
