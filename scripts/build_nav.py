#!/usr/bin/env python3
"""Fuente única de la navegación de la guía: orden, etiquetas, mapa y trazabilidad.

Qué problema resuelve
---------------------
Docusaurus ordena el sidebar por `sidebar_position` y, donde no lo hay, por nombre de
fichero. El orden de esta guía es el de montar una competición de verdad —Details →
Participation → Pages → Collaborators, y después recursos, fases y submissions—, que no se
parece en nada al alfabético: sin declararlo, `collaborators` abriría la sección de la
competición y `tasks` cerraría la de recursos, que es justo el orden en el que nada de lo
que se lee tiene sentido todavía. Y las seis carpetas aparecerían con su nombre crudo
(«competicion», «evaluacion»), sin tilde y en minúscula, porque las rutas son ASCII por
invariante.

Se podría poner un `sidebar_position` a mano en cada documento, y eso es exactamente lo que
este script existe para evitar: el orden repartido en veintiún ficheros no se puede leer de
un vistazo, nadie lo revisa entero al añadir una página, y un índice escrito a mano se queda
corto en cuanto alguien crea un documento y se olvida de listarlo.

Aquí se declara el recorrido completo, documento a documento, y de esa declaración salen:

- el `sidebar_position` (y el `sidebar_label`, cuando hace falta) del front matter,
- la `description` del front matter, sacada del rótulo `**Objetivo:**` de cada documento,
- el `_category_.json` de cada carpeta (etiqueta y posición),
- `docs/mapa-de-la-guia.md`, el índice completo, que no puede quedarse corto porque se
  genera de esta misma declaración,
- `docs-map.json`, la trazabilidad: qué parte de Codabench documenta cada página.

Reglas que respeta
------------------
- **La declaración tiene que ser exhaustiva.** Si aparece un documento sin declarar, o se
  declara uno que no existe, el script FALLA. Es la única manera de que un índice generado
  no acabe mintiendo. Es la invariante 10 del contrato del repositorio.
- **`index.md` es el índice de su carpeta** y no se lista en `docs`: Docusaurus lo sirve en
  la ruta de la carpeta y su posición la manda la `position` de la categoría. A diferencia
  de la referencia de la que sale este script, aquí `index.md` es la ÚNICA grafía admitida
  para un índice; aceptar además `carpeta/carpeta.md` abriría un agujero en la regla de
  arriba —un documento con ese nombre dejaría de necesitar declaración— y competiría con
  `index.md` por la misma URL.
- **Toda carpeta declarada tiene su `index.md`**, y su ausencia es un fallo duro. La
  referencia caía en ese caso a una página de aterrizaje `generated-index`; aquí el árbol
  del contrato da índice propio a las seis secciones, así que ese respaldo sólo serviría
  para que un `index.md` olvidado pasara sin ruido y la sección se publicara con una lista
  de tarjetas en lugar del texto puente que le toca.
- **Aquí no se fijan slugs.** La referencia transliteraba los suyos porque arrastraba rutas
  con tildes y mayúsculas heredadas. La invariante 7 del contrato prohíbe de entrada tildes
  y mayúsculas en las rutas bajo `docs/` —de eso se ocupa `scripts/check_docs.py`—, así que
  la URL que Docusaurus deriva de la ruta del fichero ya es la definitiva. Inventar aquí una
  segunda convención de URL sólo partiría el sitio en dos.
- No toca `title`: de eso se ocupa `scripts/add_frontmatter.py`.

Uso
---
    python scripts/build_nav.py --check     # no escribe; sale 1 si algo está desalineado
    python scripts/build_nav.py --apply

Idempotente: aplicar dos veces seguidas no cambia nada.
"""

from __future__ import annotations

import argparse
import io
import json
import re
import sys
from pathlib import Path

# La salida lleva rutas, etiquetas y títulos con tildes y rayas EM. En Linux —el CI— la salida
# ya es UTF-8, pero la consola de Windows arranca con la página de códigos del sistema, y ahí un
# `—` o una `→` revientan el print con UnicodeEncodeError: se pierde el informe justo cuando
# alguien intenta leer por qué ha fallado algo. Mismo remedio que en el resto de scripts.
for _flujo in (sys.stdout, sys.stderr):
    try:
        _flujo.reconfigure(encoding="utf-8")
    except (AttributeError, OSError, ValueError):
        pass

REPO = Path(__file__).resolve().parent.parent
DOCS = REPO / "docs"
MAPA = DOCS / "mapa-de-la-guia.md"
# Muy por encima del número de secciones para que el mapa quede siempre el último de la raíz,
# se añadan las secciones que se añadan.
MAPA_POSICION = 99
DOCS_MAP = REPO / "docs-map.json"

# En la raíz de `docs/` sólo viven la portada y el mapa. Cualquier otra cosa suelta ahí sería
# una página sin sección, y por tanto sin sitio en el recorrido (invariante 10).
PORTADA = "index.mdx"

# Identificador de la fuente en `docs-map.json`. Aquí el producto documentado es Codabench,
# que es EXTERNO: no hay un repositorio hermano al que apuntar, así que las `fuentes` son
# URLs de su documentación oficial en vez de rutas de fichero.
FUENTE_CODABENCH = "codabench"

# URLs que se citan más de una vez. Se nombran para que una corrección se haga en un sitio.
DOC_GETTING_STARTED = (
    "https://docs.codabench.org/latest/Organizers/Benchmark_Creation/"
    "Getting-started-with-Codabench/"
)
DOC_FORMULARIO = (
    "https://docs.codabench.org/latest/Organizers/Benchmark_Creation/"
    "Competition-Creation-Form/"
)
DOC_RECURSOS = (
    "https://docs.codabench.org/v1.31.2/Organizers/Running_a_benchmark/Resource-Management/"
)
DOC_RAIZ = "https://docs.codabench.org/"
# Tutorial de la comunidad, no documentación oficial. Se cita porque la guía lo cita: es la
# referencia más concreta que hay sobre cómo se empaqueta un bundle de submission.
TUTORIAL_PAVAO = "https://adrienpavao.com/blog/codabench-tuto/codabench-tuto.html"

RE_FM = re.compile(r"\A---\s*\n(?P<fm>.*?)\n---\s*\n", re.S)
RE_POS = re.compile(r"^sidebar_position:.*$", re.M)
RE_LABEL = re.compile(r"^sidebar_label:.*$", re.M)
RE_DESC = re.compile(r"^description:.*$", re.M)
RE_TITLE = re.compile(r'^title:\s*"?(?P<t>.*?)"?\s*$', re.M)
# El rótulo del contrato es `**Objetivo:**`, en negrita y como primera línea del cuerpo.
RE_OBJETIVO = re.compile(r"^\*\*Objetivo:\*\*\s*(?P<t>.+?)\s*$", re.M)
# Marcas de Markdown que no deben viajar a una descripción: negrita, cursiva, código y enlaces.
RE_MD_ENLACE = re.compile(r"\[([^\]]+)\]\([^)]+\)")
RE_MD_MARCAS = re.compile(r"[*_`]+")

# ---------------------------------------------------------------------------
# LA DECLARACIÓN. Es el recorrido de montar una competición, no el orden alfabético.
#
# Cada sección: carpeta, etiqueta, documentos en orden y, si algún día hiciera falta,
# subcarpetas en orden. Los documentos se nombran sin extensión; el `index.md` de la carpeta
# NO se lista, porque su posición la manda la categoría.
#
# Un documento se declara de dos maneras:
#
#   "details"                 -> usa su `title` como etiqueta del sidebar
#   ["formato", "Formato"]    -> usa esa etiqueta corta en el sidebar
#
# La segunda forma es para los títulos que repiten el contexto que el sidebar ya da: dentro
# de la categoría «Submissions», «Formato de submission» gasta media línea en decirle al
# lector dónde está. El `title` no se toca —es lo que se ve en la pestaña del navegador, en
# las migas y en el buscador, donde ese contexto sí hace falta—; lo que cambia es el
# `sidebar_label`, y sale de aquí para que nadie tenga que mantenerlo documento a documento.
#
# `fuentes` completa la declaración con la TRAZABILIDAD. En la referencia de la que sale este
# script eran rutas del repositorio de la aplicación documentada. Codabench no es nuestro: la
# fuente contrastable de cada sección es la página de la documentación oficial en la que se
# apoya. De ahí sale `docs-map.json`, que responde a la pregunta que aparece cada vez que
# Codabench toca su interfaz o su documentación: ¿qué páginas de la guía hay que revisar?
# Una subcarpeta hereda las fuentes de su sección salvo que declare las suyas.
# ---------------------------------------------------------------------------

SECCIONES = [
    {
        "carpeta": "empezar",
        "label": "Antes de empezar",
        "fuentes": [DOC_GETTING_STARTED],
        "docs": [
            "conceptos",
            "requisitos",
        ],
    },
    {
        "carpeta": "competicion",
        "label": "Crear la competición",
        # Las cuatro páginas describen pestañas del formulario de creación, que es
        # exactamente lo que documenta esta página oficial.
        "fuentes": [DOC_FORMULARIO],
        # El orden es el de las pestañas del formulario, no el alfabético.
        "docs": [
            "details",
            "participation",
            "pages",
            "collaborators",
        ],
    },
    {
        "carpeta": "recursos",
        "label": "Recursos y tasks",
        "fuentes": [DOC_RECURSOS],
        "docs": [
            "datasets-programs",
            "tasks",
        ],
    },
    {
        "carpeta": "evaluacion",
        "label": "Fases y evaluación",
        # Las fases se declaran en el formulario de creación, pero lo que se ejecuta en cada
        # una son los programas y las tasks del gestor de recursos: hay que mirar las dos.
        "fuentes": [DOC_FORMULARIO, DOC_RECURSOS],
        "docs": [
            "phases",
            "leaderboards",
            "submission-rule",
        ],
    },
    {
        "carpeta": "submissions",
        "label": "Submissions",
        "fuentes": [DOC_RECURSOS, TUTORIAL_PAVAO],
        "docs": [
            # «Formato de submission», dentro de la categoría «Submissions», repite la
            # palabra que ya está en el encabezado de la categoría.
            ["formato", "Formato"],
            "probar",
        ],
    },
    {
        "carpeta": "referencia",
        "label": "Referencia",
        # Sección transversal: ni los errores ni las fuentes salen de una página concreta de
        # la documentación, sino del conjunto.
        "fuentes": [DOC_RAIZ],
        "docs": [
            "troubleshooting",
            # El título completo es «Fuentes y documentación oficial»; en el sidebar, dentro
            # de «Referencia», la primera palabra ya lo dice todo.
            ["fuentes", "Fuentes"],
        ],
    },
]


# ---------------------------------------------------------------------------


def leer(p: Path) -> str:
    return io.open(p, encoding="utf-8").read()


def escribir(p: Path, s: str) -> None:
    # `newline="\n"` a propósito: esto se ejecuta en Windows, pero el CI y el build corren en
    # Linux. Sin ello cada regeneración metería CRLF, `--check` fallaría por finales de línea
    # y el diff sería ruido que no corresponde a ningún cambio real (ver `.gitattributes`).
    io.open(p, "w", encoding="utf-8", newline="\n").write(s)


def es_indice(doc: Path) -> bool:
    """`index.md`, y sólo eso: es la única grafía de índice que admite este repositorio."""
    return doc.name == "index.md"


def titulo_de(p: Path) -> str:
    m = RE_TITLE.search(leer(p))
    return m.group("t").strip() if m else p.stem


def declaracion(entrada) -> tuple[str, str | None]:
    """Normaliza `"stem"` o `["stem", "Etiqueta"]` a la tupla (stem, etiqueta o None)."""
    if isinstance(entrada, str):
        return entrada, None
    return entrada[0], entrada[1]


def frontmatter_de(p: Path) -> str:
    m = RE_FM.match(leer(p))
    if not m:
        raise SystemExit(f"{p} no tiene front matter; pasa antes add_frontmatter.py")
    return m.group("fm")


def descripcion_de(p: Path) -> str | None:
    """La frase del «Objetivo», limpia de Markdown, para el front matter.

    Sin ella, Docusaurus compone la descripción de cada página —la que sale en la etiqueta
    `<meta name="description">`, en las tarjetas y en los resultados de búsqueda— cogiendo el
    principio del contenido. Y el contenido empieza literalmente por «**Objetivo:** …», de
    modo que ese rótulo acabaría repetido en cada tarjeta.
    """
    m = RE_OBJETIVO.search(leer(p))
    if not m:
        return None
    texto = RE_MD_ENLACE.sub(r"\1", m.group("t"))
    texto = RE_MD_MARCAS.sub("", texto).strip()
    return capitalizar_inicial(resumir(texto)) or None


def capitalizar_inicial(texto: str) -> str:
    """La descripción arranca en mayúscula aunque el objetivo empiece en minúscula.

    En el cuerpo del documento, «**Objetivo:** subir a Codabench los datos…» está bien
    escrito: la frase va detrás de un rótulo y de dos puntos. Pero la `description` viaja
    SOLA —a la etiqueta `<meta>`, a la tarjeta de la sección, al resultado de búsqueda— y
    ahí ese mismo texto abre una frase en minúscula. Las dos formas de redactar el objetivo
    conviven hoy en la guía, así que el generador las unifica en la COPIA en vez de obligar
    a repasar los veintiún objetivos y a mantener esa convención a mano.

    Toca el primer carácter y sólo si es una letra minúscula; el texto del documento no se
    toca nunca. La única víctima posible sería un objetivo que empezara por un identificador
    en minúscula a propósito, que en prosa en español no se da: los objetivos empiezan por
    un verbo en infinitivo.
    """
    return texto[:1].upper() + texto[1:] if texto[:1].islower() else texto


# Red de seguridad, no objetivo: una frase que pase de aquí es casi seguro un párrafo mal
# puntuado. El corte normal es la frase, no el contador.
TOPE_DESC = 300


def resumir(texto: str) -> str:
    """La PRIMERA FRASE del objetivo, que es lo que cabe en una tarjeta y en un `<meta>`.

    El objetivo del documento NO se toca: puede necesitar dos frases para dejar clara una
    distinción que el lector necesita, y recortarlo ahí sería perder información. Lo que se
    acorta es la copia que va al front matter, porque ese texto tiene otro trabajo: resumir.

    Se corta por frase y no por número de caracteres a propósito. Un corte por contador deja
    finales como «...el programa de evaluación que la», que es peor que una frase larga: la
    descripción se lee entera en la tarjeta de sección, donde no hay nada que la complete.
    """
    # Frase = punto, cierre o exclamación + espacio + mayúscula. Así no parte «v1.23» ni «p. ej.».
    corte = re.search(r"(?<=[.!?])\s+(?=[A-ZÁÉÍÓÚÑ¿¡])", texto)
    frase = texto[: corte.start()].strip() if corte else texto
    if len(frase) <= TOPE_DESC:
        return frase
    recorte = frase[: TOPE_DESC - 1]
    if " " in recorte:
        recorte = recorte[: recorte.rindex(" ")]
    return recorte.rstrip(" ,;:—-") + "…"


def linea_desc(desc: str) -> str:
    """`description` en YAML, con las comillas escapadas."""
    return 'description: "' + desc.replace("\\", "\\\\").replace('"', '\\"') + '"'


def alineado(p: Path, pos: int, label: str | None) -> bool:
    """¿El front matter ya dice lo que la declaración pide?"""
    fm = frontmatter_de(p)
    m = RE_POS.search(fm)
    if not m or m.group(0) != f"sidebar_position: {pos}":
        return False
    actual = RE_LABEL.search(fm)
    if label is None:
        if actual is not None:
            return False
    elif actual is None or actual.group(0) != f'sidebar_label: "{label}"':
        return False
    return descripcion_alineada(p)


def descripcion_alineada(p: Path) -> bool:
    """¿La `description` del front matter coincide con el objetivo del documento?"""
    desc = descripcion_de(p)
    actual = RE_DESC.search(frontmatter_de(p))
    if desc is None:
        return actual is None
    return actual is not None and actual.group(0) == linea_desc(desc)


def con_descripcion(p: Path, fm: str) -> str:
    """Devuelve el front matter con la `description` puesta al día (o retirada)."""
    desc = descripcion_de(p)
    if desc is None:
        return "\n".join(l for l in fm.splitlines() if not RE_DESC.match(l))
    linea = linea_desc(desc)
    if RE_DESC.search(fm):
        return RE_DESC.sub(lambda _: linea, fm, count=1)
    lineas = fm.splitlines()
    i = next((n for n, l in enumerate(lineas) if l.startswith("title:")), -1)
    lineas.insert(i + 1, linea)
    return "\n".join(lineas)


def fijar_frontmatter(p: Path, pos: int, label: str | None) -> None:
    """Escribe `sidebar_position`, `sidebar_label` y `description` según la declaración.

    Si la declaración no trae etiqueta, se RETIRA la que hubiera: el sidebar se gobierna
    desde aquí, y una etiqueta suelta en un documento sería una segunda fuente de verdad.
    """
    texto = leer(p)
    m = RE_FM.match(texto)
    fm = frontmatter_de(p)
    fm2 = fm

    nueva = f"sidebar_position: {pos}"
    if RE_POS.search(fm2):
        fm2 = RE_POS.sub(nueva, fm2, count=1)
    else:
        fm2 = fm2 + "\n" + nueva

    if label is None:
        fm2 = "\n".join(l for l in fm2.splitlines() if not RE_LABEL.match(l))
    else:
        linea = f'sidebar_label: "{label}"'
        if RE_LABEL.search(fm2):
            fm2 = RE_LABEL.sub(linea, fm2, count=1)
        else:
            # Detrás de `title`, que es la primera clave por convención.
            lineas = fm2.splitlines()
            i = next((n for n, l in enumerate(lineas) if l.startswith("title:")), -1)
            lineas.insert(i + 1, linea)
            fm2 = "\n".join(lineas)

    fm2 = con_descripcion(p, fm2)

    if fm2 != fm:
        escribir(p, texto[: m.start("fm")] + fm2 + texto[m.end("fm") :])


def fijar_descripcion(p: Path) -> None:
    """Pone al día sólo la `description`. Es lo que necesita un `index.md`, que no lleva
    posición propia."""
    texto = leer(p)
    m = RE_FM.match(texto)
    fm = frontmatter_de(p)
    fm2 = con_descripcion(p, fm)
    if fm2 != fm:
        escribir(p, texto[: m.start("fm")] + fm2 + texto[m.end("fm") :])


def recorrer(
    nodo: dict,
    base: Path,
    posicion: int,
    salida: list,
    errores: list,
    nivel: int,
    fuentes_heredadas: list[str] | None = None,
    mapa_fuentes: dict | None = None,
):
    """Valida y aplana una sección. `salida` recibe (acción, ...) para escribir después."""
    fuentes = nodo.get("fuentes") or fuentes_heredadas or []
    carpeta = base / nodo["carpeta"]
    # Los mensajes de fallo llevan siempre la ruta desde la raíz del repositorio, para que se
    # puedan copiar y pegar tal cual en un editor o en un `git add`.
    rel = "docs/" + carpeta.relative_to(DOCS).as_posix()
    if not carpeta.is_dir():
        errores.append(f"declarada una carpeta que no existe: {rel}")
        return

    reales = sorted(carpeta.glob("*.md"))
    indices = [p for p in reales if es_indice(p)]
    ordinarios = [p for p in reales if p not in indices]

    # El único `.mdx` del sitio es la portada, que lleva componentes de React. Dentro de una
    # sección un `.mdx` se publicaría igual, pero este script no lo vería: se quedaría sin
    # posición y sin descripción, que es justo lo que hay que impedir.
    for p in sorted(carpeta.glob("*.mdx")):
        errores.append(f"{rel}/{p.name} es .mdx; en las secciones sólo hay .md")

    if not indices:
        errores.append(f"{rel}/index.md no existe y toda sección necesita su índice")

    declarados_full = [declaracion(d) for d in nodo.get("docs", [])]
    declarados = [d for d, _ in declarados_full]
    sobran = [p.stem for p in ordinarios if p.stem not in declarados]
    faltan = [d for d in declarados if not (carpeta / f"{d}.md").is_file()]
    for s in sobran:
        errores.append(f"{rel}/{s}.md existe y NO está declarado en build_nav.py")
    for f in faltan:
        errores.append(f"{rel}/{f}.md está declarado y NO existe")

    subs = nodo.get("subsecciones", [])
    subcarpetas_reales = sorted(d.name for d in carpeta.iterdir() if d.is_dir())
    declaradas = [s["carpeta"] for s in subs]
    for d in subcarpetas_reales:
        if d not in declaradas:
            errores.append(f"{rel}/{d}/ existe y NO está declarada en build_nav.py")

    # `_category_.json` de esta carpeta: etiqueta y posición, nada más. La página de
    # aterrizaje es siempre el `index.md`, cuya existencia se ha comprobado arriba.
    salida.append(("categoria", carpeta, {"label": nodo["label"], "position": posicion}))

    # Trazabilidad: todo documento de esta carpeta (índice incluido) hereda sus fuentes.
    if mapa_fuentes is not None and fuentes:
        for p in reales:
            mapa_fuentes[p.relative_to(REPO).as_posix()] = fuentes

    # El índice no lleva posición propia (manda la de su categoría), pero su `description`
    # hay que ponerla igual: sin ella, su `<meta>` y su tarjeta mostrarían el rótulo
    # «Objetivo:» en crudo.
    for p in indices:
        salida.append(("descripcion", p, None))

    # Posiciones y etiquetas de los documentos, y después las subcarpetas.
    n = 0
    for stem, label in declarados_full:
        n += 1
        salida.append(("posicion", carpeta / f"{stem}.md", (n, label)))
    for sub in subs:
        n += 1
        recorrer(sub, carpeta, n, salida, errores, nivel + 1, fuentes, mapa_fuentes)


def construir_docs_map(mapa_fuentes: dict) -> str:
    """`docs-map.json`: qué parte de Codabench documenta cada página de la guía.

    Responde a la pregunta que aparece cada vez que Codabench cambia: si se ha tocado el
    formulario de creación, ¿qué páginas hay que revisar? El formato es el del paquete
    `code-documentation` (esquema 1), con una diferencia que conviene tener presente al
    leerlo: los `paths` son URLs de documentación, no rutas de fichero, porque el producto
    documentado es externo y su código no está ni en este repositorio ni al lado. Eso quita
    la posibilidad de comprobar automáticamente que la fuente sigue existiendo: una URL se
    mueve sin avisar y sólo se nota al abrirla.
    """
    datos = {
        "schema_version": 1,
        "_generado_por": "scripts/build_nav.py — no editar a mano",
        "_fuentes": {
            FUENTE_CODABENCH: {
                "producto": "Codabench",
                "documentacion": DOC_RAIZ,
                # El valor va escrito aquí como literal, en una sola línea y con esta forma
                # exacta, porque `scripts/check_codabench.py --fijar` lo localiza y le
                # sustituye el número al comprobar la última release publicada. Sacarlo a
                # una constante lo escondería de esa sustitución.
                "revision_contrastada": "v1.31.2",
                "nota": (
                    "«revision_contrastada» sale de la etiqueta de versión que llevan las "
                    "URLs de la documentación citadas por la guía, NO de una comprobación "
                    "contra una instancia de Codabench en marcha. Los «paths» son URLs de "
                    "documentación, no rutas de fichero: el producto documentado es externo. "
                    "Una de ellas es un tutorial de la comunidad, no documentación oficial."
                ),
            }
        },
        "documents": [
            {"doc": doc, "sources": [{"id": FUENTE_CODABENCH, "paths": paths}]}
            for doc, paths in sorted(mapa_fuentes.items())
        ],
    }
    return json.dumps(datos, ensure_ascii=False, indent=2) + "\n"


# El objetivo del mapa se declara aquí porque la página es generada: es la única de la guía
# cuyo texto no escribe una persona en su `.md`.
# En minúscula, como el resto de la guía: el rótulo y la frase se leen como una sola oración
# («Objetivo: reunir en una sola página…»). La `description` del front matter sí va
# capitalizada, y de eso se encarga `capitalizar_inicial()` unas líneas más abajo.
OBJETIVO_MAPA = (
    "reunir en una sola página todos los documentos de la guía, agrupados por sección y en "
    "el mismo orden en que los presenta la navegación lateral."
)


def construir_mapa() -> str:
    """El índice completo, generado. Cada sección con su recuento real."""
    lineas = [
        "---",
        'title: "Mapa de la guía"',
        # La `description` va escrita aquí y no la deduce nadie después: el resto de páginas
        # la recibe de `fijar_frontmatter`, pero el mapa no está en `SECCIONES` —no es una
        # página de sección— y sin esta línea Docusaurus le pondría como `<meta>` el rótulo
        # «**Objetivo:**» de más abajo.
        linea_desc(capitalizar_inicial(resumir(OBJETIVO_MAPA))),
        f"sidebar_position: {MAPA_POSICION}",
        "---",
        "",
        "# Mapa de la guía",
        "",
        f"**Objetivo:** {OBJETIVO_MAPA}",
        "",
        ":::note[Página generada]",
        "Esta página la genera `scripts/build_nav.py` a partir de la declaración `SECCIONES` "
        "y del árbol de `docs/`. No se edita a mano: cualquier cambio se pierde al "
        "regenerarla, y si se queda desalineada la comprobación de CI falla.",
        ":::",
        "",
    ]

    def bloque(nodo: dict, base: Path, nivel: int):
        carpeta = base / nodo["carpeta"]
        indices = [p for p in sorted(carpeta.glob("*.md")) if es_indice(p)]
        total = len(list(carpeta.rglob("*.md")))
        # El encabezado va SIEMPRE en texto plano y la página índice entra como primer
        # elemento de la lista. Enlazar el encabezado parecía natural, pero deja el título de
        # la sección con el mismo aspecto que sus páginas y el mapa se lee peor.
        encabezado = "#" * min(nivel + 1, 4)
        lineas.append(f"{encabezado} {nodo['label']}")
        lineas.append("")
        plural = "página" if total == 1 else "páginas"
        lineas.append(f"*{total} {plural}.*")
        lineas.append("")
        for idx in indices:
            destino = "./" + idx.relative_to(DOCS).as_posix()
            lineas.append(f"- [{titulo_de(idx)}]({destino})")
        # El mapa usa el `title` completo, no la etiqueta corta del sidebar: aquí no hay una
        # categoría alrededor que dé contexto, así que el título largo sí distingue.
        for entrada in nodo.get("docs", []):
            stem, _ = declaracion(entrada)
            p = carpeta / f"{stem}.md"
            destino = "./" + p.relative_to(DOCS).as_posix()
            lineas.append(f"- [{titulo_de(p)}]({destino})")
        if indices or nodo.get("docs"):
            lineas.append("")
        for sub in nodo.get("subsecciones", []):
            bloque(sub, carpeta, nivel + 1)

    for seccion in SECCIONES:
        bloque(seccion, DOCS, 1)

    return "\n".join(lineas).rstrip() + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    salida: list = []
    errores: list[str] = []
    mapa_fuentes: dict[str, list[str]] = {}
    for i, seccion in enumerate(SECCIONES, start=1):
        recorrer(seccion, DOCS, i, salida, errores, 1, None, mapa_fuentes)

    # Carpetas sueltas en la raíz de `docs/`: una carpeta sin declarar se publicaría entera,
    # con su nombre crudo por etiqueta y en orden alfabético, que es el defecto que este
    # script existe para impedir.
    declaradas_raiz = {s["carpeta"] for s in SECCIONES}
    for d in sorted(p.name for p in DOCS.iterdir() if p.is_dir()):
        if d not in declaradas_raiz:
            errores.append(f"docs/{d}/ existe y NO está declarada en build_nav.py")

    # Documentos sueltos en la raíz de `docs/`: la portada y el mapa, nada más.
    permitidos = {PORTADA, MAPA.name}
    for p in sorted(DOCS.glob("*.md")) + sorted(DOCS.glob("*.mdx")):
        if p.name not in permitidos:
            errores.append(f"docs/{p.name} está en la raíz y no es ni la portada ni el mapa")

    if errores:
        for e in errores:
            print(f"FALLO  {e}")
        return 1

    mapa = construir_mapa()
    pendientes = []
    for accion, destino, dato in salida:
        if accion == "categoria":
            actual = destino / "_category_.json"
            nuevo = json.dumps(dato, ensure_ascii=False, indent=2) + "\n"
            if not actual.is_file() or leer(actual) != nuevo:
                pendientes.append(("categoria", actual, nuevo))
        elif accion == "descripcion":
            if not descripcion_alineada(destino):
                pendientes.append(("descripcion", destino, None))
        else:
            pos, label = dato
            if not alineado(destino, pos, label):
                # `alineado()` comprueba posición, etiqueta Y descripción. Etiquetarlo todo
                # como "posicion" mandaría a mirar el campo equivocado cuando lo que ha
                # cambiado es el «Objetivo:» de la página.
                motivo = "posicion" if descripcion_alineada(destino) else "descripcion"
                pendientes.append((motivo, destino, dato))
    if not MAPA.is_file() or leer(MAPA) != mapa:
        pendientes.append(("mapa", MAPA, mapa))

    docs_map = construir_docs_map(mapa_fuentes)
    if not DOCS_MAP.is_file() or leer(DOCS_MAP) != docs_map:
        pendientes.append(("trazabilidad", DOCS_MAP, docs_map))

    print(f"secciones declaradas : {len(SECCIONES)}")
    print(f"documentos ordenados : {sum(1 for a, _, _ in salida if a == 'posicion')}")
    print(f"categorias           : {sum(1 for a, _, _ in salida if a == 'categoria')}")
    print(f"docs con trazabilidad: {len(mapa_fuentes)}")
    print(f"descripciones        : {sum(1 for a, _, _ in salida if a == 'descripcion')} índices"
          f" + {sum(1 for a, _, _ in salida if a == 'posicion')} documentos")
    print(f"pendientes de escribir: {len(pendientes)}")

    if not args.apply:
        for accion, destino, _ in pendientes[:12]:
            print(f"  {accion:<12} {destino.relative_to(REPO).as_posix()}")
        if len(pendientes) > 12:
            print(f"  ... y {len(pendientes) - 12} más")
        return 1 if (args.check and pendientes) else 0

    for accion, destino, dato in pendientes:
        if accion == "posicion":
            fijar_frontmatter(destino, dato[0], dato[1])
        elif accion == "descripcion":
            # Un documento ordinario llega aquí con su (posición, etiqueta); un `index.md`,
            # con `None`, porque su sitio en el sidebar lo manda el `_category_.json`.
            if dato is None:
                fijar_descripcion(destino)
            else:
                fijar_frontmatter(destino, dato[0], dato[1])
        else:
            escribir(destino, dato)
    print(f"escritos: {len(pendientes)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
