/**
 * Contexto de autenticación.
 *
 * Guarda el perfil del usuario en sesión y lo pone a disposición de toda
 * la aplicación. El token vive en el cliente de la API; acá solo importa
 * quién es la persona y qué puede hacer.
 */

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import { almacen, ingresar as ingresarApi, pedir } from "../api/cliente";
import type { Perfil } from "../api/tipos";

interface ValorAutenticacion {
  perfil: Perfil | null;
  cargando: boolean;
  esAdministrador: boolean;
  ingresar: (correo: string, clave: string) => Promise<void>;
  salir: () => void;
}

const Contexto = createContext<ValorAutenticacion | null>(null);

export function ProveedorAutenticacion({ children }: { children: ReactNode }) {
  const [perfil, setPerfil] = useState<Perfil | null>(null);
  const [cargando, setCargando] = useState(true);

  const cargarPerfil = useCallback(async () => {
    if (!almacen.acceso()) {
      setPerfil(null);
      setCargando(false);
      return;
    }
    try {
      setPerfil(await pedir<Perfil>("/perfil/"));
    } catch {
      almacen.limpiar();
      setPerfil(null);
    } finally {
      setCargando(false);
    }
  }, []);

  useEffect(() => {
    void cargarPerfil();
  }, [cargarPerfil]);

  const ingresar = useCallback(
    async (correo: string, clave: string) => {
      await ingresarApi(correo, clave);
      setPerfil(await pedir<Perfil>("/perfil/"));
    },
    [],
  );

  const salir = useCallback(() => {
    almacen.limpiar();
    setPerfil(null);
  }, []);

  const valor = useMemo(
    () => ({
      perfil,
      cargando,
      esAdministrador: perfil?.rol === "administrador",
      ingresar,
      salir,
    }),
    [perfil, cargando, ingresar, salir],
  );

  return <Contexto.Provider value={valor}>{children}</Contexto.Provider>;
}

export function useAutenticacion(): ValorAutenticacion {
  const valor = useContext(Contexto);
  if (!valor) {
    throw new Error(
      "useAutenticacion debe usarse dentro de ProveedorAutenticacion.",
    );
  }
  return valor;
}
