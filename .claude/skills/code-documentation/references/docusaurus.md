# Autoría Docusaurus

## Descubrir la configuración real

Inspeccionar `package.json`, lockfile, `docusaurus.config.*`, `sidebars.*` y
plugins. No ejecutar/importar la configuración para leerla. Detectar la versión
instalada y conservar el gestor de paquetes. No actualizar Docusaurus por defecto.

Lo que hoy declara este repositorio, y que conviene releer antes de dar nada por
supuesto:

| Qué | Valor en `codabench-docs` | Por qué importa |
| --- | --- | --- |
| Docusaurus | 3.10.2, preset clásico, Node 22 | El comportamiento de MDX y de los enlaces cambia entre mayores |
| `routeBasePath` | `/` | Los docs se sirven en la raíz: `docs/index.mdx` **es** la portada, no hay `/docs/` |
| `markdown.format` | `'detect'` | Los `.md` se procesan como CommonMark; solo los `.mdx` son MDX |
| `onBrokenLinks` / `onBrokenAnchors` | `'throw'` | Un enlace o un ancla rotos **tumban el build**, no avisan |
| `onBrokenMarkdownLinks` | `'throw'` | Lo mismo para los enlaces relativos entre `.md` |
| Versiones | solo `current`, etiquetada `Codabench v1.23` | No hay `versioned_docs/` ni `versions.json` |
| Buscador | `@easyops-cn/docusaurus-search-local` | Índice local, generado en el build; no hay Algolia |
| Temas de color | claro por defecto, `respectPrefersColorScheme` | Los dos modos existen y los dos hay que revisarlos |

En una instalación convencional `docs/` contiene el contenido actual y
`versioned_docs/`, `versioned_sidebars/` y `versions.json` guardan los
snapshots. Aquí solo existe el primero. No asumir `docs/current`.
Referencia: `https://docusaurus.io/docs/versioning`.

## Escribir y enlazar

Conservar IDs, slugs, frontmatter y sidebar existentes. Preferir enlaces
relativos al archivo `.md` de destino —un enlace Markdown cuyo destino sea
`../submissions/formato.md`, no una ruta de URL—: así resuelven en el editor, en
GitHub y en el sitio publicado, y con `onBrokenMarkdownLinks`
en `'throw'` un destino equivocado se detecta en el build en vez de publicarse.
No convertir rutas privadas en enlaces públicos.
Referencia: `https://docusaurus.io/docs/markdown-features/links`.

`sidebar_position`, `sidebar_label` y `description` los escribe
`scripts/build_nav.py --apply` a partir de la declaración `SECCIONES`. Editarlos
a mano es trabajo que se pierde en la siguiente ejecución. El `title` y el H1 sí
se escriben a mano, y tienen que decir lo mismo.

No incorporar frontmatter personalizado de trazabilidad sin comprobar su
compatibilidad; esos datos van al mapa (`docs-map.json`), que también genera
`build_nav.py`. Usar MDX solo si hace falta: con `format: 'detect'`, un `.md`
puede contener `{` sueltas —una plantilla de comando, una clave de `scores.txt`—
sin romper nada, mientras que en un `.mdx` esa misma llave se interpreta como
JSX y tumba el build. Hoy el único `.mdx` es la portada. Respetar las
convenciones de H1 y categorías del sitio.

## Diagramas y capturas

Este sitio **no** tiene `@docusaurus/theme-mermaid` instalado ni `mermaid: true`
en `markdown`. Un bloque con lenguaje `mermaid` se renderiza como código, no
como diagrama. Añadir el soporte es instalar un paquete y tocar la
configuración: proponerlo, no hacerlo por cuenta propia. Si se acepta, dibujar
solo nodos y relaciones contrastados y renderizar el diagrama antes de afirmar
que renderiza.
Referencia: `https://docusaurus.io/docs/markdown-features/diagrams`.

Hoy la guía no tiene capturas de pantalla: es contenido procedimental con los
rótulos de la interfaz en negrita. Si se añaden, usar Playwright o el navegador
disponible en un entorno autorizado, preparar datos ficticios, añadir texto
alternativo y retirar cualquier dato personal o nombre de instancia. No afirmar
que se ha probado una pantalla a partir de una imagen generada.

## Comprobaciones finales

El script de build es `npm run build`, que ejecuta `docusaurus build` sin más.
**Sin `--locale`**: con un solo locale el sitio se publica en la raíz, y pasar
`--locale en` publicaría el sitio inglés encima del español. Inspeccionar lo que
invoca antes de ejecutarlo y hacerlo en la raíz del sitio, si los permisos lo
permiten.

Con `onBrokenLinks` y `onBrokenAnchors` en `'throw'`, el build es una prueba
real de que los enlaces internos y las anclas resuelven; no lo es de que el
contenido sea correcto. No bajar la severidad para hacer pasar la validación:
eso convierte la red de seguridad en decoración.

Antes del build corren los validadores de Python, que comprueban lo que
Docusaurus no mira: `scripts/check_docs.py` (invariantes del contenido) y
`scripts/build_nav.py --check` (navegación declarada, mapa y `docs-map.json`).
Docusaurus construye igual de bien una página con un correo real dentro.

La skill no trae un parser MDX ni un verificador completo de enlaces. Su helper
valida la estructura del mapa y la existencia de páginas —y en este repositorio
ni siquiera eso, porque el mapa usa URLs; ver `data-formats.md`—.

## Capa visual profesional obligatoria

Aplicar `professional-experience.md` a toda página modificada y el contrato de
diseño si se toca el tema. El tema aquí es copia exacta del manual de captia.ai:
revisar layout, navegación y estilos desde lo que ya hay. Preferir adaptadores
CSS y composición pública; evitar ejectar componentes del tema sin evaluar
mantenimiento y compatibilidad. No instalar un tema premium ni otro kit visual.

Validar rutas teniendo en cuenta `baseUrl` y `routeBasePath`. Aquí los docs
viven en la raíz, así que **no hay una página `src/pages/index.js` compitiendo
por `/`**: la portada es `docs/index.mdx`. Añadir una página suelta en `/`
provocaría un conflicto de rutas. Conservar la operación de tabs, copia de
código, enlaces y buscador en SSR e hidratación.

El buscador ya está integrado y es local: `@easyops-cn/docusaurus-search-local`
construye el índice durante el build y lo sirve como parte del sitio estático.
Dos consecuencias. La primera, que se puede comprobar de verdad —consulta,
resultado, extracto, teclado, estado sin resultados— y hay que hacerlo antes de
darlo por bueno. La segunda, y más importante: **todo lo que entra en `docs/`
entra en el índice y se descarga en el navegador de cualquier visitante**.
Esconder una página del sidebar no la protege. Si algo no puede ser público, no
puede estar en `docs/`.
Referencias: `https://docusaurus.io/docs/styling-layout` y
`https://docusaurus.io/docs/search`.

Cuando existan versiones históricas compartirán tema y componentes con la
actual. Probar esa compatibilidad tras cambios globales: el versionado de
Markdown por sí solo no congela CSS, React ni todas las imágenes.
