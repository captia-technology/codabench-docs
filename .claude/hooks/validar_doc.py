#!/usr/bin/env python3
"""Valida UN documento de `docs/` justo después de escribirlo.

Por qué es un PostToolUse y no un PreToolUse
--------------------------------------------
El contenido solo se puede comprobar cuando ya está escrito. Y en `PostToolUse` el código de
salida 2 NO bloquea la herramienta —el fichero ya se escribió— pero SÍ hace llegar el stderr a
Claude, que es la única vía para que un hook posterior le diga algo al modelo. Así que:

    exit 0  -> todo bien, silencio
    exit 2  -> hay incumplimientos; el stderr se los cuenta a Claude para que los arregle

Por qué no ejecuta `scripts/check_docs.py`
------------------------------------------
Ese recorre todos los documentos, resuelve cada enlace contra el sistema de ficheros y compara
el árbol entero. Un hook que corre en CADA escritura tiene que ser instantáneo, así que aquí
solo se valida el fichero tocado y solo con comprobaciones locales —las que no necesitan mirar
otros documentos—. La comprobación completa sigue corriendo en CI
(`.github/workflows/docs-ci.yml`).

Las invariantes son las mismas que las de `scripts/check_docs.py` y las de
`.claude/rules/documentacion.md` —una lista, tres implementaciones: si cambia una, cambian las
tres—, y aquí se comprueban todas las que se pueden decidir mirando un solo fichero: 1, 2, 3,
4 (sintaxis y origen de la imagen; que el fichero exista lo resuelve `check_docs.py`), 6, 7 y 8.

Quedan fuera, y sólo estas cuatro:

- la 5 (los enlaces resuelven) y la 9 (ninguna imagen huérfana), que se contestan contra el
  árbol entero y no contra el documento que se acaba de escribir,
- la 10 (todo documento declarado), que la comprueba `scripts/build_nav.py --check`, que es
  quien tiene la declaración delante,
- la 11 (el rótulo `**Objetivo:**`), que es un AVISO: este hook sólo tiene exit 2 —bloqueante—
  o silencio, así que reportarla aquí la convertiría en un fallo. La avisa `check_docs.py`.

Entrada: el JSON del evento por stdin. Salida: mensajes en stderr.
"""

from __future__ import annotations

import io
import json
import re
import sys
import unicodedata
from pathlib import Path

# Los incumplimientos se escriben en español, con tildes, comillas angulares y rayas, y su ÚNICO
# lector es Claude, que recibe este stderr tal cual. En Linux ya sale UTF-8, pero en Windows
# —donde se escribe la documentación— Python usa la página de códigos del sistema: en cp1252 la
# `ñ` viaja como un byte suelto que no es UTF-8 válido, así que el mensaje llega roto o no llega,
# justo cuando su trabajo es explicar qué hay que corregir. Mismo remedio, y por lo mismo, que
# `scripts/check_docs.py`.
for _flujo in (sys.stdout, sys.stderr):
    try:
        _flujo.reconfigure(encoding="utf-8")
    except (AttributeError, OSError, ValueError):
        pass

# El repositorio y su `docs/`, resueltos desde la posición de ESTE fichero, exactamente igual
# que `scripts/check_docs.py` (`REPO = Path(__file__).resolve().parent.parent`). Las dos
# implementaciones de la invariante 7 tienen que estar de acuerdo en QUÉ carpeta es `docs/`,
# o comprueban cosas distintas.
REPO = Path(__file__).resolve().parent.parent.parent
DOCS = REPO / "docs"

RE_H1 = re.compile(r"^# (?!#)", re.MULTILINE)
RE_H1_TEXTO = re.compile(r"^#\s+(?P<t>.+?)\s*$", re.MULTILINE)
RE_FM = re.compile(r"\A---\s*\n")
RE_FM_BLOQUE = re.compile(r"\A---\s*\n(?P<fm>.*?)\n---\s*\n", re.S)
RE_FM_TITLE = re.compile(r'^title:\s*"?(?P<t>.*?)"?\s*$', re.M)
RE_HTML_IMG = re.compile(r"<img[^>]*>")
RE_MD_IMG = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
RE_EMOJI = re.compile("[\U0001f300-\U0001faff☀-➿️‍⏱⏲⌛⌚]+")
RE_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
RE_IP = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
# Credenciales. El repositorio es público y esta guía habla de subir recursos a una plataforma: un
# token pegado en un ejemplo se publica igual que el resto del texto.
RE_SECRETO = re.compile(
    r"(?:api[_-]?key|secret|password|passwd|authorization)\s*[:=]\s*\S+"
    r"|Bearer\s+[A-Za-z0-9._~+/-]{16,}",
    re.I,
)
DOMINIOS_DEMO = ("ejemplo.com", "example.com")


def es_demo(correo: str) -> bool:
    """¿El correo pertenece a un dominio de ejemplo? Se compara el DOMINIO, no el sufijo.

    Con `endswith` sobre el correo entero, `alguien@malejemplo.com` pasaba por demo. Mismo
    criterio, letra por letra, que `scripts/check_docs.py`.
    """
    dominio = correo.rsplit("@", 1)[-1].lower().rstrip(".")
    return any(dominio == d or dominio.endswith("." + d) for d in DOMINIOS_DEMO)
# La documentación oficial de Codabench y la propia plataforma usan estas direcciones en los
# ejemplos de despliegue local: no son datos de nadie.
IPS_DOC = {"127.0.0.1", "0.0.0.0"}
# Última pieza de la invariante 8: las URLs de instancias internas. Codabench también se
# despliega on-premise, así que una URL cuyo HOST contiene «codabench» y no es uno de estos
# tres apunta a la instancia de alguien —normalmente la del equipo, con su competición aún sin
# publicar— y no a documentación pública. El host se compara entero: `github.com/…/codabench`
# no entra, porque ahí «codabench» va en la ruta.
RE_URL_CODABENCH = re.compile(r"https?://([A-Za-z0-9.-]*codabench[A-Za-z0-9.-]*)", re.I)
HOSTS_CODABENCH = {"codabench.org", "www.codabench.org", "docs.codabench.org"}


def privados() -> list[str]:
    """Identificadores que no deben publicarse, si el equipo mantiene la lista.

    `scripts/privados.txt` no se versiona (ver `.gitignore`): el repositorio es privado pero el
    sitio no, y una lista de nombres de cliente dentro del repo sería justo el dato que se
    quiere proteger. Una línea por identificador; `#` comenta.
    """
    p = REPO / "scripts" / "privados.txt"
    if not p.is_file():
        return []
    fuera = []
    for linea in io.open(p, encoding="utf-8").read().splitlines():
        linea = linea.split("#", 1)[0].strip()
        if linea:
            fuera.append(linea)
    return fuera


def columnas(linea: str) -> int:
    """Celdas que Markdown ve en una fila de tabla.

    Copiada literalmente de `scripts/check_docs.py`. No la toques aquí sin tocarla allí: la
    invariante 6 se comprueba en los dos sitios y con el mismo criterio, o un documento pasaría
    el hook y caería en CI.

    El pipe escapado (`\\|`) NO separa; el que va dentro de `código` SÍ separa, que es justo lo
    que rompe las tablas sin avisar.
    """
    s = linea.strip().replace("\\|", "\x00")
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return len(s.split("|"))


def filas_descuadradas(texto: str) -> list[tuple[int, int, int, str]]:
    """Filas de tabla cuyo número de celdas no coincide con el de su cabecera.

    También copiada de `scripts/check_docs.py`, y por el mismo motivo.
    """
    malas: list[tuple[int, int, int, str]] = []
    lineas = texto.split("\n")
    i = 0
    while i < len(lineas):
        if not lineas[i].lstrip().startswith("|"):
            i += 1
            continue
        j = i
        while j < len(lineas) and lineas[j].lstrip().startswith("|"):
            j += 1
        bloque = lineas[i:j]
        if len(bloque) >= 2:
            base = columnas(bloque[0])
            for k, l in enumerate(bloque[1:], start=1):
                n = columnas(l)
                if n != base:
                    malas.append((i + k + 1, base, n, l.strip()))
        i = j
    return malas


def main() -> int:
    try:
        evento = json.load(sys.stdin)
    except Exception:
        return 0  # sin evento legible no hay nada que validar; nunca estorbar

    ruta = (evento.get("tool_input") or {}).get("file_path") or ""
    if not ruta:
        return 0

    p = Path(ruta)
    if p.suffix.lower() not in (".md", ".mdx") or not p.is_file():
        return 0

    # Qué tramos de la ruta entran en la invariante 7: los que cuelgan de `docs/`. Cuál es ese
    # `docs/` no es evidente aquí. `check_docs.py` parte de `REPO/docs` y no tiene el problema;
    # a este hook le llega una ruta absoluta desde el evento, y quedarse con el PRIMER tramo
    # llamado «docs» falla en cuanto el clon vive debajo de una carpeta que también se llama así
    # —`~/docs/Codabench-Docs/docs/empezar/index.md`—: se acabaría juzgando el nombre del clon,
    # que no es asunto de esta invariante, y el hook bloquearía en esa máquina y en ninguna otra.
    # Por eso se ancla en el `docs/` de ESTE repositorio, y solo si el fichero no cuelga de él
    # —otra copia del árbol, una prueba fuera del repositorio— se recurre al ÚLTIMO tramo «docs».
    try:
        tramos = p.resolve().relative_to(DOCS).parts
    except ValueError:
        partes = [x.lower() for x in p.parts]
        if "docs" not in partes:
            return 0
        tramos = p.parts[len(partes) - partes[::-1].index("docs"):]

    try:
        texto = io.open(p, encoding="utf-8").read()
    except Exception:
        return 0

    fallos: list[str] = []

    # 1 — front matter: presente, cerrado y con `title`.
    #
    # No basta con el `---` de apertura: un bloque sin cerrar deja de ser front matter y
    # Docusaurus publica el YAML como texto de la página. Y un bloque sin `title` deja el
    # título en manos de Docusaurus (lo deduce del H1 o del nombre del fichero), que es justo
    # lo que la invariante 3 impide que diverja.
    bloque = RE_FM_BLOQUE.match(texto)
    if not RE_FM.match(texto):
        fallos.append("sin front matter: hace falta al menos `title`")
    elif not bloque:
        fallos.append(
            "front matter abierto y sin cerrar con `---`: lo que va debajo se publica como "
            "texto de la página"
        )
    elif not RE_FM_TITLE.search(bloque.group("fm")):
        fallos.append(
            "el front matter no declara `title`: es lo que se ve en la pestaña, en las migas "
            "y en el buscador"
        )

    # 2 — un solo H1.
    n_h1 = len(RE_H1.findall(texto))
    if n_h1 == 0 and p.suffix.lower() == ".md":
        fallos.append(
            "sin encabezado H1: la invariante pide UNO, no «como mucho uno». Sin él "
            "Docusaurus pinta el `title` del front matter y la página parece correcta, pero "
            "el cotejo `title` == H1 se queda sin nada que comparar"
        )
    if n_h1 > 1:
        fallos.append(
            f"{n_h1} encabezados H1. Solo el título va en `#`; las secciones en `##`, o no "
            "aparecerán en el índice lateral (arranca en H2)"
        )

    # 3 — el `title` del front matter dice lo mismo que el H1, y sin emoji.
    if bloque:
        mt = RE_FM_TITLE.search(bloque.group("fm"))
        mh = RE_H1_TEXTO.search(texto[bloque.end():])
        if mt and mh:
            h1 = RE_EMOJI.sub("", mh.group("t")).strip().strip("–-—").strip()
            if mt.group("t").strip() != h1:
                fallos.append(
                    f"el `title` del front matter no coincide con el H1 -> "
                    f"title={mt.group('t')!r} vs H1={h1!r}. El `title` es lo que se ve en la "
                    "pestaña, en las migas y en el buscador; el H1, lo que se lee en la página"
                )
        # El emoji se comprueba aparte del cotejo: si el H1 lleva el mismo emoji que el
        # `title`, los dos textos «coinciden» —el H1 se compara ya sin emoji— y el emoji se
        # colaría hasta la pestaña y los metadatos, donde no aporta nada.
        if mt and RE_EMOJI.search(mt.group("t")):
            fallos.append(
                f"el `title` del front matter lleva emoji -> {mt.group('t')!r}. Acaba en la "
                "pestaña y en los metadatos del buscador"
            )

    # 4 — imágenes.
    if "user-attachments" in texto:
        fallos.append(
            "referencia a github.com/user-attachments: son URLs efímeras que exigen "
            "autenticación. Co-ubica la imagen junto al .md"
        )
    for tag in RE_HTML_IMG.findall(texto):
        fallos.append(
            f"`<img>` en crudo ({tag[:48]}…): Docusaurus no resuelve esa ruta y la imagen "
            "queda rota en producción. Usa `![alt](./fichero.png)`"
        )
    for ref in RE_MD_IMG.findall(texto):
        if ref.startswith(("http://", "https://")):
            fallos.append(
                f"imagen remota ({ref[:48]}…): añade al sitio una dependencia de un tercero "
                "que puede cambiar o desaparecer. Co-ubícala junto al .md"
            )
        elif ref.startswith(("../", "/")):
            fallos.append(
                f"imagen fuera de la carpeta del documento ({ref[:48]}…): resuelve hoy, pero "
                "el día que la página cambie de sección el `../` apunta a otro sitio. "
                "Co-ubícala junto al .md"
            )

    # 6 — filas de tabla cuadradas.
    #
    # Es local al fichero, así que se comprueba aquí y no sólo en CI: una fila descuadrada NO
    # rompe el build —GFM recorta el sobrante en silencio— y el contenido desaparece del sitio
    # publicado sin que nada avise. La causa casi siempre es un `|` dentro de `código`, que en
    # GFM separa celdas igual que uno suelto.
    for n_linea, esperadas, hay, contenido in filas_descuadradas(texto):
        fallos.append(
            f"línea {n_linea}: fila de tabla con {hay} celdas y cabecera de {esperadas} -> "
            f"{contenido[:48]}… (¿un `|` sin escapar? dentro de `código` también separa: "
            "escríbelo `\\|`)"
        )

    # 7 — ruta ASCII y en minúscula, carpetas incluidas.
    #
    # Docusaurus construye la URL con la ruta entera, así que una carpeta `Evaluación/` da el
    # mismo problema que un fichero `Phases.md`: `/Evaluaci%C3%B3n/…`. Se recorren todos los
    # tramos por debajo de `docs/`.
    for n, tramo in enumerate(tramos):
        que = "el fichero" if n == len(tramos) - 1 else "la carpeta"
        if tramo != unicodedata.normalize("NFKD", tramo).encode("ascii", "ignore").decode():
            fallos.append(
                f"{que} `{tramo}` no es ASCII: su URL saldría percent-encoded. Renómbralo "
                "transliterado"
            )
        if tramo != tramo.lower():
            fallos.append(
                f"{que} `{tramo}` tiene mayúsculas: en este repositorio las rutas de docs/ van "
                "en minúscula, y una sola excepción parte el sitio en dos convenciones"
            )

    # 8 — nada publicable que identifique a nadie.
    for m in RE_EMAIL.finditer(texto):
        if not es_demo(m.group(0)):
            fallos.append(f"correo no demo: {m.group(0)}. Usa un dominio @ejemplo.com")
    for m in RE_IP.finditer(texto):
        if m.group(0) not in IPS_DOC:
            fallos.append(f"dirección IP: {m.group(0)}. El repositorio es público")
    for m in RE_SECRETO.finditer(texto):
        fallos.append(f"parece una credencial: {m.group(0)[:40]}… El repositorio es público")
    for m in RE_URL_CODABENCH.finditer(texto):
        if m.group(1).lower() not in HOSTS_CODABENCH:
            fallos.append(
                f"URL de una instancia de Codabench que no es la pública: {m.group(0)[:48]}…. "
                "Enlaza a www.codabench.org o a docs.codabench.org"
            )
    for ident in privados():
        if re.search(re.escape(ident), texto, re.I):
            fallos.append(
                f"menciona un identificador de la lista privada ({ident[:24]}…). El repositorio "
                "es público"
            )

    if not fallos:
        return 0

    rel = p.as_posix()
    print(f"{rel} incumple las reglas de docs/:", file=sys.stderr)
    for f in fallos:
        print(f"  - {f}", file=sys.stderr)
    print("Detalle en .claude/rules/documentacion.md", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
