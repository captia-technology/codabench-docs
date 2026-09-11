# Documentación de Codabench

Guía de cómo crear y mantener competiciones en **Codabench**: 21 páginas en español repartidas en
6 secciones, construida con [Docusaurus](https://docusaurus.io/) 3.10.2 y publicada en Vercel.

| | |
|---|---|
| **Sitio** | `docs.codabench.captia.ai` |
| **Contenido** | Contrastado con **Codabench v1.23**. Esa etiqueta sale de las URL de la documentación oficial que citaba la guía original, **no** de una comprobación contra una instancia viva: ver [`docs-meta/03-version-contrastada.md`](docs-meta/03-version-contrastada.md) |
| **Publica** | Vercel, desde la rama de producción. GitHub Actions solo verifica |
| **Repositorio** | `captia-technology/codabench-docs`, **público**. El sitio también |

> **Lo primero que hay que interiorizar**: aquí **todo es público**. No solo el sitio: el
> repositorio también, así que `docs-meta/`, `scripts/` y `.claude/` se leen desde GitHub aunque no
> entren en el sitio publicado. La regla de qué no puede salir vale para el árbol entero, no solo
> para `docs/`. Codabench se despliega por instancias, así que lo que no puede salir es concreto:
> la URL de una instancia interna, la cola de ejecución de un cliente, correos con dominio real,
> direcciones IP, claves o tokens de API. Un hook lo comprueba al escribir y
> `scripts/check_docs.py` lo bloquea en CI —ambos cubren `docs/`; **fuera de `docs/` no hay red de
> seguridad automática** y la revisión es humana—.

---

## Índice

- [Empezar](#empezar)
- [Cómo está organizado](#cómo-está-organizado)
- [Actualizar la documentación](#actualizar-la-documentación)
  - [Editar una página existente](#editar-una-página-existente)
  - [Añadir una página nueva](#añadir-una-página-nueva)
  - [Cuando Codabench cambia](#cuando-codabench-cambia)
- [Desplegar](#desplegar)
- [Comandos](#comandos)
- [Reglas que rompen el sitio si se incumplen](#reglas-que-rompen-el-sitio-si-se-incumplen)
- [Cuando algo falla](#cuando-algo-falla)
- [Para saber más](#para-saber-más)

---

## Empezar

Requisitos: **Node 22** (el `engines` de `package.json` exige ≥20, que es lo que comprueba el propio
arranque de Docusaurus 3.10; CI y Vercel usan 22) y **Python 3.11+** para los scripts de validación
—en esta máquina se invoca como `python`; el CI usa 3.12—.

> **Python tiene que responder al nombre `python`.** No es un detalle de estilo: el hook de
> `.claude/settings.json` invoca `python .claude/hooks/validar_doc.py` en cada escritura, y en
> muchas instalaciones de Linux y macOS solo existe `python3`. Ahí el hook moriría con 127 en cada
> edición y la validación al escribir se perdería en silencio (el CI seguiría cubriendo el
> contenido, porque `actions/setup-python` sí pone `python` en el PATH). En una máquina así, o se
> crea el alias, o se ajusta el comando en `.claude/settings.local.json`, que no se versiona.

```bash
npm ci             # instalación limpia desde el lockfile, igual que hacen CI y Vercel
npm start          # previsualización local con recarga en caliente
npm run build      # build de producción — SIN --locale, ver más abajo
npm run serve      # sirve el build ya construido, para comprobarlo como en producción
```

> `npm run build` va **deliberadamente sin `--locale`**. Con un único idioma, construir uno
> concreto no añade prefijo de URL: pasar `--locale` publicaría ese idioma en la raíz del sitio.
> El día que se añada `en`, ese locale vivirá bajo `/en/` sin romper ningún enlace entrante.

---

## Cómo está organizado

| Dónde | Qué contiene | Se publica |
|---|---|---|
| `docs/` | Las 21 páginas de la guía en sus 6 secciones, más la portada (`index.mdx`) y el mapa generado | **Sí** |
| `src/` | Componentes de la portada y el tema | Sí (compilado) |
| `static/` | El mark del design system y el resto de estáticos | Sí |
| `scripts/` | Validadores y generadores, en Python. Los que escriben en el árbol son idempotentes y traen `--check`; los `check_*` no escriben nada | No |
| `docs-meta/` | Cómo se montó todo y por qué cada decisión es como es. Registros fechados | **No** |
| `.claude/rules/` | `documentacion.md` (al tocar `docs/`) y `design-system.md` (al tocar el tema) | No |
| `.claude/hooks/` | `validar_doc.py`, que valida cada documento justo después de escribirlo | No |
| `.github/workflows/` | `docs-ci.yml`: la verificación en cada PR y push. **No publica nada** | No |
| `.github/dependabot.yml` | Vigila las acciones del workflow y Docusaurus. Solo abre PR; la CI las valida | No |

El recorrido de las seis secciones es el orden real de montar una competición: **Empezar →
Competición → Recursos → Evaluación → Submissions → Referencia**. No es alfabético y no es
casual; una página leída fuera de ese recorrido se lee fuera de contexto.

### La navegación se declara, no se deduce

Es la decisión estructural más importante del repositorio. El orden del sidebar, la etiqueta de
cada página, los `_category_.json`, el mapa de la guía (`docs/mapa-de-la-guia.md`) y
`docs-map.json` salen **todos** de `SECCIONES`, dentro de
[`scripts/build_nav.py`](scripts/build_nav.py).

Si aparece un documento que no está declarado ahí, **el script falla y CI con él**. Es
deliberado: colocar una página en el recorrido de la guía es una decisión, no un detalle. La
alternativa —dejar que Docusaurus ordene por nombre de fichero— pondría `collaborators` antes que
`details` dentro de Competición, que es exactamente al revés de como se rellena el formulario.

En la raíz de `docs/` solo pueden vivir dos ficheros: la portada `index.mdx` y el mapa
`mapa-de-la-guia.md`, que está **generado**. Todo lo demás va dentro de su sección.

### `docs-meta/` no se publica, y es a propósito

Vive fuera de `docs/`, que es lo único que entra en el sitio. Contiene el porqué de cada decisión
—de dónde se replicó el patrón, cómo se repartió el contenido original, de dónde sale la etiqueta
de versión— y ese material no es documentación de producto: es documentación del repositorio. Ver
[`docs-meta/README.md`](docs-meta/README.md).

---

## Actualizar la documentación

### Editar una página existente

Todas las páginas comparten la misma plantilla —front matter, un H1, el rótulo `Objetivo:` y
secciones en H2—, descrita en
[`.claude/rules/documentacion.md`](.claude/rules/documentacion.md), que es lectura obligada antes
de tocar `docs/`.

Al terminar:

```bash
python scripts/check_docs.py
```

Sale con código 1 si algo falla y dice qué. Es la misma comprobación que corre en CI.

### Añadir una página nueva

```bash
# 1. Escribir el .md dentro de su sección de docs/, en ruta ASCII y minúscula
python scripts/normalize_headings.py --apply   # un solo H1 por documento
python scripts/add_frontmatter.py --apply      # title a partir del H1

# 2. Declararla en SECCIONES, dentro de scripts/build_nav.py    <-- a mano, es una decisión
python scripts/build_nav.py --apply            # posición, etiquetas, categorías, mapa y docs-map

# 3. Comprobar
python scripts/check_docs.py && npm run build
```

**En ese orden.** El paso 2 no está automatizado a propósito: `build_nav.py` se niega a pasar
hasta que coloques la página en el recorrido.

Y una restricción que sorprende la primera vez: **las rutas van en ASCII y en minúscula**, sin
tildes, sin mayúsculas y sin guiones bajos. El repositorio de referencia arrastra rutas heredadas
con tildes y las resuelve con un `slug` transliterado por documento; aquí, con el árbol partiendo
de cero, sale más barato prohibirlo de entrada que mantener la excepción.

### Cuando Codabench cambia

Esto es lo más fácil de olvidar y lo que más daño hace.

El sitio afirma, en el pie de todas las páginas y en el desplegable de versión, estar
**«contrastado con Codabench v1.23»**. No es un adorno: es la afirmación que sostiene todo lo
demás. Codabench es un producto externo y sigue su propio calendario; cuando publique una versión
que cambie la interfaz descrita y nadie toque la guía, esa frase pasará a ser falsa en un sitio
público y **ningún build ni validador lo detectará**: el sitio compila perfectamente mientras
miente.

**Paso 1 — ver si la etiqueta se ha quedado atrás.**

```bash
python scripts/check_codabench.py
```

Compara la última release publicada de Codabench (`codalab/codabench` en GitHub) con la versión que
declara este sitio. Sale con **0** si está al día, **1** si hay algo que revisar y **2** si no pudo
consultar la API. No revisa contenido —eso no lo puede hacer un script—: dice qué páginas dependen
de qué fuentes, leyéndolo de `docs-map.json`, para que la revisión sea acotada.

Es una comprobación de red y **no** corre en CI: un CI que depende de un sitio ajeno acaba fallando
por motivos que no tienen nada que ver con el cambio que se está revisando, y un CI que falla sin
culpa del cambio se acaba ignorando.

**Paso 2 — revisar el contenido.** Trabajo de criterio, y el que no se automatiza: hay que abrir
la interfaz de Codabench y contrastar pantalla a pantalla las páginas afectadas. Qué páginas son
lo dice `docs-map.json`, que declara las fuentes de cada sección —URLs de la documentación
oficial y, donde corresponda, «observación directa de la UI»—. La pregunta que responde es
exactamente esta: si Codabench cambia, ¿qué páginas hay que revisar?

**Paso 3 — cerrar el ciclo.**

```bash
python scripts/check_codabench.py --fijar   # sube la etiqueta de versión donde aparece
python scripts/build_nav.py --apply         # regenera el mapa y docs-map.json
python scripts/check_docs.py && npm run build
```

> **`--fijar` nunca antes del paso 2.** Cambiar «v1.23» por la versión nueva sin haber revisado las
> páginas no actualiza nada: convierte una afirmación **caducada** en una **falsa**, que es peor,
> porque la caducada se detecta comparando versiones —justamente con este script— y la falsa solo
> la descubre un lector siguiendo instrucciones que ya no encajan con lo que tiene en pantalla.

Lo que se revisó y contra qué se contrastó se anota en `docs-meta/`, con fecha. Reescribir esos
registros para que cuadren con la versión nueva daría un historial falso.

---

## Desplegar

```
commit  ──►  push a la rama de trabajo  ──►  abrir el pull request  ──►  GitHub Actions verifica
                                                                                │
                                                                                ▼
                                                   merge --ff-only a la rama de producción
                                                                                │
                                                                                ▼
                                                        push  ──►  Vercel construye y publica
```

> **El pull request es lo que dispara el CI, no el push.** `docs-ci.yml` declara
> `on: push` y `on: pull_request` **solo contra `main` y `master`**: empujar a una rama de trabajo
> sin pull request abierto no ejecuta absolutamente nada, y no hay ningún aviso de que no se ha
> ejecutado. O se abre el pull request, o se lanza a mano —el workflow trae `workflow_dispatch`—,
> o se verifica en local con `python scripts/check_docs.py && python scripts/build_nav.py --check`.

**Vercel es el único que publica.** Está conectado al repositorio: despliega producción desde la
rama de producción y una preview por cada pull request.
[`docs-ci.yml`](.github/workflows/docs-ci.yml) **no publica nada**; cubre lo que el build de Vercel
no ve —`check_docs.py` y `build_nav.py --check`, que son Python— y tumba el PR antes de que nadie
mire la preview. Y cubre además el caso que Vercel ni siquiera intenta: un cambio en `scripts/`,
que puede romper la validación de todas las páginas, no dispara ningún build de Vercel.

> **Ojo con el nombre de la rama.** Hoy la rama por defecto de este repositorio es `master`
> (`origin/HEAD → origin/master`), mientras que el montaje se especificó sobre `main`.
> `docs-ci.yml` lista las dos a propósito —un workflow que solo nombrara la rama que aún no existe
> no fallaría: simplemente no se ejecutaría nunca—, pero Vercel no admite esa ambigüedad. Lo que
> manda es la rama que el proyecto tenga configurada como *Production Branch*: compruébalo en el
> panel antes de dar por hecho que un push publica. Es la clase de desajuste que no da error en
> ninguna parte y simplemente no despliega.

### Dos trampas de Vercel

**1. El orden de los commits decide si se publica.** `vercel.json` trae un `ignoreCommand` que
salta el build cuando el commit no toca nada que salga en el sitio (por ejemplo, solo `docs-meta/`
o `.claude/`). Compara **únicamente el último commit contra su padre**:

```
git rev-parse HEAD^ >/dev/null 2>&1 || exit 1
git diff --quiet HEAD^ HEAD -- docs src static docusaurus.config.js sidebars.js \
                               package.json package-lock.json vercel.json
```

Convenio de Vercel: código 0 = saltar el build, 1 = construir. La primera línea es la red de
seguridad para cuando no existe `HEAD^` —clon superficial, primer despliegue—: sale 1 y construye,
que es el lado seguro del error.

La consecuencia práctica es la que muerde: una tanda de commits que **termine** tocando solo
`scripts/` o `docs-meta/` **no publica nada**, por mucho que los commits anteriores hayan cambiado
la guía entera. Si vas a subir varios commits, deja el que toca `docs/` para el final.
Comprobarlo antes es una línea:

```bash
git diff --quiet HEAD^ HEAD -- docs src static docusaurus.config.js sidebars.js \
  package.json package-lock.json vercel.json && echo "SALTA" || echo "CONSTRUYE"
```

**2. `vercel.json` no admite comentarios ni claves inventadas.** JSON no tiene comentarios, y
Vercel valida el fichero contra su esquema y **rechaza las propiedades que no reconoce**. En el
repositorio de referencia, un intento de simular un comentario con una clave `_comentario_…` dejó
el despliegue caído tres días: la configuración quedaba inválida y el build ni arrancaba. Lo
insidioso es que **el CI seguía en verde**, porque construye el sitio con las mismas órdenes pero
no lee `vercel.json`. Un build correcto no dice nada sobre si la configuración de despliegue es
válida.

Por eso el `vercel.json` de aquí no lleva ni un comentario. Si hay que explicar una opción, la
explicación va a [`docs-meta/README.md`](docs-meta/README.md).

### Rollback

| Situación | Qué hacer |
|---|---|
| Un despliegue rompió el sitio | *Instant Rollback* en el panel de Vercel — inmediato, sin tocar el repositorio |
| Hay que deshacerlo en git | `git revert <sha>` y push. Recuerda que el último commit debe tocar una ruta vigilada para que Vercel reconstruya |
| El contenido está mal pero el sitio funciona | Corregir y volver a desplegar; no hace falta rollback |

### La fecha de actualización necesita el historial completo

`docusaurus.config.js` trae `showLastUpdateTime: true`, y esa fecha sale de `git log`, no del
sistema de ficheros. El CI ya lo cubre con `fetch-depth: 0`, pero **Vercel clona en superficial y
no hay opción equivalente en `vercel.json`**: hay que declarar `VERCEL_DEEP_CLONE=true` en las
variables de entorno del proyecto. Sin ella el sitio compila igual —el aviso
`Cannot infer the update date` no rompe nada— pero todas las páginas acaban mostrando la misma
fecha, que es peor que no mostrar ninguna: dice que el manual se revisó entero el día del último
despliegue.

### Dominio

El sitio se sirve en la raíz de su dominio (`baseUrl: '/'`) y el `url` sale de
`VERCEL_PROJECT_PRODUCTION_URL`, la variable que inyecta Vercel con el dominio de producción del
proyecto. En cuanto `docs.codabench.captia.ai` quede asignado ahí, el canonical, el Open Graph y
el sitemap se corrigen solos sin tocar `docusaurus.config.js`; el literal que hay en el fichero es
solo el respaldo para builds locales y para el primer despliegue.

Mientras el subdominio no exista, el sitio se sirve en `codabench-docs.vercel.app`, y para ese
host `vercel.json` devuelve `X-Robots-Tag: noindex, nofollow`: así el dominio provisional no
compite en buscadores con el definitivo ni deja resultados que caduquen el día del corte.

---

## Comandos

| Comando | Para qué |
|---|---|
| `python scripts/check_docs.py` | Invariantes de `docs/` — **lo mismo que corre en CI** |
| `python scripts/build_nav.py --check` | Navegación declarada, mapa y `docs-map.json` — **también en CI** |
| `python scripts/build_nav.py --apply` | Regenera el orden, los `_category_.json`, el mapa y `docs-map.json` |
| `python scripts/add_frontmatter.py --apply` | `title` de un documento nuevo, a partir de su H1 |
| `python scripts/normalize_headings.py --apply` | Un solo H1 por documento |
| `python scripts/check_fuentes.py` | Que las URL externas que cita la guía sigan vivas. De red, a mano |
| `python scripts/check_codabench.py` | ¿Sigue siendo v1.23 la versión contrastada? De red, a mano |
| `python scripts/check_codabench.py --fijar` | Cierra el ciclo tras revisar: sube la etiqueta de versión donde aparece |
| `npm run build` | Build de producción, **sin `--locale`** |

Los tres que **escriben** en el árbol —`build_nav.py`, `add_frontmatter.py` y
`normalize_headings.py`— son idempotentes y llevan las dos caras del mismo par: `--apply` escribe y
`--check` no escribe y sale con 1 si queda algo por hacer, que es la forma en que corren en CI. Los
`check_*` no llevan `--check` porque comprobar es lo único que hacen; la única excepción que
escribe es `check_codabench.py --fijar`.

Los dos que salen a la red no corren en CI a propósito: dependen de un sitio ajeno, y su fallo no
diría nada sobre el cambio que se está verificando.

---

## Reglas que rompen el sitio si se incumplen

Están desarrolladas en [`.claude/rules/documentacion.md`](.claude/rules/documentacion.md), y son
exactamente las que comprueban el hook y `scripts/check_docs.py` —una lista, tres implementaciones:
si cambia una, cambian las tres—. En corto, con lo que ocurre si se incumplen:

1. **Front matter con `title`, y ese `title` dice lo mismo que el H1.** Si divergen, la pestaña
   del navegador, el resultado de búsqueda y el encabezado de la página dicen tres cosas distintas.
2. **Un solo H1 por documento.** El índice lateral arranca en H2: una sección escrita con `#` no
   aparece en él.
3. **Imágenes en sintaxis Markdown, nunca `<img>`.** Docusaurus solo convierte a `require()` las
   rutas de `![alt](./fichero.png)`; un `<img src="./x.png">` compila y da imagen rota. Nunca
   remotas, nunca desde `github.com/user-attachments`, siempre co-ubicadas junto a su `.md`.
4. **Todo enlace relativo a un `.md` resuelve, con la caja exacta del fichero.** El sistema de
   ficheros de Windows es insensible a mayúsculas y el CI corre en Linux: un enlace con la caja
   cambiada pasa en local y rompe el build en CI.
5. **Filas de tabla cuadradas, y un `|` dentro de `` `código` `` también separa celdas.** Hay que
   escribirlo `\|`, o Markdown recorta la fila en silencio.
6. **Rutas ASCII y en minúscula** bajo `docs/`, sin tildes ni mayúsculas.
7. **Nada publicable que identifique a nadie.** El sitio es público: ni correos con dominio real
   —`@ejemplo.com` y `@example.com` sí—, ni IPs, ni credenciales o tokens, ni URLs de instancias
   internas de Codabench.
8. **Ninguna imagen huérfana** en `docs/`, y **todo documento declarado en `SECCIONES`**.

Y la que no rompe el build pero sí la guía: toda página que no sea la portada ni el mapa abre con
el rótulo **`Objetivo:`** en negrita. De esa frase sale la `description` del front matter, que es
lo que se lee en el buscador antes de entrar. `check_docs.py` la avisa sin bloquear, porque es
calidad editorial y no algo que tumbe el sitio.

Ninguna de estas reglas nace aquí de un fallo publicado —este repositorio no tiene todavía ese
historial—: vienen de la implementación de referencia, donde cada una costó un build o un
despliegue.

---

## Cuando algo falla

**El build dice «broken link».** `onBrokenLinks: 'throw'` está puesto a propósito. Mira si el
destino cambió de sección: los enlaces internos son relativos entre documentos, así que mover una
página rompe los que apuntan a ella. Si el enlace es correcto y aun así falla, caché rancia:
`npm run clear` y reconstruir.

**El build falla con un error de JSX dentro de un `.md`.** Una llave suelta.
`markdown.format: 'detect'` devuelve los `.md` a CommonMark justo para evitarlo, así que si
aparece, o el fichero es un `.mdx` o alguien tocó esa opción. Esta guía habla de plantillas de
comando (`command: python3 $program/scoring.py $input $output`) y de claves de `scores.txt`: las
llaves llegan tarde o temprano.

**Cambié algo y el sitio no se actualiza.** Mira si el último commit toca una ruta vigilada; ver
[trampa 1](#dos-trampas-de-vercel). Y comprueba que la *Production Branch* del proyecto de Vercel
es la rama a la que estás empujando.

**El sitio carga sin estilos.** Síntoma clásico de un `baseUrl` que no coincide con la ruta en la
que se sirve. Debe ser `'/'`.

**`build_nav.py` falla con un documento sin declarar.** Es lo que tiene que hacer. Decláralo en
`SECCIONES`.

**CI en verde pero el despliegue en rojo.** El CI no lee `vercel.json`; ver
[trampa 2](#dos-trampas-de-vercel).

---

## Para saber más

| Documento | Qué cuenta |
|---|---|
| [`docs-meta/01-setup-inicial.md`](docs-meta/01-setup-inicial.md) | De dónde se replicó el patrón, qué se copió exacto y qué se adaptó |
| [`docs-meta/02-reparto-del-contenido.md`](docs-meta/02-reparto-del-contenido.md) | De dónde sale cada página del sitio, sección a sección |
| [`docs-meta/03-version-contrastada.md`](docs-meta/03-version-contrastada.md) | De dónde sale «Codabench v1.23» y qué haría falta para contrastarla de verdad |
| [`.claude/rules/documentacion.md`](.claude/rules/documentacion.md) | La plantilla de página y las invariantes, desarrolladas |
| [`.claude/rules/design-system.md`](.claude/rules/design-system.md) | Los tokens de marca y por qué el tema no se bifurca |
| [`CLAUDE.md`](CLAUDE.md) | El índice del repositorio para trabajar con Claude Code |

Los ficheros de la competición —`public_data`, `reference_data`, `scoring_program`,
`starting_kit`— **no se generan aquí**. Salen del motor parametrizado por `spec.yaml` del
repositorio privado `captia-technology/codabench-dataset-pipeline` (acceso restringido). Esta guía
empieza cuando esos zips ya existen.
