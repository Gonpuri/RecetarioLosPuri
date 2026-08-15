# SGRF-EIS-001
Capítulo 1 – Introducción

**Versión: **1.0
**Estado: **Borrador de trabajo

## 1.1 Propósito

El presente documento constituye la introducción de la Especificación de Ingeniería de Software (EIS) del Sistema de Gestión de Recetas Familiares (SGRF). Su objetivo es describir el problema que resuelve el sistema, el contexto de uso, los objetivos generales y específicos, el alcance de la primera versión y los principios rectores que guiarán el desarrollo.

## 1.2 Contexto

Actualmente las recetas familiares se encuentran distribuidas en cuadernos, hojas sueltas, recortes, sitios web y conocimiento transmitido verbalmente. Esta dispersión dificulta la organización, búsqueda y conservación del patrimonio gastronómico familiar.

## 1.3 Problema

Se identifican problemas de duplicación de recetas, dificultad para encontrar información, imposibilidad de escalar correctamente las cantidades, ausencia de organización uniforme y pérdida de conocimiento con el paso del tiempo.

## 1.4 Objetivo General

Desarrollar un sistema para uso familiar que permita registrar, organizar, consultar y mantener recetas mediante un modelo basado en Preparaciones, preservando siempre la receta base y calculando dinámicamente las cantidades para distintos rendimientos.

## 1.5 Objetivos Específicos

• Registrar recetas.
• Organizar mediante categorías y subcategorías.
• Clasificar mediante etiquetas.
• Registrar una única fuente por receta.
• Dividir recetas en Preparaciones.
• Gestionar ingredientes, pasos, fotografías y notas.
• Escalar recetas desde un rendimiento base.
• Generar listas de compras.
• Compartir el recetario entre los miembros de la familia.
• Archivar recetas sin eliminarlas.

## 1.6 Alcance

La versión 1.0 incluye gestión de usuarios, recetas, preparaciones, ingredientes, pasos, fotografías (máximo tres por receta), notas, categorías, etiquetas, fuentes, escalado y lista de compras. Se excluyen funciones comerciales, stock, costos, OCR, IA, videos y delivery.

## 1.7 Usuarios

Administrador: administra usuarios y catálogos.
Usuario Familiar: crea, consulta, modifica y archiva recetas; genera listas de compras.

## 1.8 Principios

1. La receta base nunca se modifica.
2. Toda receta posee una o más Preparaciones.
3. La Preparación es la unidad funcional del dominio.
4. La aplicación prioriza la experiencia de cocinar.
5. El análisis es independiente de la tecnología.

## 1.9 Criterios de Calidad

El sistema deberá priorizar consistencia funcional, mantenibilidad, trazabilidad, escalabilidad, simplicidad de uso e integridad de los datos.

## 1.10 Conclusión

Este capítulo establece el contexto y la visión general del proyecto, sirviendo como base para los capítulos posteriores dedicados al dominio, requisitos, arquitectura y experiencia de usuario.