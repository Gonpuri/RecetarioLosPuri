# SGRF-EIS-001
Capítulo 7 – Anexos

**Versión: **1.0
**Objetivo: **Reunir la información de referencia que complementa la especificación funcional y sirve como guía para la implementación del Sistema de Gestión de Recetas Familiares.

## 7.1 Glosario

Receta: elaboración culinaria completa.
Preparación: subreceta o etapa.
Rendimiento Base: cantidad original registrada.
Escalado: cálculo temporal de cantidades.
Fuente: origen de la receta.
Lista de Compras: documento generado con ingredientes faltantes.

## 7.2 Reglas de Negocio Resumidas

RN-001 Toda receta posee un único Rendimiento Base.
RN-002 Toda receta posee una única Fuente.
RN-003 Toda receta posee una o más Preparaciones.
RN-004 La receta base nunca se modifica.
RN-005 Máximo tres fotografías por receta (2 de proceso y 1 final).
RN-006 La lista de compras se genera únicamente con ingredientes seleccionados por el usuario.

## 7.3 Modelo Entidad–Relación (Resumen)

Receta 1..N Preparación
Preparación 1..N IngredientePreparación
Ingrediente 1..N IngredientePreparación
Preparación 1..N Paso
Preparación 1..N Fotografía
Receta N..N Categoría
Receta N..N Etiqueta
Fuente 1..N Receta

## 7.4 Diccionario de Datos (Resumen)

Entidades principales:
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
- Usuario
- ListaCompra
- ItemCompra

## 7.5 Decisiones Arquitectónicas (ADR)

ADR-001 La Receta es el Aggregate Root.
ADR-002 La Preparación es la unidad funcional del dominio.
ADR-003 El escalado no persiste datos.
ADR-004 Los ingredientes pertenecen a un catálogo reutilizable.
ADR-005 La documentación es independiente de la tecnología.

## 7.6 Backlog

Must Have:
- Usuarios
- Recetas
- Preparaciones
- Escalado
- Lista de compras

Should Have:
- Favoritos
- Exportación

Could Have:
- OCR
- IA
- Videos

Won't Have (v1.0):
- Delivery
- Facturación
- Stock
- Costos

## 7.7 Roadmap

Versión 1.0: funcionalidades básicas.
Versión 1.1: mejoras de búsqueda y exportación.
Versión 2.0: OCR, IA, temporizadores e importación automática.

## 7.8 Restricciones para la Implementación

- No modificar la receta base.
- No persistir recetas escaladas.
- No agregar funcionalidades comerciales.
- No crear entidades fuera del dominio sin aprobación.
- Respetar el Lenguaje Ubicuo.

## 7.9 Definition of Done

Una funcionalidad se considera terminada cuando:
• Cumple las reglas de negocio.
• Posee pruebas.
• No rompe funcionalidades existentes.
• Respeta el modelo de dominio.
• Se encuentra documentada.

## 7.10 Referencias del Proyecto

Documentos relacionados:
- SGRF-EIS-001
- Capítulos 1 al 6
- Modelo lógico
- Casos de uso
- Wireframes
- Backlog del proyecto

## 7.11 Conclusión

Los anexos consolidan la información complementaria del proyecto y constituyen una guía rápida para el equipo de desarrollo, asegurando que las decisiones de diseño, las reglas de negocio y la planificación permanezcan alineadas durante toda la implementación.