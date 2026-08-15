# SGRF-EIS-001
Capítulo 5 – Arquitectura

**Versión: **1.0
**Objetivo: **Definir la arquitectura lógica propuesta para la implementación del Sistema de Gestión de Recetas Familiares, independiente de la tecnología.

## 5.1 Principios Arquitectónicos

La arquitectura deberá:
• Ser independiente del framework y del motor de base de datos.
• Separar claramente el dominio del resto de las capas.
• Implementar las reglas de negocio exclusivamente en el dominio.
• Facilitar pruebas unitarias e integración.
• Permitir la evolución sin modificar el modelo del negocio.

## 5.2 Arquitectura por Capas

Presentación
↓
Aplicación
↓
Dominio
↓
Infraestructura
↓
Persistencia

Cada capa solo podrá depender de la inmediatamente inferior mediante interfaces definidas.

## 5.3 Capa de Presentación

Responsable de:
- Navegación.
- Pantallas.
- Formularios.
- Componentes visuales.
No contendrá reglas de negocio.

## 5.4 Capa de Aplicación

Coordina los casos de uso.
Responsabilidades:
- Orquestar operaciones.
- Validar permisos.
- Gestionar transacciones.
- Invocar servicios del dominio.

## 5.5 Capa de Dominio

Núcleo del sistema.
Contendrá:
- Entidades.
- Objetos de Valor.
- Servicios del Dominio.
- Interfaces de Repositorios.
La entidad Receta actuará como Aggregate Root.

## 5.6 Infraestructura

Implementa los detalles técnicos:
- Repositorios.
- Acceso a archivos.
- Persistencia de fotografías.
- Servicios externos futuros.

## 5.7 Persistencia

El modelo físico deberá respetar el modelo lógico definido en el análisis.
Las restricciones de integridad deberán implementarse en la base de datos y validarse también en el dominio.

## 5.8 Servicios del Dominio

EscaladorRecetas:
Calcula ingredientes para un nuevo rendimiento.

GeneradorListaCompras:
Consolida ingredientes seleccionados.

BuscadorRecetas:
Resuelve búsquedas.

ValidadorRecetas:
Verifica reglas de negocio.

## 5.9 Flujo General

Usuario
→ Interfaz
→ Caso de Uso
→ Dominio
→ Repositorio
→ Base de Datos

La respuesta seguirá el camino inverso hasta la interfaz.

## 5.10 Reglas Arquitectónicas

- Nunca acceder a la base de datos desde la interfaz.
- Nunca colocar reglas de negocio en la capa de presentación.
- Nunca modificar la receta base durante el escalado.
- Utilizar el Lenguaje Ubicuo en todo el código.

## 5.11 Escalabilidad

La arquitectura deberá permitir incorporar en versiones futuras:
- OCR.
- IA.
- Temporizadores.
- Importación desde sitios web.
Sin alterar el modelo de dominio existente.

## 5.12 Conclusión

La arquitectura propuesta prioriza la separación de responsabilidades, la mantenibilidad y la evolución del sistema, permitiendo implementar el proyecto con cualquier stack tecnológico sin modificar las reglas del negocio.