/**
 * Edición de una receta existente.
 *
 * A diferencia del alta, acá cada cambio se guarda por separado contra la
 * API. Editar una receta cargada es una tarea de a ratos —se corrige un
 * paso, se ajusta una cantidad—, y perder todo por cerrar la pestaña sería
 * peor que la molestia de no tener un botón "Guardar" único.
 *
 * Una receta archivada no se puede editar (decisión D-4): la pantalla lo
 * dice y ofrece restaurarla.
 */

import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { ErrorApi, pedir } from "../api/cliente";
import {
  AYUDA_ESCALADO,
  ETIQUETAS_ESCALADO,
  UNIDADES,
  type ElementoCatalogo,
  type Ingrediente,
  type Preparacion,
  type Receta,
  type TipoEscalado,
  type TipoFotografia,
} from "../api/tipos";
import { Aviso, Cargando } from "../componentes/Comunes";
import Reordenar, { moverElemento } from "../componentes/Reordenar";
import SubirFotografia from "../componentes/SubirFotografia";

const MAXIMO_PROCESO = 2;
const MAXIMO_FINAL = 1;

export default function EditarReceta() {
  const { recetaId = "" } = useParams();
  const navegar = useNavigate();

  const [receta, setReceta] = useState<Receta | null>(null);
  const [ingredientes, setIngredientes] = useState<ElementoCatalogo[]>([]);
  const [fuentes, setFuentes] = useState<ElementoCatalogo[]>([]);
  const [categorias, setCategorias] = useState<ElementoCatalogo[]>([]);
  const [etiquetas, setEtiquetas] = useState<ElementoCatalogo[]>([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [guardado, setGuardado] = useState<string | null>(null);

  const recargar = useCallback(async () => {
    setReceta(await pedir<Receta>(`/recetas/${recetaId}/`));
  }, [recetaId]);

  useEffect(() => {
    Promise.all([
      pedir<Receta>(`/recetas/${recetaId}/`),
      pedir<ElementoCatalogo[]>("/ingredientes/"),
      pedir<ElementoCatalogo[]>("/fuentes/"),
      pedir<ElementoCatalogo[]>("/categorias/"),
      pedir<ElementoCatalogo[]>("/etiquetas/"),
    ])
      .then(([datosReceta, catalogo, catalogoFuentes, cats, etiqs]) => {
        setReceta(datosReceta);
        setIngredientes(catalogo);
        setFuentes(catalogoFuentes);
        setCategorias(cats);
        setEtiquetas(etiqs);
      })
      .catch((fallo) =>
        setError(
          fallo instanceof ErrorApi ? fallo.message : "No se pudo abrir la receta.",
        ),
      )
      .finally(() => setCargando(false));
  }, [recetaId]);

  /** Ejecuta una operación contra la API y refresca la receta. */
  const operar = useCallback(
    async (accion: () => Promise<unknown>, mensaje = "Guardado") => {
      setError(null);
      try {
        await accion();
        await recargar();
        setGuardado(mensaje);
        setTimeout(() => setGuardado(null), 2000);
      } catch (fallo) {
        setError(
          fallo instanceof ErrorApi
            ? fallo.message
            : "No se pudo guardar el cambio.",
        );
      }
    },
    [recargar],
  );

  if (cargando) return <Cargando texto="Abriendo la receta…" />;
  if (!receta) return <Aviso>{error ?? "No se encontró la receta."}</Aviso>;

  if (receta.archivada) {
    return (
      <div className="space-y-4">
        <h1 className="text-2xl font-semibold tracking-tight">{receta.nombre}</h1>
        <Aviso tono="advertencia">
          Esta receta está archivada. Restaurala para poder editarla.
        </Aviso>
        <button
          type="button"
          className="boton-primario"
          onClick={() =>
            operar(
              () =>
                pedir(`/recetas/${recetaId}/archivar/`, { metodo: "DELETE" }),
              "Receta restaurada",
            )
          }
        >
          Restaurar receta
        </button>
      </div>
    );
  }

  const fotosProceso = receta.preparaciones.flatMap((p) =>
    p.fotografias.filter((f) => f.tipo === "proceso"),
  );
  const fotosFinal = receta.preparaciones.flatMap((p) =>
    p.fotografias.filter((f) => f.tipo === "final"),
  );
  const tiposDisponibles: TipoFotografia[] = [
    ...(fotosProceso.length < MAXIMO_PROCESO ? (["proceso"] as const) : []),
    ...(fotosFinal.length < MAXIMO_FINAL ? (["final"] as const) : []),
  ];

  return (
    <div className="space-y-5 pb-8">
      <div>
        <Link
          to={`/recetas/${recetaId}`}
          className="text-sm font-medium text-tinta-suave hover:text-azul"
        >
          ← Volver a la receta
        </Link>
        <h1 className="mt-2 text-2xl font-semibold tracking-tight">
          Editar {receta.nombre}
        </h1>
      </div>

      {error && <Aviso>{error}</Aviso>}
      {guardado && <Aviso tono="exito">{guardado}</Aviso>}

      <DatosGenerales receta={receta} fuentes={fuentes} operar={operar} />

      {receta.preparaciones.map((preparacion, indice) => (
        <BloqueEdicion
          key={preparacion.id}
          recetaId={recetaId}
          preparacion={preparacion}
          indice={indice}
          total={receta.preparaciones.length}
          ingredientes={ingredientes}
          puedeEliminar={receta.preparaciones.length > 1}
          tiposDisponibles={tiposDisponibles}
          operar={operar}
          recargar={recargar}
          onMover={(destino) =>
            operar(
              () =>
                pedir(`/recetas/${recetaId}/preparaciones/reordenar/`, {
                  metodo: "POST",
                  cuerpo: {
                    ids_en_orden: moverElemento(
                      receta.preparaciones.map((p) => p.id),
                      indice,
                      destino,
                    ),
                  },
                }),
              "Preparaciones reordenadas",
            )
          }
        />
      ))}

      <AgregarPreparacion recetaId={recetaId} operar={operar} />

      <Clasificacion
        receta={receta}
        recetaId={recetaId}
        categorias={categorias}
        etiquetas={etiquetas}
        operar={operar}
      />

      <Notas receta={receta} recetaId={recetaId} operar={operar} />

      <button
        type="button"
        className="boton-secundario w-full"
        onClick={() => navegar(`/recetas/${recetaId}`)}
      >
        Terminar de editar
      </button>
    </div>
  );
}

type Operar = (accion: () => Promise<unknown>, mensaje?: string) => Promise<void>;

function DatosGenerales({
  receta,
  fuentes,
  operar,
}: {
  receta: Receta;
  fuentes: ElementoCatalogo[];
  operar: Operar;
}) {
  const [nombre, setNombre] = useState(receta.nombre);
  const [descripcion, setDescripcion] = useState(receta.descripcion);
  const [rendimiento, setRendimiento] = useState(receta.rendimiento_base);
  const [unidad, setUnidad] = useState(receta.rendimiento_descripcion);
  const [fuenteId, setFuenteId] = useState(receta.fuente_id);

  return (
    <section className="tarjeta space-y-4 p-4">
      <h2 className="font-semibold tracking-tight">Datos generales</h2>

      <div>
        <label htmlFor="nombre" className="etiqueta-campo">
          Nombre
        </label>
        <input
          id="nombre"
          className="campo"
          value={nombre}
          onChange={(e) => setNombre(e.target.value)}
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
              step="0.001"
              className="campo w-24"
              value={rendimiento}
              onChange={(e) => setRendimiento(e.target.value)}
            />
            <input
              className="campo flex-1"
              value={unidad}
              onChange={(e) => setUnidad(e.target.value)}
              aria-label="Unidad del rendimiento"
            />
          </div>
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

      <button
        type="button"
        className="boton-primario"
        onClick={() =>
          operar(
            () =>
              pedir(`/recetas/${receta.id}/`, {
                metodo: "PATCH",
                cuerpo: {
                  nombre,
                  descripcion,
                  rendimiento_base: rendimiento,
                  rendimiento_descripcion: unidad,
                  fuente_id: fuenteId,
                },
              }),
            "Datos generales guardados",
          )
        }
      >
        Guardar datos generales
      </button>
    </section>
  );
}

function BloqueEdicion({
  recetaId,
  preparacion,
  indice,
  total,
  ingredientes,
  puedeEliminar,
  tiposDisponibles,
  operar,
  recargar,
  onMover,
}: {
  recetaId: string;
  preparacion: Preparacion;
  indice: number;
  total: number;
  ingredientes: ElementoCatalogo[];
  puedeEliminar: boolean;
  tiposDisponibles: TipoFotografia[];
  operar: Operar;
  recargar: () => Promise<void>;
  onMover: (destino: number) => void;
}) {
  const [nombre, setNombre] = useState(preparacion.nombre);
  const [nuevoPaso, setNuevoPaso] = useState("");
  const base = `/recetas/${recetaId}/preparaciones/${preparacion.id}`;

  return (
    <section className="tarjeta space-y-4 p-4">
      <div className="flex items-center gap-2">
        <Reordenar
          posicion={indice}
          total={total}
          onMover={onMover}
          etiqueta={`la preparación ${preparacion.nombre}`}
        />
        <input
          className="campo flex-1 font-semibold"
          value={nombre}
          onChange={(e) => setNombre(e.target.value)}
          onBlur={() => {
            if (nombre.trim() && nombre !== preparacion.nombre) {
              void operar(
                () => pedir(`${base}/`, { metodo: "PATCH", cuerpo: { nombre } }),
                "Preparación renombrada",
              );
            }
          }}
          aria-label="Nombre de la preparación"
        />
        {puedeEliminar && (
          <button
            type="button"
            className="boton-secundario text-error"
            onClick={() =>
              operar(
                () => pedir(`${base}/`, { metodo: "DELETE" }),
                "Preparación eliminada",
              )
            }
          >
            Eliminar
          </button>
        )}
      </div>

      <div className="space-y-2">
        <h3 className="text-sm font-semibold text-tinta-suave">Ingredientes</h3>
        {preparacion.ingredientes.map((ingrediente) => (
          <RenglonIngrediente
            key={ingrediente.ingrediente_preparacion_id}
            base={base}
            ingrediente={ingrediente}
            operar={operar}
          />
        ))}

        <AgregarIngrediente
          base={base}
          ingredientes={ingredientes}
          operar={operar}
        />
      </div>

      <div className="space-y-2">
        <h3 className="text-sm font-semibold text-tinta-suave">Pasos</h3>
        {preparacion.pasos.map((paso, indicePaso) => (
          <div key={paso.id} className="flex items-center gap-2">
            <span className="grid h-11 w-7 shrink-0 place-items-center text-sm font-semibold text-tinta-tenue">
              {paso.orden}
            </span>
            <Reordenar
              posicion={indicePaso}
              total={preparacion.pasos.length}
              etiqueta={`el paso ${paso.orden}`}
              onMover={(destino) =>
                operar(
                  () =>
                    pedir(`${base}/pasos/reordenar/`, {
                      metodo: "POST",
                      cuerpo: {
                        ids_en_orden: moverElemento(
                          preparacion.pasos.map((p) => p.id),
                          indicePaso,
                          destino,
                        ),
                      },
                    }),
                  "Pasos reordenados",
                )
              }
            />
            <input
              className="campo flex-1"
              defaultValue={paso.descripcion}
              onBlur={(e) => {
                if (e.target.value.trim() && e.target.value !== paso.descripcion) {
                  void operar(
                    () =>
                      pedir(`${base}/pasos/${paso.id}/`, {
                        metodo: "PATCH",
                        cuerpo: { descripcion: e.target.value },
                      }),
                    "Paso actualizado",
                  );
                }
              }}
              aria-label={`Paso ${paso.orden}`}
            />
            <button
              type="button"
              className="px-1 text-sm font-medium text-error"
              aria-label={`Eliminar paso ${paso.orden}`}
              onClick={() =>
                operar(
                  () => pedir(`${base}/pasos/${paso.id}/`, { metodo: "DELETE" }),
                  "Paso eliminado",
                )
              }
            >
              ✕
            </button>
          </div>
        ))}

        <div className="flex gap-2">
          <input
            className="campo flex-1"
            value={nuevoPaso}
            onChange={(e) => setNuevoPaso(e.target.value)}
            placeholder="Agregar un paso…"
            aria-label="Nuevo paso"
          />
          <button
            type="button"
            className="boton-secundario"
            disabled={!nuevoPaso.trim()}
            onClick={() =>
              operar(
                () =>
                  pedir(`${base}/pasos/`, {
                    metodo: "POST",
                    cuerpo: { descripcion: nuevoPaso },
                  }),
                "Paso agregado",
              ).then(() => setNuevoPaso(""))
            }
          >
            Agregar
          </button>
        </div>
      </div>

      <div className="space-y-2">
        <h3 className="text-sm font-semibold text-tinta-suave">Fotografías</h3>
        {preparacion.fotografias.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {preparacion.fotografias.map((foto) => (
              <figure key={foto.id} className="relative">
                <img
                  src={foto.ruta}
                  alt={foto.descripcion || foto.tipo}
                  className="h-24 w-24 rounded-pieza object-cover"
                />
                <button
                  type="button"
                  className="absolute -right-1.5 -top-1.5 grid h-6 w-6 place-items-center rounded-full bg-error text-xs font-bold text-white"
                  aria-label="Eliminar fotografía"
                  onClick={() =>
                    operar(
                      () =>
                        pedir(`${base}/fotografias/${foto.id}/`, {
                          metodo: "DELETE",
                        }),
                      "Fotografía eliminada",
                    )
                  }
                >
                  ✕
                </button>
              </figure>
            ))}
          </div>
        )}
        <SubirFotografia
          recetaId={recetaId}
          preparacionId={preparacion.id}
          tiposDisponibles={tiposDisponibles}
          onSubida={() => void recargar()}
        />
      </div>
    </section>
  );
}

/**
 * Ingrediente de una preparación, editable en el lugar (RF-017).
 *
 * Cambiar el tipo de escalado a "a gusto" o "cantidad necesaria" descarta
 * la cantidad, porque esos tipos se definen justamente por no tenerla. El
 * dominio lo rechazaría; acá directamente se ocultan los campos.
 */
function RenglonIngrediente({
  base,
  ingrediente,
  operar,
}: {
  base: string;
  ingrediente: Ingrediente;
  operar: Operar;
}) {
  const [editando, setEditando] = useState(false);
  const [tipo, setTipo] = useState<TipoEscalado>(ingrediente.tipo_escalado);
  const [cantidad, setCantidad] = useState(ingrediente.cantidad ?? "");
  const [unidad, setUnidad] = useState(ingrediente.unidad ?? "g");

  const llevaCantidad = tipo === "lineal" || tipo === "fijo";
  const ruta = `${base}/ingredientes/${ingrediente.ingrediente_preparacion_id}/`;

  if (!editando) {
    return (
      <div className="flex items-center gap-2 rounded-pieza border border-borde px-3 py-2">
        <span className="min-w-0 flex-1 truncate font-medium">
          {ingrediente.nombre}
        </span>
        <span className="tabular-nums text-azul-oscuro">
          {ingrediente.texto_cantidad}
        </span>
        <button
          type="button"
          className="px-1 text-sm font-medium text-azul"
          onClick={() => setEditando(true)}
        >
          Cambiar
        </button>
        <button
          type="button"
          className="px-1 text-sm font-medium text-error"
          aria-label={`Quitar ${ingrediente.nombre}`}
          onClick={() =>
            operar(() => pedir(ruta, { metodo: "DELETE" }), "Ingrediente quitado")
          }
        >
          ✕
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-2 rounded-pieza border border-azul bg-azul-claro/30 p-3">
      <p className="font-medium">{ingrediente.nombre}</p>

      <div className="flex flex-wrap gap-2">
        <select
          className="campo min-w-[10rem] flex-1"
          value={tipo}
          onChange={(e) => setTipo(e.target.value as TipoEscalado)}
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
              value={cantidad}
              onChange={(e) => setCantidad(e.target.value)}
              aria-label="Cantidad"
            />
            <select
              className="campo w-24"
              value={unidad}
              onChange={(e) => setUnidad(e.target.value)}
              aria-label="Unidad"
            >
              {UNIDADES.map((item) => (
                <option key={item.simbolo} value={item.simbolo}>
                  {item.simbolo}
                </option>
              ))}
            </select>
          </>
        )}
      </div>

      <p className="text-sm text-tinta-suave">{AYUDA_ESCALADO[tipo]}</p>

      <div className="flex gap-2">
        <button
          type="button"
          className="boton-primario flex-1"
          disabled={llevaCantidad && !cantidad}
          onClick={() =>
            operar(
              () =>
                pedir(ruta, {
                  metodo: "PATCH",
                  cuerpo: {
                    tipo_escalado: tipo,
                    cantidad: llevaCantidad ? cantidad : null,
                    unidad: llevaCantidad ? unidad : null,
                  },
                }),
              "Ingrediente actualizado",
            ).then(() => setEditando(false))
          }
        >
          Guardar
        </button>
        <button
          type="button"
          className="boton-secundario"
          onClick={() => setEditando(false)}
        >
          Cancelar
        </button>
      </div>
    </div>
  );
}

function AgregarIngrediente({
  base,
  ingredientes,
  operar,
}: {
  base: string;
  ingredientes: ElementoCatalogo[];
  operar: Operar;
}) {
  const [ingredienteId, setIngredienteId] = useState("");
  const [tipo, setTipo] = useState<TipoEscalado>("lineal");
  const [cantidad, setCantidad] = useState("");
  const [unidad, setUnidad] = useState("g");

  const llevaCantidad = tipo === "lineal" || tipo === "fijo";

  return (
    <div className="space-y-2 rounded-pieza border border-dashed border-borde p-3">
      <select
        className="campo"
        value={ingredienteId}
        onChange={(e) => setIngredienteId(e.target.value)}
        aria-label="Ingrediente a agregar"
      >
        <option value="">Agregar un ingrediente…</option>
        {ingredientes.map((item) => (
          <option key={item.id} value={item.id}>
            {item.nombre}
          </option>
        ))}
      </select>

      {ingredienteId && (
        <>
          <div className="flex flex-wrap gap-2">
            <select
              className="campo min-w-[10rem] flex-1"
              value={tipo}
              onChange={(e) => setTipo(e.target.value as TipoEscalado)}
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
                  value={cantidad}
                  onChange={(e) => setCantidad(e.target.value)}
                  placeholder="500"
                  aria-label="Cantidad"
                />
                <select
                  className="campo w-24"
                  value={unidad}
                  onChange={(e) => setUnidad(e.target.value)}
                  aria-label="Unidad"
                >
                  {UNIDADES.map((item) => (
                    <option key={item.simbolo} value={item.simbolo}>
                      {item.simbolo}
                    </option>
                  ))}
                </select>
              </>
            )}
          </div>

          <p className="text-sm text-tinta-tenue">{AYUDA_ESCALADO[tipo]}</p>

          <button
            type="button"
            className="boton-secundario w-full"
            disabled={llevaCantidad && !cantidad}
            onClick={() =>
              operar(
                () =>
                  pedir(`${base}/ingredientes/`, {
                    metodo: "POST",
                    cuerpo: {
                      ingrediente_id: ingredienteId,
                      tipo_escalado: tipo,
                      cantidad: llevaCantidad ? cantidad : null,
                      unidad: llevaCantidad ? unidad : null,
                    },
                  }),
                "Ingrediente agregado",
              ).then(() => {
                setIngredienteId("");
                setCantidad("");
              })
            }
          >
            Agregar ingrediente
          </button>
        </>
      )}
    </div>
  );
}

function AgregarPreparacion({
  recetaId,
  operar,
}: {
  recetaId: string;
  operar: Operar;
}) {
  const [nombre, setNombre] = useState("");

  return (
    <div className="flex gap-2">
      <input
        className="campo flex-1"
        value={nombre}
        onChange={(e) => setNombre(e.target.value)}
        placeholder="Nueva preparación: salsa, cobertura, armado…"
        aria-label="Nombre de la nueva preparación"
      />
      <button
        type="button"
        className="boton-secundario"
        disabled={!nombre.trim()}
        onClick={() =>
          operar(
            () =>
              pedir(`/recetas/${recetaId}/preparaciones/`, {
                metodo: "POST",
                cuerpo: { nombre, ingredientes: [], pasos: [] },
              }),
            "Preparación agregada",
          ).then(() => setNombre(""))
        }
      >
        Agregar
      </button>
    </div>
  );
}

/**
 * Categorías y etiquetas de la receta (RF-027 y RF-028).
 *
 * Se asignan y se quitan de a una contra la API, sin botón de guardar: un
 * chip que se apaga al tocarlo ya comunica que el cambio se aplicó.
 */
function Clasificacion({
  receta,
  recetaId,
  categorias,
  etiquetas,
  operar,
}: {
  receta: Receta;
  recetaId: string;
  categorias: ElementoCatalogo[];
  etiquetas: ElementoCatalogo[];
  operar: Operar;
}) {
  const grupos = [
    {
      titulo: "Categorías",
      ruta: "categorias",
      opciones: categorias,
      asignadas: receta.categorias_ids,
      vacio: "Todavía no hay categorías cargadas.",
    },
    {
      titulo: "Etiquetas",
      ruta: "etiquetas",
      opciones: etiquetas,
      asignadas: receta.etiquetas_ids,
      vacio: "Todavía no hay etiquetas cargadas.",
    },
  ];

  /** Muestra la jerarquía completa de una categoría. */
  function texto(ruta: string, elemento: ElementoCatalogo): string {
    if (ruta !== "categorias" || !elemento.categoria_padre_id) return elemento.nombre;
    const padre = categorias.find((c) => c.id === elemento.categoria_padre_id);
    return padre ? `${padre.nombre} › ${elemento.nombre}` : elemento.nombre;
  }

  return (
    <section className="tarjeta space-y-4 p-4">
      <h2 className="font-semibold tracking-tight">Clasificación</h2>

      {grupos.map((grupo) => (
        <div key={grupo.ruta}>
          <h3 className="mb-2 text-sm font-semibold text-tinta-suave">
            {grupo.titulo}
          </h3>

          {grupo.opciones.length === 0 ? (
            <p className="text-sm text-tinta-tenue">{grupo.vacio}</p>
          ) : (
            <div className="flex flex-wrap gap-2">
              {grupo.opciones.map((opcion) => {
                const asignada = grupo.asignadas.includes(opcion.id);
                return (
                  <button
                    key={opcion.id}
                    type="button"
                    aria-pressed={asignada}
                    className={`rounded-full px-3 py-1.5 text-sm font-medium transition-colors ${
                      asignada
                        ? "bg-azul text-white"
                        : "border border-borde bg-white text-tinta-suave hover:border-azul hover:text-azul"
                    }`}
                    onClick={() =>
                      operar(
                        () =>
                          pedir(`/recetas/${recetaId}/${grupo.ruta}/${opcion.id}/`, {
                            metodo: asignada ? "DELETE" : "POST",
                          }),
                        asignada ? "Quitada de la receta" : "Asignada a la receta",
                      )
                    }
                  >
                    {texto(grupo.ruta, opcion)}
                  </button>
                );
              })}
            </div>
          )}
        </div>
      ))}
    </section>
  );
}

function Notas({
  receta,
  recetaId,
  operar,
}: {
  receta: Receta;
  recetaId: string;
  operar: Operar;
}) {
  const [texto, setTexto] = useState("");

  return (
    <section className="tarjeta space-y-3 p-4">
      <h2 className="font-semibold tracking-tight">Notas</h2>

      {receta.notas.map((nota) => (
        <div key={nota.id} className="flex items-center gap-2">
          <input
            className="campo flex-1"
            defaultValue={nota.texto}
            aria-label="Nota"
            onBlur={(e) => {
              if (e.target.value.trim() && e.target.value !== nota.texto) {
                void operar(
                  () =>
                    pedir(`/recetas/${recetaId}/notas/${nota.id}/`, {
                      metodo: "PATCH",
                      cuerpo: { texto: e.target.value },
                    }),
                  "Nota actualizada",
                );
              }
            }}
          />
          <button
            type="button"
            className="px-1 text-sm font-medium text-error"
            aria-label="Eliminar nota"
            onClick={() =>
              operar(
                () =>
                  pedir(`/recetas/${recetaId}/notas/${nota.id}/`, {
                    metodo: "DELETE",
                  }),
                "Nota eliminada",
              )
            }
          >
            ✕
          </button>
        </div>
      ))}

      <div className="flex gap-2">
        <input
          className="campo flex-1"
          value={texto}
          onChange={(e) => setTexto(e.target.value)}
          placeholder="Anotá algo para la próxima vez…"
          aria-label="Nueva nota"
        />
        <button
          type="button"
          className="boton-secundario"
          disabled={!texto.trim()}
          onClick={() =>
            operar(
              () =>
                pedir(`/recetas/${recetaId}/notas/`, {
                  metodo: "POST",
                  cuerpo: { texto },
                }),
              "Nota agregada",
            ).then(() => setTexto(""))
          }
        >
          Agregar
        </button>
      </div>
    </section>
  );
}
