// @ts-check
/**
 * Configuración del sitio de la guía de Codabench.
 *
 * El tema, la tipografía y los tokens son los MISMOS que los del manual de captia.ai
 * (`my-qa-captia-ai-app`): el Captia Technology Design System es la única autoridad visual de
 * la organización y no se bifurca por sitio. Lo que cambia aquí es el contenido, el dominio y
 * la navegación.
 *
 * Decisiones que no son obvias y que conviene no deshacer sin leer `docs-meta/`:
 *
 * - `markdown.format: 'detect'` — con el modo MDX por defecto de Docusaurus 3, cualquier `{`
 *   suelto en el texto se interpreta como una expresión JSX y rompe el build. Esta guía habla de
 *   ficheros `metadata`, plantillas de comando (`$program/scoring.py $input $output`) y claves de
 *   `scores.txt`, y ese tipo de contenido acaba trayendo llaves tarde o temprano. Con 'detect',
 *   los `.md` se procesan como CommonMark y solo los `.mdx` —hoy únicamente la portada— son MDX.
 *
 * - `i18n` con un solo locale y sin `--locale` en el build — construir un único locale NO añade
 *   prefijo de URL, así que el español vive en la raíz. Añadir `en` más adelante lo colocará bajo
 *   `/en/` sin romper ningún enlace entrante. Si algún día se pasa `--locale en` al build, el
 *   sitio inglés se publicaría en la raíz y machacaría el español.
 *
 * - `versions.current.label: 'Codabench v1.31.2'` sin `versioned_docs` — la versión viva se etiqueta
 *   con la versión de Codabench contra la que se contrastó el contenido, igual que el manual de
 *   captia.ai se etiqueta con la versión de la aplicación. Todavía no se congela ninguna: el
 *   primer corte tendrá sentido cuando Codabench publique una versión que cambie la UI descrita.
 *   De dónde sale esa etiqueta y qué la mantiene honesta, en `docs-meta/03-version-contrastada.md`.
 */

// `showLastUpdateTime` saca la fecha de `git log`, no del sistema de ficheros, y cuando el
// comando falla NO degrada: tumba el build entero con «Can't process doc metadata». Pasa siempre
// que se construye sin historial —un `vercel deploy` desde la CLI sube los ficheros sin `.git`, y
// un `git archive` o un ZIP descargado tampoco lo llevan—, y el mensaje de error no menciona ni
// la fecha ni esta opción: habla de metadatos de un documento, así que se busca el fallo en el
// documento.
//
// El despliegue normal —Vercel conectado al repositorio— sí clona y tiene `.git`, de modo que la
// fecha se sigue mostrando ahí, que es donde importa. Para que sea la fecha REAL de cada página y
// no la del último despliegue, el clon no puede ser superficial: hay que declarar
// `VERCEL_DEEP_CLONE=true` en las variables de entorno del proyecto (ver README).
const fs = require('fs');
const path = require('path');
const hayHistorialGit = fs.existsSync(path.join(__dirname, '.git'));

const config = {
  title: 'Guía de Codabench',
  tagline: 'Crear y mantener competiciones en Codabench',
  // Marca real del Captia Technology Design System (static/img/logo-mark.svg), con su geometría
  // exacta: cuadrado #00FF79 con los arcos y el anillo en #0000DC.
  favicon: 'img/logo-mark.svg',

  // Vercel es el ÚNICO destino de publicación, en la RAÍZ del dominio `docs.codabench.captia.ai`.
  //
  // `baseUrl` es lo primero que hay que revisar si algún día se sirve desde otro sitio: un sitio
  // construido con prefijo de ruta (como el que impone GitHub Pages, /codabench-docs/) y servido
  // en una raíz —o al revés— responde 200 pero con TODO el CSS, el JS y las imágenes en 404. Se
  // ve como HTML sin estilos.
  //
  // La URL se toma de la variable que inyecta Vercel, que vale el DOMINIO DE PRODUCCIÓN del
  // proyecto: en cuanto `docs.codabench.captia.ai` queda asignado ahí, el canonical, el Open Graph
  // y el sitemap se corrigen solos, sin tocar este fichero. El literal es solo el respaldo para
  // builds locales y para el primer despliegue, antes de que el dominio exista.
  url: `https://${process.env.VERCEL_PROJECT_PRODUCTION_URL || 'docs.codabench.captia.ai'}`,
  baseUrl: '/',
  organizationName: 'captia-technology',
  projectName: 'codabench-docs',
  trailingSlash: false,

  // Un enlace o un ancla rotos tumban el build. Es la red de seguridad del contenido.
  onBrokenLinks: 'throw',
  onBrokenAnchors: 'throw',

  markdown: {
    format: 'detect',
    // Los diagramas se escriben en bloques ```mermaid dentro del propio .md. Se eligió frente a
    // SVG a mano por una razón que se nota al mantenerlos: un diagrama en texto se revisa en el
    // diff, se corrige en una línea y hereda los colores del tema en los dos modos. Un SVG
    // incrustado hay que volver a dibujarlo y, si trae colores propios, se rompe en modo oscuro.
    mermaid: true,
    hooks: { onBrokenMarkdownLinks: 'throw' },
  },

  i18n: {
    defaultLocale: 'es',
    locales: ['es'],
    localeConfigs: {
      es: { label: 'Español', htmlLang: 'es-ES', direction: 'ltr' },
    },
  },

  // Tipografía del Captia Technology Design System: Geist para texto y JetBrains Mono para
  // datos. El propio sistema advierte de que no vendoriza las binarias y usa las familias
  // equivalentes de Google Fonts, que es de donde se cargan aquí.
  headTags: [
    {
      tagName: 'link',
      attributes: { rel: 'preconnect', href: 'https://fonts.googleapis.com' },
    },
    {
      tagName: 'link',
      attributes: { rel: 'preconnect', href: 'https://fonts.gstatic.com', crossorigin: 'anonymous' },
    },
  ],
  stylesheets: [
    'https://fonts.googleapis.com/css2?family=Geist:wght@300..900&family=JetBrains+Mono:wght@400;500;700&display=swap',
  ],

  presets: [
    [
      'classic',
      {
        docs: {
          path: 'docs',
          routeBasePath: '/',
          sidebarPath: './sidebars.js',
          showLastUpdateTime: hayHistorialGit,
          lastVersion: 'current',
          versions: {
            current: { label: 'Codabench v1.31.2', path: '' },
          },
        },
        blog: false,
        // Dos ficheros, y el orden importa: `custom.css` declara los tokens y es copia exacta
        // del tema del manual de captia.ai —no se toca—; `diagramas.css` los consume para
        // vestir los diagramas, que son de este sitio. Ver `.claude/rules/design-system.md`.
        theme: { customCss: ['./src/css/custom.css', './src/css/diagramas.css'] },
      },
    ],
  ],

  themes: [
    '@docusaurus/theme-mermaid',
    [
      require.resolve('@easyops-cn/docusaurus-search-local'),
      {
        hashed: true,
        language: ['es'],
        indexBlog: false,
        docsRouteBasePath: '/',
        highlightSearchTermsOnTargetPage: true,
        searchResultLimits: 10,
        // El extracto por defecto son 50 caracteres, y en una guía donde media docena de páginas
        // empiezan describiendo la misma pantalla del editor web, ese fragmento se agota antes de
        // llegar a la palabra buscada: todos los resultados se leen igual. Con 120 se ve POR QUÉ
        // ha salido cada uno.
        searchResultContextMaxLength: 120,
        // Y la ruta, porque los términos de Codabench se repiten entre secciones —«Task» aparece
        // en Recursos y en Fases, «submission» en media guía—: sin la ruta, dos resultados
        // distintos se leen igual.
        explicitSearchResultPath: true,
      },
    ],
  ],

  themeConfig: {
    colorMode: { defaultMode: 'light', respectPrefersColorScheme: true },
    // Mermaid trae sus propios colores y ninguno es de la marca. Se le pasan los temas que
    // reconoce —`base` admite variables— con los tokens del Captia Technology Design System: azul
    // de marca sobre claro, verde de acento sobre oscuro, que es la misma regla que sigue el
    // resto del sitio y por el mismo motivo medido (el azul sobre el fondo oscuro da 1.87).
    mermaid: {
      theme: { light: 'base', dark: 'base' },
      options: {
        fontFamily: 'Geist, system-ui, sans-serif',
        themeVariables: {
          primaryColor: '#f5f5f5',
          primaryTextColor: '#0a0a0a',
          primaryBorderColor: '#0000dc',
          lineColor: '#6b6b6b',
          secondaryColor: '#ffffff',
          tertiaryColor: '#ffffff',
          fontSize: '14px',
        },
      },
    },
    // Sin tarjeta social todavía: generarla exige rasterizar el mark real y disponer de la
    // binaria de Geist, que el propio design system declara no vendorizada. Antes que
    // publicar una aproximación del logo, no se declara ninguna.
    navbar: {
      title: 'Codabench',
      logo: { alt: 'Captia', src: 'img/logo-mark.svg', width: 26, height: 26 },
      items: [
        { to: '/mapa-de-la-guia', label: 'Mapa de la guía', position: 'left' },
        { type: 'docsVersionDropdown', position: 'right' },
        {
          href: 'https://github.com/captia-technology/codabench-docs',
          label: 'GitHub',
          position: 'right',
        },
        // Un enlace normal y no `to`: `/salir` no es una página de Docusaurus, lo atiende
        // `middleware.js`, y el router del cliente lo resolvería sin pedirlo al servidor.
        {
          type: 'html',
          position: 'right',
          value: '<a class="navbar__link" href="/salir">Salir</a>',
        },
      ],
    },
    footer: {
      style: 'dark',
      links: [
        {
          title: 'La guía',
          items: [
            { label: 'Portada', to: '/' },
            { label: 'Mapa de la guía', to: '/mapa-de-la-guia' },
            { label: 'Conceptos clave', to: '/empezar/conceptos' },
            { label: 'Troubleshooting', to: '/referencia/troubleshooting' },
          ],
        },
        {
          title: 'El recorrido',
          items: [
            { label: 'Crear la competición', to: '/competicion' },
            { label: 'Recursos y tasks', to: '/recursos' },
            { label: 'Fases y evaluación', to: '/evaluacion' },
            { label: 'Submissions', to: '/submissions' },
          ],
        },
        {
          title: 'Fuera de aquí',
          items: [
            { label: 'Codabench', href: 'https://www.codabench.org/' },
            { label: 'Documentación oficial', href: 'https://docs.codabench.org/' },
            { label: 'Fuentes de esta guía', to: '/referencia/fuentes' },
          ],
        },
      ],
      copyright: `© ${new Date().getFullYear()} CAPTIA Technology. Guía contrastada con Codabench v1.31.2.`,
    },
    prism: {
      theme: require('prism-react-renderer').themes.github,
      darkTheme: require('prism-react-renderer').themes.dracula,
    },
    tableOfContents: { minHeadingLevel: 2, maxHeadingLevel: 4 },
  },
};

module.exports = config;
