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
 * - `versions.current.label: 'Codabench v1.23'` sin `versioned_docs` — la versión viva se etiqueta
 *   con la versión de Codabench contra la que se contrastó el contenido, igual que el manual de
 *   captia.ai se etiqueta con la versión de la aplicación. Todavía no se congela ninguna: el
 *   primer corte tendrá sentido cuando Codabench publique una versión que cambie la UI descrita.
 *   De dónde sale esa etiqueta y qué la mantiene honesta, en `docs-meta/03-version-contrastada.md`.
 */

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
          showLastUpdateTime: true,
          lastVersion: 'current',
          versions: {
            current: { label: 'Codabench v1.23', path: '' },
          },
        },
        blog: false,
        theme: { customCss: './src/css/custom.css' },
      },
    ],
  ],

  themes: [
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
      copyright: `© ${new Date().getFullYear()} CAPTIA Technology. Guía contrastada con Codabench v1.23.`,
    },
    prism: {
      theme: require('prism-react-renderer').themes.github,
      darkTheme: require('prism-react-renderer').themes.dracula,
    },
    tableOfContents: { minHeadingLevel: 2, maxHeadingLevel: 4 },
  },
};

module.exports = config;
