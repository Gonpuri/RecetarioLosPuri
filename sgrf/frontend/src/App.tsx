/**
 * Estructura general de la aplicación y sus rutas.
 *
 * La navegación sigue el Capítulo 6.5. En pantallas chicas la barra baja
 * al pie, donde el pulgar la alcanza: el Capítulo 6.10 pide priorizar el
 * uso en el teléfono, que es donde se cocina.
 */

import type { ReactNode } from "react";
import { NavLink, Navigate, Route, Routes, useLocation } from "react-router-dom";

import { Cargando } from "./componentes/Comunes";
import { useAutenticacion } from "./contexto/Autenticacion";
import Administracion from "./paginas/Administracion";
import DetalleReceta from "./paginas/DetalleReceta";
import EditarReceta from "./paginas/EditarReceta";
import ImprimirReceta from "./paginas/ImprimirReceta";
import Ingresar from "./paginas/Ingresar";
import ListaCompras from "./paginas/ListaCompras";
import NuevaReceta from "./paginas/NuevaReceta";
import Recetas from "./paginas/Recetas";

const SECCIONES = [
  { ruta: "/recetas", texto: "Recetas" },
  { ruta: "/favoritas", texto: "Favoritas" },
  { ruta: "/lista-compras", texto: "Lista de compras" },
];

function Navegacion() {
  const { perfil, esAdministrador, salir } = useAutenticacion();
  if (!perfil) return null;

  const secciones = esAdministrador
    ? [...SECCIONES, { ruta: "/administracion", texto: "Administrar" }]
    : SECCIONES;

  const clases = ({ isActive }: { isActive: boolean }) =>
    `rounded-pieza px-3 py-2 text-sm font-medium transition-colors ${
      isActive ? "bg-azul-claro text-azul-oscuro" : "text-tinta-suave hover:text-azul"
    }`;

  return (
    <header className="sticky top-0 z-20 border-b border-borde bg-white/95 backdrop-blur print:hidden">
      <div className="mx-auto flex max-w-4xl items-center gap-4 px-4 py-3">
        <NavLink to="/recetas" className="mr-auto flex items-center gap-2">
          <span className="grid h-9 w-9 place-items-center rounded-pieza bg-azul text-white">
            <svg viewBox="0 0 24 24" className="h-5 w-5" aria-hidden="true">
              <path
                d="M8 3v7a3 3 0 006 0V3M11 3v7M8 3h6M11 10v11"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.8"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </span>
          <span className="font-titulo text-lg font-semibold tracking-tight text-tinta">
            Recetario
          </span>
        </NavLink>

        <nav className="hidden items-center gap-1 sm:flex">
          {secciones.map((seccion) => (
            <NavLink key={seccion.ruta} to={seccion.ruta} className={clases}>
              {seccion.texto}
            </NavLink>
          ))}
        </nav>

        <button
          type="button"
          onClick={salir}
          className="text-sm font-medium text-tinta-suave hover:text-error"
        >
          Salir
        </button>
      </div>

      {/* Navegación al pie en teléfonos, al alcance del pulgar. */}
      <nav className="flex border-t border-borde sm:hidden">
        {SECCIONES.map((seccion) => (
          <NavLink
            key={seccion.ruta}
            to={seccion.ruta}
            className={({ isActive }) =>
              `flex-1 py-2.5 text-center text-sm font-medium ${
                isActive ? "text-azul" : "text-tinta-suave"
              }`
            }
          >
            {seccion.texto}
          </NavLink>
        ))}
      </nav>
    </header>
  );
}

/** Exige sesión iniciada y recuerda a dónde quería ir la persona. */
function Protegida({ children }: { children: ReactNode }) {
  const { perfil, cargando } = useAutenticacion();
  const ubicacion = useLocation();

  if (cargando) return <Cargando texto="Abriendo el recetario…" />;
  if (!perfil) return <Navigate to="/ingresar" state={{ desde: ubicacion }} replace />;
  return <>{children}</>;
}

export default function App() {
  return (
    <div className="min-h-screen">
      <Navegacion />
      <main className="mx-auto max-w-4xl px-4 py-6">
        <Routes>
          <Route path="/ingresar" element={<Ingresar />} />
          <Route
            path="/recetas"
            element={
              <Protegida>
                <Recetas />
              </Protegida>
            }
          />
          <Route
            path="/favoritas"
            element={
              <Protegida>
                <Recetas soloFavoritas />
              </Protegida>
            }
          />
          <Route
            path="/recetas/nueva"
            element={
              <Protegida>
                <NuevaReceta />
              </Protegida>
            }
          />
          <Route
            path="/recetas/:recetaId"
            element={
              <Protegida>
                <DetalleReceta />
              </Protegida>
            }
          />
          <Route
            path="/recetas/:recetaId/editar"
            element={
              <Protegida>
                <EditarReceta />
              </Protegida>
            }
          />
          <Route
            path="/recetas/:recetaId/imprimir"
            element={
              <Protegida>
                <ImprimirReceta />
              </Protegida>
            }
          />
          <Route
            path="/administracion"
            element={
              <Protegida>
                <Administracion />
              </Protegida>
            }
          />
          <Route
            path="/lista-compras"
            element={
              <Protegida>
                <ListaCompras />
              </Protegida>
            }
          />
          <Route path="*" element={<Navigate to="/recetas" replace />} />
        </Routes>
      </main>
    </div>
  );
}
