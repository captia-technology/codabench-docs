# `docs-meta/` — cómo está montado este repositorio y por qué

Documentos de trabajo sobre el propio repositorio: de dónde se replicó el patrón, cómo se repartió
el contenido, qué se decidió y con qué argumento.

**No son documentación de producto.** Viven fuera de `docs/`, que es lo único que entra en el sitio
publicado, así que quedan excluidos automáticamente. No los muevas dentro de `docs/`.

Existen porque el porqué de una decisión no cabe en el sitio ni en un comentario de código, y sin
él la decisión se deshace sola: alguien ve `markdown.format: 'detect'`, no entiende para qué está,
lo quita y el build se cae. Aquí es donde se busca antes de deshacer algo.

## Estado actual

El repositorio pasa de ser **una guía de un solo fichero** (`docs/crear-competicion.md`, 236
líneas) a un **sitio Docusaurus de 21 páginas en 6 secciones**, con el tema del Captia Technology
Design System, validadores en Python, verificación en CI y publicación en Vercel. El patrón se
replica del manual de captia.ai (`my-qa-captia-ai-app`); qué se copió exacto y qué se adaptó está
en [`01-setup-inicial.md`](01-setup-inicial.md).

El contenido publicado se etiqueta como contrastado con **Codabench v1.23**. Esa etiqueta tiene un
origen concreto y limitado, y [`03-version-contrastada.md`](03-version-contrastada.md) existe para
que no se convierta en una afirmación falsa sin que nadie se dé cuenta.

## Los documentos

| Documento | Qué contiene | Vigencia |
|---|---|---|
| [`01-setup-inicial.md`](01-setup-inicial.md) | El montaje del 2026-09-10: de dónde se replicó el patrón, qué se copió exacto, qué se adaptó y qué se decidió | **Instantánea fechada** — registro de cómo quedó montado, no se reescribe |
| [`02-reparto-del-contenido.md`](02-reparto-del-contenido.md) | De dónde sale cada página del sitio: la correspondencia entre las 16 partes de la guía original —preámbulo, 14 secciones y Referencias— y las 16 páginas que las heredan | **Vigente** — es la trazabilidad del contenido |
| [`03-version-contrastada.md`](03-version-contrastada.md) | De dónde salió la etiqueta «Codabench v1.23» del primer corte, qué **no** significaba, y qué haría falta para contrastarla de verdad | **Vigente** — se actualiza cada vez que la etiqueta cambie |
| [`04-sync-codabench-v1.31.2.md`](04-sync-codabench-v1.31.2.md) | La revisión de v1.23 a v1.31.2: qué cambió de verdad, qué no era desfase sino hueco, y qué queda pendiente | **Vigente** — es el registro del ciclo de versión |

## Dos avisos que valen siempre

**El sitio es público, y el repositorio también.** Esta carpeta no entra en el sitio —Docusaurus
solo publica `docs/`—, pero se lee desde GitHub como cualquier otro fichero: no es un cuaderno
privado. Codabench se despliega por instancias, y lo que no puede salir es concreto: la URL de una instancia interna, el
nombre de una cola de ejecución de un cliente, correos con dominio real, IPs, claves o tokens. Hoy
la guía no tiene capturas; el día que las tenga, revísalas antes de subirlas, porque una captura de
la interfaz de Codabench lleva la URL en la barra y el usuario en la esquina.

**Estos documentos se escriben con fecha y no se reescriben para que cuadren.** Un registro que se
actualiza para parecer siempre correcto no sirve de nada: la gracia de `01` es que dice cómo se
montó el 2026-09-10, aunque después algo haya cambiado. Lo que cambia se anota como nota posterior
fechada, encima de lo que corrige.

## Scripts

| Script | Para qué | Estado |
|---|---|---|
| `scripts/check_docs.py` | Invariantes de `docs/`: front matter, un H1 por página, `title` == H1, enlaces e imágenes que resuelven con la caja exacta, tablas cuadradas, rutas ASCII, nada publicable que identifique a nadie. Sale con 1 si falla | En uso, corre en CI |
| `scripts/build_nav.py` | **Fuente única de la navegación**: orden y etiqueta de cada documento, los `_category_.json`, `docs/mapa-de-la-guia.md` y `docs-map.json`. Falla si aparece un documento sin declarar en `SECCIONES` | En uso, corre en CI |
| `scripts/add_frontmatter.py` | `title` de un documento nuevo, a partir de su H1. El orden no sale de aquí: lo declara `build_nav.py` | En uso al añadir docs |
| `scripts/normalize_headings.py` | Deja un solo H1 por documento | En uso al añadir docs |
| `scripts/check_fuentes.py` | Que las URL externas que cita la guía sigan vivas. `check_docs.py` solo valida los enlaces relativos, así que una fuente rota se degrada en silencio | En uso, a mano (sale a la red) |
| `scripts/check_codabench.py` | Compara la última release publicada de `codalab/codabench` con la versión que declara este sitio. Con `--fijar`, cierra el ciclo subiendo la etiqueta | En uso, a mano (sale a la red) |

Los dos últimos **no corren en CI a propósito**: dependen de sitios ajenos —`docs.codabench.org` y
la API de GitHub—, que caen, se mueven y devuelven 429. Un CI que se pone en rojo por eso no dice
nada sobre el cambio que se está verificando y enseña al equipo a ignorar el rojo.

**Cómo añadir un documento**, en este orden:

```bash
python scripts/normalize_headings.py --apply   # un solo H1
python scripts/add_frontmatter.py --apply      # title a partir del H1
# declararlo a mano en SECCIONES, dentro de scripts/build_nav.py
python scripts/build_nav.py --apply            # posición, etiqueta, categorías, mapa y docs-map
python scripts/check_docs.py                   # invariantes
```

El paso de en medio es a mano **a propósito**: colocar una página en el recorrido de la guía es una
decisión, y `build_nav.py` se niega a pasar hasta que se toma.

## Por qué `vercel.json` no lleva comentarios

JSON no los admite, y simularlos con una clave inventada tampoco funciona: Vercel valida
`vercel.json` contra su esquema y **rechaza las propiedades que no reconoce**. En el repositorio de
referencia, un `_comentario_ignoreCommand` dejó la configuración inválida y el despliegue caído
tres días, sin que ningún build llegara a arrancar. Lo insidioso es que **el CI seguía en verde**,
porque construye el sitio con las mismas órdenes pero no lee `vercel.json`: un build correcto no
dice nada sobre si la configuración de despliegue es válida.

Así que si hay que explicar una opción de ese fichero, la explicación va aquí. Empezando por la
que más sorprende, el `ignoreCommand`:

```
git rev-parse HEAD^ >/dev/null 2>&1 || exit 1
git diff --quiet HEAD^ HEAD -- docs src static docusaurus.config.js sidebars.js \
                               package.json package-lock.json vercel.json
```

Salta el build cuando el commit no toca nada que salga en el sitio —por ejemplo, solo `docs-meta/`
o `.claude/`—. Convenio de Vercel: código 0 = saltar, 1 = construir. Compara **solo el último
commit** contra su padre, así que una tanda de commits tiene que **terminar** con uno que toque
`docs/`, `src/`, `static/` o la configuración; si no, no se publica nada por mucho que los
anteriores hayan cambiado la guía entera. Si no existe `HEAD^` —clon superficial, primer
despliegue— la primera línea sale con 1 y construye, que es el lado seguro del error.

Y las cabeceras: `X-Robots-Tag: noindex, nofollow` se aplica **solo** cuando el host es
`codabench-docs.vercel.app`, el dominio provisional. Así el sitio no compite consigo mismo en
buscadores mientras se da de alta `docs.codabench.captia.ai`, ni deja resultados que caduquen el
día del corte. El resto son caché de assets y cabeceras de seguridad estándar.

## Lo que queda pendiente

**Dar de alta `docs.codabench.captia.ai`** en el proyecto de Vercel. La configuración ya está
preparada: `url` sale de `VERCEL_PROJECT_PRODUCTION_URL` y `baseUrl` es `/`, así que el canonical,
el Open Graph y el sitemap se corrigen solos el día que el dominio se asigne, sin tocar
`docusaurus.config.js`.

**Decidir el nombre de la rama de producción.** Hoy la rama por defecto del repositorio es
`master` (`origin/HEAD → origin/master`), mientras que el montaje se especificó sobre `main`.
`.github/workflows/docs-ci.yml` lista las dos a propósito, porque un workflow que solo nombrara la
rama que aún no existe no fallaría: simplemente no se ejecutaría nunca, y nadie lo notaría. Vercel
no admite esa ambigüedad —tiene una sola *Production Branch*—, así que hay que renombrar la rama o
confirmar en el panel cuál está configurada. Es un desajuste que no da error en ninguna parte:
simplemente no despliega.

**Contrastar la versión de verdad.** Ver [`03-version-contrastada.md`](03-version-contrastada.md):
hoy «v1.23» sale de una URL de la documentación oficial, no de una instancia.

**Capturas.** La guía es procedimental y describe formularios que el lector tiene delante; no hay
ni una imagen. Añadirlas obligaría a auditar cada una antes de publicarla, porque una captura de
Codabench lleva la instancia y el usuario a la vista. La plantilla de página ya contempla imágenes
co-ubicadas junto a su `.md`, así que la decisión se puede tomar más adelante sin rehacer nada.
