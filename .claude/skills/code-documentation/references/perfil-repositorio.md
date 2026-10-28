# Perfil de `codabench-docs`

Lo que esta skill necesita saber de este repositorio concreto para no trabajar a
ciegas. Es un perfil operativo, no una descripción del contenido: el contenido
está en `docs/` y el porqué de cada decisión en `docs-meta/`.

Confirmar cada dato leyendo el archivo que se cita. Un perfil escrito una vez
envejece; los archivos no.

## Qué es este sitio

Guía de cómo crear y mantener competiciones en **Codabench**, la plataforma
open-source para benchmarks y competiciones de machine learning, sucesora de
CodaLab. Sitio Docusaurus 3.10.2 en español, publicado en
`https://docs.codabench.captia.ai`.

| Clave | Valor | Dónde se comprueba |
| --- | --- | --- |
| Repositorio | `captia-technology/codabench-docs`, **público** | `docusaurus.config.js` (`organizationName`, `projectName`) |
| Sitio publicado | **público**, sin autenticación | La regla de datos publicables sale de ahí |
| Dominio | `https://docs.codabench.captia.ai` | `docusaurus.config.js`; el literal es respaldo, manda `VERCEL_PROJECT_PRODUCTION_URL` |
| Publica | Vercel, producción desde `main`; preview por pull request | `vercel.json` y el encabezado de `.github/workflows/docs-ci.yml` |
| Rama por defecto hoy | `master` | `git branch --show-current` |
| Versión rotulada | `Codabench v1.31.2` | `docusaurus.config.js`, `versions.current.label` |
| Idioma | español, un solo locale, sin prefijo de URL | `docusaurus.config.js`, bloque `i18n` |

`main` y `master` conviven a propósito: el workflow de CI nombra las dos ramas
porque un workflow que solo escuchara a una rama que todavía no existe no
fallaría, simplemente no se ejecutaría nunca. Comprobar la rama actual antes de
escribir y explicar la discrepancia si no coincide con lo que pide el usuario;
no cambiar de rama por cuenta propia. Una petición de auditoría sigue siendo de
solo lectura.

## La fuente es externa

Codabench **no** es un producto de la organización y no hay checkout de su
código. La evidencia de lo que afirma la guía sale de la documentación oficial
(`https://docs.codabench.org/`), de la observación directa de la interfaz y de
las competiciones reales ya montadas. Nada de eso se compara con `git diff`.

El repositorio privado `captia-technology/codabench-dataset-pipeline` genera los
ficheros que la guía asume ya preparados —`public_data`, `reference_data`,
`scoring_program`, `starting_kit`—. Es un vecino, no una fuente: la guía se
puede seguir sin él, con los zips hechos a mano. No enlazarlo como si el lector
tuviera acceso; el acceso está restringido.

Todo esto está desarrollado en `multi-repo-and-releases.md`.

## El árbol y lo que se publica

```text
docs/            lo ÚNICO que entra en el sitio
docs-meta/       cómo se montó y qué costó; NO se publica
scripts/         validadores y generadores, en Python 3.11
src/             tema y componentes; copia exacta del design system
static/img/      marca
.claude/         reglas, hook y esta skill
```

Un informe privado, una auditoría o una nota de trabajo van a `docs-meta/`,
nunca a `docs/` ni a `static/`: `static/` se sirve tal cual en el sitio público.

Bajo `docs/` las rutas son ASCII y en minúscula, sin tildes ni guiones bajos, y
en la raíz de `docs/` solo pueden vivir `index.mdx` y `mapa-de-la-guia.md`.
No es una preferencia estética: el sistema de ficheros de Windows no distingue
mayúsculas y el CI corre en Linux, así que un enlace a `Conceptos.md` que apunte
a `conceptos.md` abre en local y devuelve 404 en producción.

## La navegación se declara, no se deduce

El orden del sidebar, la etiqueta corta de cada página, los `_category_.json`,
la página del mapa y `docs-map.json` salen todos de la lista `SECCIONES`, dentro
de `scripts/build_nav.py`. Si aparece un documento que no está declarado ahí, el
script **falla** y CI con él.

Es deliberado: colocar una página en el recorrido de la guía es una decisión
editorial, no un efecto secundario de crear un fichero. Para añadir una página:
declararla en `SECCIONES` con su sección y sus fuentes, y ejecutar los scripts.

`sidebar_position`, `sidebar_label` y `description` del front matter los escribe
`build_nav.py --apply`; no se ponen a mano. La `description` se deriva de la
primera frase del rótulo `**Objetivo:**` del cuerpo.

## Comandos

```bash
python scripts/check_docs.py           # invariantes del contenido; es lo que corre en CI
python scripts/build_nav.py --check    # navegación declarada, mapa y docs-map
python scripts/build_nav.py --apply    # regenera front matter, _category_.json, mapa y docs-map
python scripts/add_frontmatter.py --apply
python scripts/normalize_headings.py --apply
npm run build                          # build de producción, SIN --locale
npm start                              # previsualización local
```

Y dos comprobaciones más que **no** corren en CI porque necesitan red y dependen
de servidores ajenos:

```bash
python scripts/check_codabench.py      # ¿hay release nueva de Codabench? qué páginas revisar
python scripts/check_fuentes.py        # ¿siguen vivas las URLs externas que cita la guía?
```

`check_codabench.py` compara la etiqueta `Codabench v1.31.2` que declara este
sitio con la última release publicada en
`https://api.github.com/repos/codalab/codabench/releases/latest`, y lista qué
páginas dependen de qué fuentes leyéndolo de `docs-map.json`. Sale 0 al día, 1
si hay algo que revisar y 2 si no pudo consultar la API. **No revisa contenido**:
que una versión nueva cambie las pantallas descritas solo se sabe abriéndolas.
Su `--fijar` es el cierre mecánico y va DESPUÉS de esa revisión, nunca antes.
`check_fuentes.py` comprueba las URLs externas de `docs/` y de `docs-map.json`
—`--listar` las enumera sin tocar la red— y sale 1 si alguna falla.

Al añadir un documento el orden es `normalize_headings.py`,
`add_frontmatter.py` y `build_nav.py`, en ese orden: normalizar los
encabezados antes de derivar el front matter, y declarar la navegación al
final, cuando el documento ya tiene título y objetivo.

Python es 3.11 y se invoca como `python`. Node es 22. El CI usa Python 3.12 y
Node 22, así que un script que dependa de un detalle de 3.11 pasaría en local y
fallaría en CI.

Nunca pasar `--locale` al build: con un solo locale, Docusaurus publica en la
raíz; con `--locale en` el sitio inglés se publicaría en la raíz y machacaría al
español.

## Las invariantes del contenido

Están escritas una sola vez, en `.claude/rules/documentacion.md`, y las
comprueban `scripts/check_docs.py` (en CI) y el hook `.claude/hooks/validar_doc.py`
(al escribir). Esta skill no las repite para no crear una segunda versión que se
desincronice: leerlas ahí antes de redactar.

Lo que conviene tener presente al documentar: front matter con `title`, un solo
H1 que dice lo mismo que el `title`, imágenes en sintaxis Markdown y
co-ubicadas, enlaces relativos que resuelven con la caja exacta, filas de tabla
cuadradas —una `|` dentro de `` `código` `` también separa celdas en GFM y hay
que escribirla `\|`—, y nada publicable que identifique a nadie.

## Datos que no pueden publicarse

El repositorio es público: el sitio pide credencial, pero `docs/` se lee en GitHub sin ella. En `docs/` no puede aparecer un correo
con dominio real (se permiten `@ejemplo.com` y `@example.com`), una dirección
IP, una credencial o token, la URL de una instancia interna de Codabench, ni
ningún identificador de la lista `scripts/privados.txt`.

Ese fichero **no se versiona** y esta skill **no debe leerlo**: su contenido es
justamente lo que se quiere proteger. Lo consumen `check_docs.py` y el hook.

## Marca y acabado

El tema no se diseña aquí: `src/css/custom.css`, `src/components/Portada/` y
`static/img/logo-mark.svg` son copia exacta del manual de captia.ai, que es la
implementación de referencia del Captia Technology Design System. Reutilizar,
no reinventar; leer `captia-design-contract.md` antes de tocar estilos y
`professional-experience.md` antes de tocar estructura visual.

Usar `showcase-patterns.md` para ideas de organización, no para copiar otras
marcas. Validar el render según `visual-qa.md`.

Hoy la guía **no tiene capturas de pantalla**. Es contenido procedimental: pasos
numerados y rótulos de la interfaz en negrita. Si algún día se añaden capturas,
pasan a aplicarse las reglas de imágenes de `.claude/rules/documentacion.md` y
la revisión de datos personales de `security-and-verification.md`; hasta
entonces, no describir una pantalla como si se hubiera capturado.
