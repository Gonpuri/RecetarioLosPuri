/**
 * Tipos que reflejan los DTO de la capa de Aplicación.
 *
 * Conservan el Lenguaje Ubicuo del proyecto. Las cantidades viajan como
 * texto para no perder precisión al convertirlas a número de coma
 * flotante: la aritmética la hace el backend con Decimal.
 */

export type TipoEscalado = "lineal" | "fijo" | "a_gusto" | "cantidad_necesaria";
export type TipoFotografia = "proceso" | "final";
export type Rol = "administrador" | "usuario_familiar";

export interface Ingrediente {
  ingrediente_preparacion_id: string;
  ingrediente_id: string;
  nombre: string;
  texto_cantidad: string;
  tipo_escalado: TipoEscalado;
  cantidad: string | null;
  unidad: string | null;
  observacion: string;
}

export interface Paso {
  id: string;
  orden: number;
  descripcion: string;
}

export interface Fotografia {
  id: string;
  ruta: string;
  tipo: TipoFotografia;
  descripcion: string;
}

export interface Preparacion {
  id: string;
  nombre: string;
  orden: number;
  ingredientes: Ingrediente[];
  pasos: Paso[];
  fotografias: Fotografia[];
}

export interface Nota {
  id: string;
  texto: string;
  fecha: string;
  autor_id: string | null;
}

export interface Receta {
  id: string;
  nombre: string;
  descripcion: string;
  rendimiento_base: string;
  rendimiento_descripcion: string;
  fuente_id: string;
  fuente_nombre: string;
  archivada: boolean;
  favorita: boolean;
  preparaciones: Preparacion[];
  categorias_ids: string[];
  etiquetas_ids: string[];
  notas: Nota[];
}

export interface RecetaResumen {
  id: string;
  nombre: string;
  rendimiento_base: string;
  rendimiento_descripcion: string;
  archivada: boolean;
  favorita: boolean;
  categorias_ids: string[];
  fotografia_final: string | null;
}

/** Resultado del escalado. Es temporal: el backend nunca lo guarda. */
/** Ingrediente tal como lo extrajo la importación, con su posible coincidencia. */
export interface IngredienteImportado {
  texto: string;
  ingrediente_id: string | null;
  cantidad: string | null;
  unidad: string | null;
  tipo_escalado: TipoEscalado;
  observacion: string;
}

export interface PreparacionImportada {
  nombre: string;
  ingredientes: IngredienteImportado[];
  pasos: string[];
}

/**
 * Borrador de receta extraído de un PDF o una foto (Cap. 7.7, versión 2.0).
 *
 * Nunca es la receta guardada: es lo que la importación entendió, para
 * revisar y corregir antes de guardarlo con el alta normal.
 */
export interface RecetaImportada {
  nombre: string;
  descripcion: string;
  rendimiento_base: string;
  rendimiento_descripcion: string;
  fuente_sugerida: string;
  preparaciones: PreparacionImportada[];
  advertencia: string | null;
}

export interface RecetaEscalada {
  receta_id: string;
  nombre: string;
  rendimiento_base: string;
  rendimiento_solicitado: string;
  rendimiento_descripcion: string;
  factor: string;
  preparaciones: Preparacion[];
}

export interface ItemCompra {
  id: string;
  ingrediente_id: string;
  nombre: string;
  texto_cantidad: string;
  comprado: boolean;
}

export interface ListaCompra {
  id: string;
  items: ItemCompra[];
  fecha: string;
  usuario_id: string | null;
}

export interface Perfil {
  id: string;
  nombre: string;
  correo: string;
  rol: Rol;
  activo: boolean;
}

export interface UsuarioResumen {
  id: string;
  nombre: string;
  correo: string;
  rol: Rol;
  activo: boolean;
}

export interface ElementoCatalogo {
  id: string;
  nombre: string;
  descripcion?: string;
  categoria_padre_id?: string | null;
  detalle?: string;
}

/** Etiquetas legibles de los tipos de escalado, para los formularios. */
export const ETIQUETAS_ESCALADO: Record<TipoEscalado, string> = {
  lineal: "Se multiplica",
  fijo: "No cambia",
  a_gusto: "A gusto",
  cantidad_necesaria: "Cantidad necesaria",
};

/** Explicación de cada tipo, mostrada como ayuda al cargar ingredientes. */
export const AYUDA_ESCALADO: Record<TipoEscalado, string> = {
  lineal: "La cantidad acompaña al rendimiento. El caso más común.",
  fijo: "La cantidad no varía aunque cambie el rendimiento.",
  a_gusto: "Sin cantidad: lo ajusta quien cocina.",
  cantidad_necesaria: "Sin cantidad: se usa la que la preparación pida.",
};

export const UNIDADES = [
  { simbolo: "g", nombre: "gramos" },
  { simbolo: "kg", nombre: "kilogramos" },
  { simbolo: "ml", nombre: "mililitros" },
  { simbolo: "l", nombre: "litros" },
  { simbolo: "cda", nombre: "cucharadas" },
  { simbolo: "cdita", nombre: "cucharaditas" },
  { simbolo: "taza", nombre: "tazas" },
  { simbolo: "pizca", nombre: "pizcas" },
  { simbolo: "u", nombre: "unidades" },
];
