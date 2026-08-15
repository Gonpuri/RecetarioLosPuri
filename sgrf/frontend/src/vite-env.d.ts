/// <reference types="vite/client" />

/**
 * Variables de entorno del front.
 *
 * Vite las incrusta en el momento de compilar, no las lee en tiempo de
 * ejecución: si cambia el valor hay que volver a desplegar.
 */
interface ImportMetaEnv {
  /** URL base de la API, terminada en /api. */
  readonly VITE_API_URL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
