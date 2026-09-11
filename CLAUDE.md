# codabench-docs

Sitio de documentación de **cómo crear y mantener competiciones en Codabench**: 21 páginas en
español repartidas en 6 secciones, con Docusaurus 3.10.2 y publicado en Vercel bajo
**https://docs.codabench.captia.ai**. El contenido se etiqueta como contrastado con **Codabench
v1.23**; esa etiqueta sale de las URL de la documentación oficial que citaba la guía original y
**no** de una comprobación contra una instancia viva —ver
[`docs-meta/03-version-contrastada.md`](docs-meta/03-version-contrastada.md), que existe
precisamente para que eso no se olvide—.

Este fichero es un índice, no un manual. El detalle vive donde se carga solo cuando hace falta:

| Dónde | Qué contiene | Cuándo se carga |
|---|---|---|
| `.claude/skills/code-documentation/` | Cómo documentar: método, plantillas, contrato de diseño, QA visual | Al trabajar en documentación |
| `.claude/rules/documentacion.md` | La plantilla de página y sus invariantes, desarrolladas | Al tocar `docs/**/*.md` |
| `.claude/rules/design-system.md` | Los tokens de marca y por qué el tema no se bifurca | Al tocar `src/`, `static/img/` o la configuración |
| `.claude/hooks/validar_doc.py` | Valida el documento recién escrito y le devuelve los fallos a Claude | Automático, tras cada `Write` o `Edit` |
| `scripts/build_nav.py` | `SECCIONES`: la declaración de la navegación, el mapa y `docs-map.json` | Al añadir, mover o renombrar una página |
| [`README.md`](README.md) | Empezar, organización, despliegue, comandos y qué hacer cuando Codabench cambia | A mano |
| `docs-meta/` | Cómo se montó todo y por qué cada decisión es como es | A mano, cuando haga falta el porqué |

## Lo mínimo que hay que saber

**Todo es público: el sitio y el repositorio.** Nada en el árbol que identifique a nadie: ni URLs
de instancias internas de Codabench, ni nombres de cola de ejecución de un cliente, ni correos con
dominio real (`@ejemplo.com` y `@example.com` sí), ni IPs, ni credenciales o tokens. El hook lo
comprueba al escribir y `scripts/check_docs.py` lo bloquea en CI, pero **los dos solo miran
`docs/`**: fuera de ahí —`docs-meta/`, `scripts/`, `.claude/`— no hay validación automática y el
cuidado es humano.

**`docs-meta/` no entra en el sitio, pero se lee en GitHub.** Está fuera de `docs/`, que es lo
único que Docusaurus publica; ahí va el porqué de las decisiones y los registros fechados. Que no
se publique en el sitio no lo hace privado: no escribas ahí nada que no pondrías en la portada.

**La navegación se declara, no se deduce.** El orden del sidebar, la etiqueta de cada página, los
`_category_.json`, `docs/mapa-de-la-guia.md` y `docs-map.json` salen todos de `SECCIONES`, dentro
de `scripts/build_nav.py`. Si aparece un documento que no está declarado ahí, el script **falla** y
CI con él. Es deliberado: colocar una página en el recorrido de la guía es una decisión. El orden
de las seis secciones es el orden real de montar una competición (Empezar → Competición → Recursos
→ Evaluación → Submissions → Referencia), no el alfabético.

**Publica Vercel, no Actions.** El workflow de `.github/workflows/` solo verifica lo que el build
de Vercel no ve (`check_docs.py` y `build_nav.py --check`, que son Python). Dos trampas de
despliegue —el `ignoreCommand` que solo mira el último commit contra su padre, y que `vercel.json`
no admite ni comentarios ni claves inventadas— están contadas en [`README.md`](README.md); merece
la pena leerlas antes de tocar `vercel.json` o de encadenar commits.

**El tema es copia exacta del design system y no se bifurca.** `src/css/custom.css`,
`src/components/Portada/` y `static/img/logo-mark.svg` vienen del Captia Technology Design System a
través del manual de captia.ai, sin un valor cambiado. La autoridad visual de la organización es
una sola: si un color o un radio no cuadran aquí, se arregla en el sistema, no en este repositorio.
Lo que sí cambia es el contenido, el dominio y la navegación.

**Cuando Codabench cambia, hay que revisar la guía.** Es un producto externo con su propio
calendario. Cuando publique una versión que cambie la interfaz descrita y nadie toque la guía, la
afirmación «contrastado con Codabench v1.23» pasa a ser falsa en un sitio público, y **ningún
build ni validador lo detecta**. `python scripts/check_codabench.py` compara la última release
publicada de `codalab/codabench` con la que declara este sitio y dice qué páginas dependen de qué
fuentes; `--fijar` cierra el ciclo subiendo la etiqueta. El paso del medio —contrastar pantalla a
pantalla— es de criterio y no se automatiza, y **`--fijar` nunca va antes de haberlo hecho**:
convertiría una afirmación caducada en una falsa, que es peor, porque la caducada se detecta
comparando versiones y la falsa solo la descubre un lector con la pantalla delante.

## Comandos

```bash
python scripts/check_docs.py          # invariantes de docs/ — lo mismo que corre en CI
python scripts/build_nav.py --check   # navegación declarada, mapa y docs-map — también en CI
python scripts/build_nav.py --apply   # regenera orden, categorías, mapa y docs-map
python scripts/add_frontmatter.py --apply     # title de un documento nuevo, a partir de su H1
python scripts/normalize_headings.py --apply  # un solo H1 por documento
python scripts/check_fuentes.py       # las URL externas que cita la guía siguen vivas
python scripts/check_codabench.py     # ¿sigue siendo v1.23 la versión contrastada?
python scripts/check_codabench.py --fijar   # cierre del ciclo, DESPUÉS de revisar el contenido
npm start                             # previsualización local
npm run build                         # build de producción, SIN --locale
```

Los tres que escriben en el árbol —`build_nav.py`, `add_frontmatter.py` y `normalize_headings.py`—
son idempotentes y traen el par `--apply`/`--check`; los `check_*` no escriben nada y no llevan
`--check` porque comprobar es lo único que hacen, con `check_codabench.py --fijar` como única
excepción. `check_fuentes.py` y
`check_codabench.py` salen a la red y por eso se ejecutan a mano, no en CI. Al añadir un documento
el orden es `normalize_headings.py` → `add_frontmatter.py` → declararlo en `SECCIONES` →
`build_nav.py --apply`, y el paso de en medio es a mano a propósito.

## Convenciones de la organización

El harness de este repositorio **hereda** del de `my-qa-captia-ai-app` (el manual de captia.ai), que
a su vez sigue el estándar CAPTIA que marca `captia.ai`: skills con descripción en español y
fórmula de disparo «Usar cuando se trabaje en…», agents con `name`/`description`/`model`, hooks en
Python, reglas en `.claude/rules/`. Antes de inventar algo nuevo aquí, mira cómo está resuelto
allí: dos dialectos del mismo harness en la misma organización serían un fallo de diseño.

Y las reglas de escritura, que valen igual para el sitio y para el repositorio: español correcto y
completo con todas las tildes, comentarios que explican **por qué** y no lo que ya se ve en el
código, nada de emoji en títulos ni en front matter, ficheros en LF, y ningún hecho afirmado que no
se pueda comprobar en el repositorio o en una fuente citada.
