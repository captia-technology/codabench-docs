# El montaje inicial — 2026-09-10

Registro de cómo se convirtió este repositorio, de una guía en un solo fichero Markdown, en un
sitio de documentación con tema propio, validadores, verificación en CI y publicación en Vercel.

Es una **instantánea fechada**: describe cómo quedó montado el 2026-09-10 y con qué argumento se
tomó cada decisión. No se reescribe cuando algo cambie después; lo que cambie se anota como nota
posterior, con su fecha, encima de lo que corrige.

## El punto de partida

Lo que había antes de tocar nada, medido y no estimado:

| Dato | Valor |
|---|---|
| Contenido | **1 fichero**: `docs/crear-competicion.md`, 236 líneas, 14 secciones más Referencias |
| Front matter | Ninguno |
| Imágenes | Ninguna |
| Ausentes | `package.json`, `docusaurus.config.js`, `sidebars.js`, `scripts/`, `.claude/`, `.github/workflows/`, `docs-meta/` |
| `README.md` | Tres párrafos: qué es el repositorio y dónde vive el pipeline de datasets |
| Rama | `master` (`origin/HEAD → origin/master`). No existe `develop` |
| Últimos commits | La guía se reenfocó al flujo por interfaz web y se enriqueció con observaciones de una competición real; el motor de generación de datasets se movió a un repositorio privado aparte |

La guía funcionaba como fichero suelto en GitHub, pero tenía tres límites que un solo fichero no
resuelve: no se puede enlazar a un paso concreto sin depender de un ancla numerada, no hay
búsqueda, y no hay forma de decir contra qué versión de Codabench está contrastado lo que dice.

## De dónde se replicó el patrón

De **`C:/CAPTIA/CAPTIA-TENANTS/my-qa-captia-ai-app`**, el manual de usuario de captia.ai: 148
páginas en español, Docusaurus 3.10.2, publicado en Vercel, con `docs-meta/`, validadores en Python
y un harness `.claude/` maduro en producción.

Se replica ese repositorio y no se monta un Docusaurus desde cero por una razón que no es la
comodidad: **ese patrón ya pagó los errores**. Las llaves que rompen el build de MDX, el
`--locale` que publica un idioma en la raíz, el enlace con la caja cambiada que pasa en Windows y
falla en Linux, el `vercel.json` con una clave inventada que tumba el despliegue tres días con el
CI en verde — todo eso está resuelto allí y comentado con el defecto que lo motivó. Volver a
descubrirlo aquí habría costado lo mismo, dos veces.

Lo que **no** se replica es el contenido ni la forma de las páginas: el manual de captia.ai
documenta pantallas con capturas numeradas y un despiece de elementos; esta guía es procedimental
y hoy no tiene ni una imagen.

## Qué se copió exacto

Verificado con `diff` contra la referencia el 2026-09-10:

| Fichero | Verificación |
|---|---|
| `src/css/custom.css` | **Idéntico fuera de comentarios y líneas en blanco.** Los tokens de marca, la escala tipográfica, los radios y los contrastes medidos no cambian ni un valor |
| `src/components/Portada/index.js` | Mismos componentes, mismas clases, mismos tokens. Una sola desviación de código: el rótulo del panel de cabecera, que allí era el literal «Manual funcional» en el JSX, aquí es la prop `rotulo` con ese mismo valor por defecto —el original renderiza idéntico—, y este sitio le pasa el suyo. De paso, el `versión ` que precedía a la etiqueta se va: aquí la etiqueta ya es «Codabench v1.31.2» |
| `src/components/Portada/styles.module.css` | Idéntico salvo el comentario de cabecera |
| `static/img/logo-mark.svg` | **Byte a byte idéntico.** Es el mark real del design system, con su geometría exacta |
| `.claude/skills/code-documentation/` | Copiada en estructura —los mismos 38 ficheros, con `references/captia-profile.md` renombrado a `references/perfil-repositorio.md`—, pero **reescrita en contenido**: solo 4 quedan idénticos byte a byte (`scripts/docs_tools.py`, los dos de `tests/` y `assets/captia-design-contract.example.json`). Todo lo demás se adaptó a documentar una fuente externa (ver abajo) |

El motivo de copiar y no adaptar: el **Captia Technology Design System** es la única autoridad
visual de la organización y no se bifurca por sitio. Dos sitios de la misma casa con dos azules
distintos es un fallo que se ve desde fuera y que nadie sabe dónde arreglar. Si un color o un radio
no cuadran, se arregla en el sistema, no aquí.

Eso incluye la desviación deliberada que la referencia ya documenta: en modo oscuro el texto
secundario del sistema (`#64748b`) da 4.05 sobre su propio fondo, por debajo del 4.5 que WCAG AA
pide para texto normal, y se sube a `#94a3b8` (7.52). Aquí se hereda tal cual, comentario incluido:
en esta guía el texto secundario son celdas de tabla y descripciones a tamaño normal, exactamente
el caso que motivó el cambio.

## Qué se adaptó, y por qué

**La skill `code-documentation`.** El original documenta una aplicación cuyo código está en un
repositorio hermano, y su unidad de evidencia es el commit. Aquí la fuente documentada es
**Codabench, una plataforma externa**: no hay commit que sirva de prueba. La skill se reescribe en
ese punto para exigir que cada afirmación diga de cuál de tres evidencias sale —documentación
oficial (con la URL y su versión), observación directa de la interfaz (instancia, fecha y ruta), o
una competición real ya montada— y que se diga cuál, porque ninguna sustituye a las otras.

Ese cambio no cabe en `SKILL.md`: arrastra a las referencias, a las plantillas y a los ejemplos, y
por eso solo cuatro ficheros de la skill sobreviven idénticos —el módulo `scripts/docs_tools.py`,
sus dos tests y el ejemplo del contrato de diseño, que no hablan de la fuente documentada—.
`references/captia-profile.md` pasa a llamarse `references/perfil-repositorio.md` por lo mismo: el
perfil que describe ya no es el de una aplicación de la casa.

**`docs-map.json`.** En la referencia mapea cada página a rutas del repositorio de la aplicación,
para responder «si el producto cambia, ¿qué páginas hay que revisar?». Aquí el producto es externo,
así que cada sección declara sus fuentes como **URLs** de la documentación oficial —y «observación
directa de la UI» donde corresponda—, con el mismo esquema (`schema_version: 1`, `_fuentes`,
`documents[].sources[].paths`) y el id de fuente `codabench`. La pregunta que responde es
idéntica; lo que cambia es qué se vigila.

**La plantilla de página.** La de la referencia gira alrededor de una captura numerada y su
despiece. La de aquí es front matter con `title`, un H1 que dice lo mismo, el rótulo `Objetivo:` en
la primera línea del cuerpo y secciones en H2, con pasos numerados para los procedimientos y tablas
para inventarios y errores. De ese `Objetivo:` sale la `description` del front matter, igual que
allí sale de «Objetivo Principal:».

**Los nombres de la interfaz no se traducen.** **Benchmarks → Management**, **Add Dataset/Program**,
**Force Best**: van en negrita y en su idioma original, porque son rótulos que el lector tiene
delante en pantalla mientras lee. Traducirlos obligaría a buscar dos veces.

**Las rutas se prohíben en no-ASCII de entrada.** La referencia arrastra 27 documentos con tilde en
la ruta —25 dentro de un único directorio, `Automatizaciones/Nodos/Configuración/`, y otros 2 con
la tilde en el propio nombre del fichero—, heredados, y los resuelve con un `slug` transliterado en
cada uno de los 27. Aquí el
árbol parte de cero: todo en minúscula ASCII, sin tildes, sin guiones bajos, y la invariante lo
bloquea. Mantener la excepción cuesta más que no tenerla.

**Lo que la referencia tiene y aquí no hace falta**: los scripts de migración de imágenes, de
saneado de capturas y de retirada de navegación de pie ya cumplieron su función allí y aquí no
tienen nada que migrar. El ciclo de release contra un repositorio hermano se sustituye por
`check_codabench.py`, que consulta la última release publicada de `codalab/codabench` en GitHub en
vez de leer el `package.json` y el CHANGELOG de un repositorio que está en el disco.

## Las decisiones que no son obvias

Cada una está comentada también en el fichero donde vive, para que no haya que venir aquí a
buscarla. Aquí está el porqué completo.

**1. `markdown.format: 'detect'`.** Docusaurus 3 procesa los `.md` como MDX por defecto, y MDX
interpreta cualquier `{` suelto como una expresión JSX: el build falla. Esta guía habla de ficheros
`metadata` con `command: python3 $program/scoring.py $input $output` y de claves de `scores.txt`;
ese tipo de contenido acaba trayendo llaves tarde o temprano. Con `'detect'`, los `.md` vuelven a
CommonMark y solo los `.mdx` —hoy únicamente la portada— son MDX.

**2. Un solo locale, y el build sin `--locale`.** Con un único idioma, construir uno concreto no
añade prefijo de URL: pasar `--locale` publicaría ese idioma en la raíz del sitio. Dejarlo fuera
mantiene el español en `/` y deja el hueco para que un futuro `en` viva bajo `/en/` sin romper
ningún enlace entrante.

**3. `routeBasePath: '/'`.** La documentación **es** el sitio: no hay blog ni landing que compartan
dominio, así que un prefijo `/docs/` solo alargaría todas las URL sin distinguir nada.

**4. `versions.current.label: 'Codabench v1.31.2'`, sin `versioned_docs`.** La versión viva se
etiqueta con la versión de Codabench contra la que se contrastó el contenido, igual que el manual
de captia.ai se etiqueta con la versión de la aplicación. No se congela ninguna versión todavía: el
primer corte tendrá sentido cuando Codabench publique una que cambie la interfaz descrita, y
congelar antes de tener nada que congelar duplica el árbol entero de `docs/` —25 ficheros— para
nada. De dónde sale exactamente
esa etiqueta, en [`03-version-contrastada.md`](03-version-contrastada.md).

**5. Búsqueda local (`@easyops-cn/docusaurus-search-local`) y no Algolia.** No hace falta dar de
alta un servicio externo ni esperar a un crawler para un sitio de 23 páginas. Dos ajustes no
vienen por defecto y se pusieron a mano: el extracto de resultado sube de 50 a **120** caracteres,
porque media docena de páginas empiezan describiendo la misma pantalla del editor web y con 50 el
fragmento se agota antes de llegar a la palabra buscada —todos los resultados se leen igual—; y
`explicitSearchResultPath`, porque los términos de Codabench se repiten entre secciones («Task»
aparece en Recursos y en Fases, «submission» en media guía) y sin la ruta dos resultados distintos
son indistinguibles.

**6. Sin tarjeta social.** Generarla exigiría rasterizar el mark real y disponer de la binaria de
Geist, que el propio design system declara no vendorizada. Antes que publicar una aproximación del
logo, no se declara ninguna.

**7. La navegación se declara en `SECCIONES`.** El orden del sidebar, la etiqueta de cada página,
los `_category_.json`, el mapa y `docs-map.json` salen todos de `scripts/build_nav.py`, y el script
falla si aparece un documento sin declarar. Alfabéticamente, `collaborators` iría antes que
`details` dentro de Competición, que es justo al revés del orden en que se rellena el formulario.

**8. El hook es `PostToolUse`, no `PreToolUse`.** El contenido solo se puede comprobar cuando ya
está escrito. En `PostToolUse` el código de salida 2 no bloquea nada —el fichero ya está— pero sí
hace llegar el stderr a Claude, que es la única vía para que un hook le diga algo al modelo.
Valida **solo el fichero tocado** y solo con comprobaciones locales: la comprobación completa, que
resuelve cada enlace contra el árbol entero, corre en CI.

**9. Los scripts que salen a la red no corren en CI.** `check_fuentes.py` depende de
`docs.codabench.org` y de tutoriales de terceros; `check_codabench.py`, de la API de GitHub. Esos
sitios caen, se mueven y devuelven 429. Un CI que se pone en rojo por eso no dice nada sobre el
cambio que se está verificando, y un CI que falla sin culpa del cambio se acaba ignorando, que es
peor que no tenerlo.

**10. La generación de datasets se queda fuera.** El motor parametrizado por `spec.yaml` que
produce `public_data`, `reference_data`, `scoring_program` y `starting_kit` vive en el repositorio
privado `captia-technology/codabench-dataset-pipeline`, de acceso restringido, y se movió allí
antes de este montaje. Esta guía empieza cuando esos zips ya existen, y lo dice en la portada y en
los requisitos previos. Meterlo aquí obligaría a publicar en un sitio público el detalle de cómo se
extraen datos de un cliente.

## El andamiaje

Ficheros que existen a partir de este montaje, y qué papel tiene cada uno:

| Fichero | Papel |
|---|---|
| `docusaurus.config.js` | Configuración del sitio. Cada decisión no obvia lleva su porqué en comentario |
| `sidebars.js` | Sidebar autogenerado del árbol de `docs/`; el orden lo pone el front matter que genera `build_nav.py` |
| `package.json` | Docusaurus 3.10.2 con versiones fijadas, no rangos |
| `vercel.json` | Build, `cleanUrls`, `ignoreCommand`, caché de assets y cabeceras de seguridad. Sin un solo comentario, y es a propósito |
| `.gitattributes` | LF siempre: se edita en Windows y se construye en Linux |
| `.gitignore` | Excluye `node_modules/`, `build/`, `.docusaurus/`, `.claude/settings.local.json` y `scripts/privados.txt` |
| `src/css/custom.css` | El tema, copiado exacto del design system |
| `src/components/Portada/` | Las piezas de la portada, copiadas exactas |
| `static/img/logo-mark.svg` | El mark real del design system |
| `docs/index.mdx` | La portada: cuatro entradas por la pregunta que trae el lector, las seis secciones y cómo se lee una página |
| `docs/mapa-de-la-guia.md` | El mapa completo. **Generado** por `build_nav.py`; no se edita a mano |
| `scripts/check_docs.py` | Las invariantes de `docs/`. Corre en CI |
| `scripts/build_nav.py` | La navegación declarada, el mapa y `docs-map.json`. Corre en CI |
| `scripts/add_frontmatter.py` | `title` de un documento nuevo, a partir de su H1 |
| `scripts/normalize_headings.py` | Un solo H1 por documento |
| `scripts/check_fuentes.py` | Que las URL externas que cita la guía sigan vivas. A mano |
| `scripts/check_codabench.py` | Si la etiqueta de versión se ha quedado atrás; con `--fijar`, la sube. A mano |
| `.claude/settings.json` | Permisos del repositorio y el hook de validación |
| `.claude/hooks/validar_doc.py` | Valida el documento recién escrito y le devuelve los fallos a Claude |
| `.claude/rules/documentacion.md` | La plantilla de página y las invariantes, desarrolladas |
| `.claude/rules/design-system.md` | Los tokens de marca y por qué el tema no se bifurca |
| `.claude/skills/code-documentation/` | El método de documentación, adaptado a una fuente externa |
| `.github/workflows/docs-ci.yml` | La verificación en cada PR y push. **No publica nada** |
| `.github/ISSUE_TEMPLATE/` | Plantillas de corrección y de página nueva |
| `CLAUDE.md` | El índice del repositorio: dónde vive cada cosa y cuándo se carga |
| `README.md` | Empezar, organización, actualizar, desplegar, comandos y qué hacer cuando algo falla |
| `docs-meta/` | Este directorio |

Las invariantes están descritas en **tres sitios** —el hook, `check_docs.py` y
`.claude/rules/documentacion.md`— a propósito: cada uno actúa en un momento distinto (al escribir,
en CI, y al leer antes de escribir). El precio es que **si cambia una, cambian las tres**, y está
dicho en los tres ficheros.

## Lo que este montaje deliberadamente no hizo

- **No reescribió la prosa de la guía.** El contenido se repartió tal cual; ver
  [`02-reparto-del-contenido.md`](02-reparto-del-contenido.md).
- **No contrastó la etiqueta de versión contra una instancia.** Ver
  [`03-version-contrastada.md`](03-version-contrastada.md).
- **No añadió capturas.** Ver [`README.md`](README.md) de este directorio.
- **No creó la rama `develop`** ni renombró `master`. Es una decisión de flujo de trabajo, no de
  montaje, y se toma cuando haya más de una persona escribiendo a la vez.
