# SGRF-EIS-001
Capítulo 3 – Dominio

**Versión: **1.0
**Estado: **Borrador de trabajo

## 3.1 Introducción

El dominio representa el núcleo del sistema. Toda la lógica del negocio gira alrededor de la entidad Receta, que actúa como raíz del agregado y coordina las Preparaciones, Ingredientes, Pasos, Fotografías, Notas y demás elementos del modelo.

## 3.2 Lenguaje Ubicuo

Los términos oficiales del dominio son:
- Receta
- Preparación
- Ingrediente
- IngredientePreparación
- Paso
- Fotografía
- Nota
- Categoría
- Etiqueta
- Fuente
- Rendimiento Base
- Lista de Compras

## 3.3 Entidades Principales

Receta: representa una elaboración culinaria completa.
Preparación: subreceta o etapa independiente.
Ingrediente: elemento reutilizable del catálogo.
IngredientePreparación: relación entre un ingrediente y una preparación.
Paso: instrucción ordenada.
Fotografía: imagen asociada a una preparación.
Nota: observación permanente.
Categoría: clasificación jerárquica.
Etiqueta: clasificación transversal.
Fuente: origen de la receta.

## 3.4 Receta

Responsabilidades:
- Mantener información general.
- Administrar Preparaciones.
- Administrar Categorías.
- Administrar Etiquetas.
- Administrar Fotografías.
- Administrar Notas.
- Mantener el Rendimiento Base.
- Mantener una única Fuente.

## 3.5 Preparación

Representa una etapa de la receta (por ejemplo Masa, Salsa, Cobertura o Armado). Cada preparación posee ingredientes, pasos y fotografías propias y mantiene un orden dentro de la receta.

## 3.6 Ingredientes

Los ingredientes pertenecen a un catálogo único reutilizable. Las cantidades no se almacenan en el ingrediente sino en la relación IngredientePreparación.

## 3.7 Objetos de Valor

Cantidad, Unidad, Rendimiento y TipoEscalado son objetos de valor utilizados para representar conceptos del dominio sin identidad propia.

## 3.8 Servicios del Dominio

EscaladorRecetas: calcula cantidades para un nuevo rendimiento.
GeneradorListaCompras: consolida ingredientes seleccionados.
BuscadorRecetas: resuelve búsquedas por distintos criterios.
ValidadorRecetas: garantiza el cumplimiento de las reglas de negocio.

## 3.9 Relaciones

Receta 1..N Preparaciones
Preparación 1..N IngredientePreparación
Ingrediente 1..N IngredientePreparación
Preparación 1..N Pasos
Preparación 1..N Fotografías
Receta N..N Categorías
Receta N..N Etiquetas
Fuente 1..N Recetas

## 3.10 Reglas del Dominio

- Toda receta posee un Rendimiento Base.
- Toda receta posee exactamente una Fuente.
- Toda receta tiene una o más Preparaciones.
- La receta base nunca se modifica.
- El escalado genera una representación temporal.
- Máximo tres fotografías por receta (dos de proceso y una final).

## 3.11 Conclusión

El modelo del dominio prioriza la preservación de la receta original y la reutilización de componentes mediante Preparaciones, permitiendo un diseño desacoplado de la tecnología y preparado para futuras ampliaciones.