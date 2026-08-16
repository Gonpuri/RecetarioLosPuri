/**
 * Lista de compras.
 *
 * Se usa en el supermercado, con una mano: los renglones son grandes y se
 * marcan tocando cualquier parte de la fila. Lo comprado baja al final en
 * lugar de desaparecer, para poder desmarcarlo si hizo falta.
 *
 * A diferencia del marcado de faltantes al generar la lista (que vive solo
 * en memoria hasta que se persiste), marcar un producto como comprado o
 * sacarlo de la lista se guarda siempre: perderlo al recargar la pantalla
 * en medio de la compra no tendría sentido.
 */

import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { ErrorApi, pedir } from "../api/cliente";
import type { ItemCompra, ListaCompra } from "../api/tipos";
import { Aviso, Cargando, Vacio } from "../componentes/Comunes";

/** Un item con la lista a la que pertenece, para poder operar sobre él. */
interface ItemConLista {
  listaId: string;
  item: ItemCompra;
}

function Renglon({
  entrada,
  onAlternar,
  onEliminar,
}: {
  entrada: ItemConLista;
  onAlternar: () => void;
  onEliminar: () => void;
}) {
  const { item } = entrada;

  return (
    <li className="flex items-center gap-2 px-4 py-4">
      <label
        className={`flex flex-1 cursor-pointer items-center gap-3 transition-colors ${
          item.comprado ? "opacity-55" : ""
        }`}
      >
        <input
          type="checkbox"
          className="h-5 w-5 shrink-0 rounded border-borde text-exito focus:ring-exito"
          checked={item.comprado}
          onChange={onAlternar}
        />
        <span className={`flex-1 font-medium ${item.comprado ? "line-through" : ""}`}>
          {item.nombre}
        </span>
        <span className="text-cantidad tabular-nums text-azul-oscuro">
          {item.texto_cantidad}
        </span>
      </label>

      <button
        type="button"
        className="shrink-0 rounded-pieza p-2 text-tinta-tenue transition-colors hover:bg-error/10 hover:text-error"
        onClick={onEliminar}
        aria-label={`Sacar ${item.nombre} de la lista`}
        title="Sacar de la lista"
      >
        <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth={1.8}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M6 6l12 12M18 6L6 18" />
        </svg>
      </button>
    </li>
  );
}

export default function ListaCompras() {
  const [listas, setListas] = useState<ListaCompra[]>([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const cargar = useCallback(async () => {
    setCargando(true);
    setError(null);
    try {
      setListas(await pedir<ListaCompra[]>("/listas-compra/"));
    } catch (fallo) {
      setError(
        fallo instanceof ErrorApi
          ? fallo.message
          : "No se pudieron cargar las listas.",
      );
    } finally {
      setCargando(false);
    }
  }, []);

  useEffect(() => {
    void cargar();
  }, [cargar]);

  /** Actualiza un item en el estado local sin esperar a recargar todo. */
  function actualizarLocal(listaId: string, itemId: string, cambio: Partial<ItemCompra>) {
    setListas((previas) =>
      previas.map((lista) =>
        lista.id !== listaId
          ? lista
          : {
              ...lista,
              items: lista.items.map((item) =>
                item.id === itemId ? { ...item, ...cambio } : item,
              ),
            },
      ),
    );
  }

  async function alternarComprado(entrada: ItemConLista) {
    const nuevoEstado = !entrada.item.comprado;
    actualizarLocal(entrada.listaId, entrada.item.id, { comprado: nuevoEstado });
    try {
      await pedir(`/listas-compra/${entrada.listaId}/items/${entrada.item.id}/`, {
        metodo: "PATCH",
        cuerpo: { comprado: nuevoEstado },
      });
    } catch (fallo) {
      actualizarLocal(entrada.listaId, entrada.item.id, {
        comprado: entrada.item.comprado,
      });
      setError(
        fallo instanceof ErrorApi
          ? fallo.message
          : "No se pudo actualizar el producto.",
      );
    }
  }

  async function eliminarItem(entrada: ItemConLista) {
    const listasPrevias = listas;
    setListas((previas) =>
      previas.map((lista) =>
        lista.id !== entrada.listaId
          ? lista
          : { ...lista, items: lista.items.filter((i) => i.id !== entrada.item.id) },
      ),
    );
    try {
      await pedir(`/listas-compra/${entrada.listaId}/items/${entrada.item.id}/`, {
        metodo: "DELETE",
      });
    } catch (fallo) {
      setListas(listasPrevias);
      setError(
        fallo instanceof ErrorApi ? fallo.message : "No se pudo sacar el producto.",
      );
    }
  }

  if (cargando) return <Cargando texto="Cargando tus listas…" />;

  const entradas: ItemConLista[] = listas.flatMap((lista) =>
    lista.items.map((item) => ({ listaId: lista.id, item })),
  );
  const pendientes = entradas.filter((e) => !e.item.comprado);
  const listos = entradas.filter((e) => e.item.comprado);

  return (
    <div className="space-y-5">
      <h1 className="text-2xl font-semibold tracking-tight">Lista de compras</h1>

      {error && <Aviso>{error}</Aviso>}

      {entradas.length === 0 ? (
        <Vacio
          titulo="Todavía no armaste ninguna lista"
          descripcion="Abrí una receta, ajustá el rendimiento y marcá los ingredientes que te faltan."
          accion={
            <Link to="/recetas" className="boton-primario">
              Ir a las recetas
            </Link>
          }
        />
      ) : (
        <>
          <p className="text-sm text-tinta-suave">
            {pendientes.length === 0
              ? "Ya tenés todo."
              : `Te faltan ${pendientes.length} de ${entradas.length}.`}
          </p>

          <section className="tarjeta overflow-hidden">
            <ul className="divide-y divide-borde">
              {pendientes.map((entrada) => (
                <Renglon
                  key={entrada.item.id}
                  entrada={entrada}
                  onAlternar={() => alternarComprado(entrada)}
                  onEliminar={() => eliminarItem(entrada)}
                />
              ))}
              {listos.map((entrada) => (
                <Renglon
                  key={entrada.item.id}
                  entrada={entrada}
                  onAlternar={() => alternarComprado(entrada)}
                  onEliminar={() => eliminarItem(entrada)}
                />
              ))}
            </ul>
          </section>
        </>
      )}
    </div>
  );
}
