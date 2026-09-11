# Contratos de componentes documentales

Estos nombres describen responsabilidades, NO exports existentes en Captia ni
componentes que traiga este paquete. Buscar equivalentes antes de implementarlos.
Elegir solo los necesarios. No generar imports de componentes imaginarios.

| Rol | Contenido y comportamiento | Criterio de aceptación |
| --- | --- | --- |
| Cabecera de artículo | Título, resumen y metadatos pertinentes | Un H1, sin badges decorativos; versión derivada de datos reales |
| Tarjeta de entrada | Título, descripción, icono opcional y enlace | Un destino real; foco visible; sin controles interactivos anidados |
| Secuencia de pasos | Instrucción, ejemplo, resultado y comprobación | Lista ordenada semántica; no usar numeración para categorías paralelas |
| Aviso | Nivel semántico, título y condición relevante | Icono/texto además de color; warning cuando el riesgo sea real |
| Variantes | Alternativas equivalentes de plataforma, lenguaje o entorno | Tabs accesibles; conservar requisitos comunes fuera de ellas |
| Código | Lenguaje, ejemplo seguro, copia, título opcional | Copiar solo el comando/código, no prompts ni salida; scroll contenido |
| Figura de producto | Imagen real, alt, pie y contexto de versión | Imagen legible, sin secretos, sin controles inventados ni zoom inaccesible |
| Tabla de referencia | Tipos, valores, requisitos y restricciones contrastados | Encabezados correctos, lectura móvil y valores desconocidos explícitos |
| Diagrama | Relaciones verificadas y explicación textual | Render revisado; legible en temas soportados y móvil |
| Siguiente paso | Continuación de la tarea y enlaces relacionados | No enlace a sí mismo ni CTA genérico; preservar versión cuando aplique |
| Aviso de versión | Actual, histórica o no verificada según datos | No insinuar soporte/EOL sin política real; enlace a versión vigente comprobado |

Dos filas de esa tabla no tienen hoy ningún caso en este repositorio: no hay
capturas de pantalla y no hay soporte de Mermaid instalado. No son una invitación
a crearlos para completar la lista; si alguna vez hacen falta, el criterio de
aceptación ya está escrito. El «aviso de versión» sí aplica, pero con una sola
versión viva: no insinuar soporte, EOL ni una política de versiones que no existe.

## Selección técnica

Reutilizar primero componentes Captia compatibles; después primitivas del tema
Docusaurus adaptadas con tokens. No instalar otro kit de UI para maquetar docs.
En una configuración compatible, Docusaurus ofrece Tabs, TabItem, CodeBlock y
avisos; inspeccionar la versión y el tema antes de utilizarlos. Los roles de la
tabla no implican que exista `@theme/Steps`, `@theme/Cards` o algo similar.

Usar MDX para composición interactiva justificada, Markdown para contenido simple
y CSS compartido para consistencia. Un documento puede ser visualmente excelente
sin JSX. No forzar MDX por apariencia ni abusar de componentes a costa de lectura.

Para componentes nuevos: especificar props, semántica HTML, tokens reales,
comportamiento responsive, teclado, SSR e impacto sobre versiones anteriores.
No acceder a `window` en evaluación de módulo; adaptar con las herramientas del
proyecto. Usar enlaces de Docusaurus apropiados para `baseUrl`, idiomas y rutas.

## Compatibilidad histórica

Los imports de docs antiguas pueden resolver al componente actual. Mantener sus
props y comportamiento o un adaptador compatible. No renombrar/eliminar activos
compartidos sin comprobar referencias históricas. Tras modificar un componente,
probar una página de cada familia que lo usa y una versión anterior pertinente.

## Fuentes de implementación

```text
https://docusaurus.io/docs/markdown-features/react
https://docusaurus.io/docs/markdown-features/tabs
https://docusaurus.io/docs/markdown-features/code-blocks
https://docusaurus.io/docs/markdown-features/admonitions
https://docusaurus.io/docs/styling-layout
```
