# SGRF-EIS-001
Capítulo 4 – Requisitos Funcionales

**Versión: **1.0
**Estado: **Borrador de trabajo
**Objetivo: **Definir el comportamiento funcional esperado del Sistema de Gestión de Recetas Familiares.

## 4.1 Introducción

Los requisitos funcionales describen las capacidades que deberá ofrecer el sistema a los usuarios. Cada requisito representa una funcionalidad verificable y constituye la base para los casos de uso, las pruebas funcionales y la implementación.

## 4.2 Gestión de Usuarios

**RF-001: **Registrar usuarios familiares.

**RF-002: **Modificar datos de un usuario.

**RF-003: **Desactivar usuarios sin eliminar su historial.

**RF-004: **Administrar permisos de acceso.

## 4.3 Gestión de Recetas

**RF-005: **Crear una receta indicando nombre, descripción, rendimiento base y fuente.

**RF-006: **Editar la información general de una receta.

**RF-007: **Consultar una receta completa.

**RF-008: **Archivar una receta.

**RF-009: **Restaurar una receta archivada.

**RF-010: **Duplicar una receta para crear una variante.

## 4.4 Gestión de Preparaciones

**RF-011: **Agregar una o más Preparaciones a una receta.

**RF-012: **Modificar una Preparación.

**RF-013: **Eliminar una Preparación respetando las reglas de negocio.

**RF-014: **Reordenar las Preparaciones.

## 4.5 Gestión de Ingredientes

**RF-015: **Administrar un catálogo reutilizable de ingredientes.

**RF-016: **Agregar ingredientes a una Preparación.

**RF-017: **Modificar cantidad, unidad y observaciones.

**RF-018: **Eliminar ingredientes de una Preparación.

## 4.6 Gestión de Pasos

**RF-019: **Agregar pasos ordenados.

**RF-020: **Modificar pasos.

**RF-021: **Eliminar pasos.

**RF-022: **Reordenar pasos.

## 4.7 Fotografías y Notas

**RF-023: **Agregar fotografías respetando el límite de tres por receta.

**RF-024: **Eliminar fotografías.

**RF-025: **Registrar notas y observaciones permanentes.

**RF-026: **Editar o eliminar notas.

## 4.8 Organización

**RF-027: **Asignar múltiples categorías.

**RF-028: **Asignar etiquetas.

**RF-029: **Administrar categorías y subcategorías.

**RF-030: **Administrar fuentes.

## 4.9 Escalado

**RF-031: **Calcular cantidades para un nuevo rendimiento.

**RF-032: **Mostrar la receta escalada sin modificar la receta base.

**RF-033: **Respetar el tipo de escalado de cada ingrediente (Lineal, Fijo, A gusto, Cantidad necesaria).

## 4.10 Lista de Compras

**RF-034: **Permitir marcar ingredientes faltantes.

**RF-035: **Generar una lista de compras consolidada.

**RF-036: **Visualizar la lista en dispositivos móviles.

**RF-037: **Permitir compartir o imprimir la lista en futuras versiones.

## 4.11 Búsquedas

**RF-038: **Buscar por nombre.

**RF-039: **Buscar por ingrediente.

**RF-040: **Buscar por categoría.

**RF-041: **Buscar por etiqueta.

**RF-042: **Buscar por fuente.

**RF-043: **Filtrar favoritas y archivadas.

## 4.12 Criterios de Aceptación

- Todas las operaciones deberán validar las reglas de negocio.
- El escalado nunca modificará la receta almacenada.
- No podrán registrarse recetas sin rendimiento base ni fuente.
- Las búsquedas deberán devolver únicamente recetas activas, salvo solicitud explícita.

## 4.13 Trazabilidad

| RF | Regla de Negocio | Caso de Uso |
| --- | --- | --- |
| RF-005 | RN-001, RN-002 | CU-001 |
| RF-011 | RN-003 | CU-003 |
| RF-031 | RN-006, RN-007 | CU-011 |
| RF-035 | RN-021, RN-022 | CU-012 |

## 4.14 Conclusión

Los requisitos funcionales definidos constituyen la especificación mínima de comportamiento del sistema. Todo desarrollo deberá demostrar el cumplimiento de estos requisitos mediante casos de uso y pruebas funcionales.