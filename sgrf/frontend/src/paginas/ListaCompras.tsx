/**
 * Lista de compras.
 *
 * Se usa en el supermercado, con una mano: los renglones son grandes y se
 * marcan tocando cualquier parte de la fila. Lo comprado baja al final en
 * lugar de desaparecer, para poder desmarcarlo si hizo falta.
 *
 * El marcado vive en la pantalla: el análisis no pide conservar qué se
 * compró entre sesiones (decisión D-17).
 */

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { ErrorApi, pedir } from "../api/cliente";
import type { ItemCompra, ListaCompra } from "../api/tipos";
import { Aviso, Cargando, Vacio } from "../componentes/Comunes";
import { useAutenticacion } from "../contexto/Autenticacion";

function Renglon({
  item,
  comprado,
  alternar,
}: {
  item: ItemCompra;
  comprado: boolean;
  alternar: () => void;
}) {
  return (
    <li>
      <label
        className={`flex cursor-pointer items-center gap-3 px-4 py-4 transition-colors hover:bg-azul-claro/40 ${
          comprado ? "opacity-55" : ""
        }`}
      >
        <input
          type="checkbox"
          className="h-5 w-5 shrink-0 rounded border-borde text-exito focus:ring-exito"
          checked={comprado}
          onChange={alternar}
        />
        <span
          className={`flex-1 font-medium ${comprado ? "line-through" : ""}`}
        >
          {item.nombre}
        </span>
        <span className="text-cantidad tabular-nums text-azul-oscuro">
          {item.texto_cantidad}
        </span>
      </label>
    </li>
  );
}

export default function ListaCompras() {
  const { perfil } = useAutenticacion();
  const [listas, setListas] = useState<ListaCompra[]>([]);
  const [comprados, setComprados] = useState<Set<string>>(new Set());
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!perfil) return;
    pedir<ListaCompra[]>("/listas-compra/")
      .then(setListas)
      .catch((fallo) =>
        setError(
          fallo instanceof ErrorApi
            ? fallo.message
            : "No se pudieron cargar las listas.",
        ),
      )
      .finally(() => setCargando(false));
  }, [perfil]);

  function alternar(id: string) {
    setComprados((previos) => {
      const copia = new Set(previos);
      copia.has(id) ? copia.delete(id) : copia.add(id);
      return copia;
    });
  }

  if (cargando) return <Cargando texto="Cargando tus listas…" />;

  const items = listas.flatMap((lista) => lista.items);
  const pendientes = items.filter((item) => !comprados.has(item.id));
  const listos = items.filter((item) => comprados.has(item.id));

  return (
    <div className="space-y-5">
      <h1 className="text-2xl font-semibold tracking-tight">Lista de compras</h1>

      {error && <Aviso>{error}</Aviso>}

      {items.length === 0 ? (
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
              : `Te faltan ${pendientes.length} de ${items.length}.`}
          </p>

          <section className="tarjeta overflow-hidden">
            <ul className="divide-y divide-borde">
              {pendientes.map((item) => (
                <Renglon
                  key={item.id}
                  item={item}
                  comprado={false}
                  alternar={() => alternar(item.id)}
                />
              ))}
              {listos.map((item) => (
                <Renglon
                  key={item.id}
                  item={item}
                  comprado
                  alternar={() => alternar(item.id)}
                />
              ))}
            </ul>
          </section>
        </>
      )}
    </div>
  );
}
