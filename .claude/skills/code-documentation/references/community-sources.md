# Procedencia y referencias consultadas

Consulta: 7 de septiembre de 2026. Esta skill es una implementación original
para el flujo solicitado. No se ha copiado ni incluido el código o texto completo
de las skills siguientes. No existen dependencias remotas en ejecución.

| Referencia | Señal observada | Práctica aplicada |
| --- | --- | --- |
| `anthropics/skills`, `doc-coauthoring` | Repositorio oficial de Anthropic | Aclarar contexto, estructurar y comprobar utilidad para un lector nuevo |
| `obra/superpowers`, `verification-before-completion` | Proyecto comunitario Superpowers | Exigir resultados observados antes de declarar una validación |
| Documentación de Claude Code | Fuente oficial de compatibilidad | Carpeta SKILL.md, recursos auxiliares y carga por tarea |
| Docusaurus | Documentación oficial del proyecto | Versionado, enlaces de docs y soporte Mermaid |
| Diátaxis | Marco publicado por sus autores | Separar aprendizaje, tareas, referencia y explicación |

La popularidad de un repositorio no equivale a votos sobre una skill
individual, una auditoría de seguridad ni una garantía. Se omiten cifras
volátiles de estrellas en esta versión; esta skill no está avalada por los
autores citados ni hereda sus señales de comunidad.

## Fuentes primarias

```text
https://github.com/anthropics/skills
https://github.com/anthropics/skills/blob/main/skills/doc-coauthoring/SKILL.md
https://github.com/obra/superpowers
https://github.com/obra/superpowers/blob/main/skills/verification-before-completion/SKILL.md
https://code.claude.com/docs/en/skills
https://docusaurus.io/docs/versioning
https://docusaurus.io/docs/markdown-features/links
https://docusaurus.io/docs/markdown-features/diagrams
https://diataxis.fr/
```

## Adaptación intencional

La documentación de código exige investigar el repositorio antes de pedir al
usuario datos recuperables. Por ello no se traslada literalmente el flujo de
entrevista de doc-coauthoring. Se retiene la revisión de lector y se añaden
revisiones Git, un mapa de impacto y protección histórica específicos.

No es necesario instalar Superpowers o las skills de Anthropic para usar
este paquete. Antes de añadir cualquier tercero, revisar sus instrucciones,
licencia vigente, permisos y versión; no ejecutar instaladores de catálogos
sin esa revisión. Al no redistribuir archivos de terceros, este paquete no
incluye ni pretende sustituir sus licencias.

## Ampliación 1.1.0: experiencia documental

Se consultó además `anthropics/skills:frontend-design` para su proceso de
planificación, implementación y revisión ajustado al encargo. No se copió su
contenido ni se ejecutó esa skill. Su exploración general de marca se sustituye
aquí por reutilización estricta del design system Captia ya existente.

La selección de Ionic, Refine y React Native está detallada en
`showcase-patterns.md`. Consultas adicionales: documentación oficial de estilos,
MDX, búsqueda y componentes de Docusaurus; comparaciones visuales de Playwright;
y referencia WCAG 2.2. Estas fuentes no avalan este paquete. No se añaden
cifras de popularidad ni dependencias nuevas en esta actualización.

## Adaptación a `codabench-docs`, 2026-09-10

Este paquete es una copia adaptada del que vive en `my-qa-captia-ai-app`, el
manual de captia.ai. La procedencia de arriba no cambia: no se consultaron
fuentes de terceros nuevas al adaptarlo, ni se instaló nada.

Lo que sí cambia es la fuente que documenta el repositorio. Aquí el producto
documentado es **Codabench**, una plataforma externa, y sus páginas oficiales
—`https://docs.codabench.org/`— no son una referencia de estilo consultada al
escribir esta skill, sino la evidencia que respalda el contenido del sitio. Se
citan en cada página y en `docs-map.json`, no aquí. Codabench es un proyecto
independiente y su documentación no avala ni esta skill ni esta guía.
