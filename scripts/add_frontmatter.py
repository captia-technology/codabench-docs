#!/usr/bin/env python3
"""Pone `title` en el front matter de un documento que no lo tiene, deducido de su H1.

Reparto de responsabilidades
----------------------------
Está acotado a propósito, y el corte importa:

- **Aquí**: `title`, y solo `title`. Sale del H1 del propio documento, sin emoji.
- **En `scripts/build_nav.py`**: `sidebar_position`, `sidebar_label`, `description` y los
  `_category_.json` de cada carpeta.

El orden del sidebar no se deduce de nada: se declara entero en `build_nav.py`, que además
FALLA si aparece un documento sin declarar. El efecto práctico para quien añade una página es
que este script le pone el título y `build_nav.py` se niega a pasar hasta que la coloques a
mano en el recorrido. Es deliberado: colocar una página en la guía es una decisión, no un
detalle.

Por qué aquí no hay `slug`
--------------------------
El manual del que se replica este patrón genera además un `slug` transliterado, porque arrastra
rutas heredadas con tildes y mayúsculas (`Configuración/`) que Docusaurus publicaría
percent-encodadas. Aquí no hace falta: la invariante 7 exige rutas ASCII en minúscula bajo
`docs/`, así que la URL que Docusaurus deduce del nombre del fichero ya es la buena y no hay
nada que fijar. Es más barato prohibirlo de entrada que taparlo después.

Lo que este script NO arregla, a propósito
------------------------------------------
Si encuentra bajo `docs/` un nombre de fichero o de carpeta con mayúsculas o con caracteres no
ASCII, **avisa y se detiene ahí**: no lo renombra. Renombrar un fichero cambia la URL publicada,
y una URL puede estar enlazada desde otras páginas, desde el footer de `docusaurus.config.js` o
desde fuera del sitio. Elegir el nombre nuevo —y, si procede, dejar una redirección— es una
decisión editorial. Quien bloquea la publicación de una ruta así es `scripts/check_docs.py`,
que es donde vive la invariante; este script solo lo pone delante de los ojos.

Uso
---
    python scripts/add_frontmatter.py            # informe, no escribe (código 0)
    python scripts/add_frontmatter.py --check    # informe, código 1 si queda trabajo
    python scripts/add_frontmatter.py --apply    # escribe el front matter que falta

Idempotente: un documento que ya tiene `title` se deja intacto.
"""

from __future__ import annotations

import argparse
import io
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DOCS = REPO / "docs"

RE_H1 = re.compile(r"^#\s+(?P<t>.+?)\s*$", re.MULTILINE)
RE_TITLE = re.compile(r"^title\s*:", re.MULTILINE)
EMOJI = re.compile("[\U0001f300-\U0001faff☀-➿️‍⏱⏲⌛⌚]+")


def _consola_utf8() -> None:
    """La consola de Windows es cp1252 y revienta al imprimir caracteres que no cubre."""
    for flujo in (sys.stdout, sys.stderr):
        if hasattr(flujo, "reconfigure"):
            flujo.reconfigure(encoding="utf-8", errors="replace")


def leer(p: Path) -> str:
    return io.open(p, encoding="utf-8").read()


def escribir(p: Path, s: str) -> None:
    io.open(p, "w", encoding="utf-8", newline="\n").write(s)


def sin_emoji(s: str) -> str:
    """El front matter y los títulos van sin emoji (regla de estilo del repositorio)."""
    return EMOJI.sub("", s).strip().strip("–-—").strip()


def partir_front_matter(texto: str) -> tuple[str | None, str]:
    """Devuelve (front matter sin los `---`, cuerpo). El front matter es None si no hay."""
    lineas = texto.split("\n")
    if not lineas or lineas[0].strip() != "---":
        return None, texto
    for i in range(1, len(lineas)):
        if lineas[i].strip() == "---":
            return "\n".join(lineas[1:i]), "\n".join(lineas[i + 1:])
    # Front matter abierto y sin cerrar: no es front matter para Docusaurus, es texto roto.
    # Se trata como documento sin front matter y `check_docs.py` dirá lo suyo.
    return None, texto


def titulo_de(texto_cuerpo: str, respaldo: str) -> str:
    """Título a partir del primer H1 del cuerpo; si no hay ninguno, el nombre del fichero."""
    m = RE_H1.search(texto_cuerpo)
    return sin_emoji(m.group("t")) if m else respaldo


def rutas_no_conformes() -> list[str]:
    """Nombres bajo `docs/` con mayúsculas o caracteres no ASCII (invariante 7)."""
    malos = []
    for p in sorted(DOCS.rglob("*")):
        rel = p.relative_to(DOCS).as_posix()
        if rel != rel.lower() or not rel.isascii():
            malos.append(rel)
    return malos


def main() -> int:
    _consola_utf8()
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--apply", action="store_true",
                    help="escribe el `title` que falte")
    ap.add_argument("--check", action="store_true",
                    help="no escribe; sale con código 1 si queda algún documento sin `title`")
    args = ap.parse_args()

    if not DOCS.is_dir():
        print(f"No existe {DOCS.relative_to(REPO).as_posix()}/: nada que hacer.")
        return 0

    documentos = sorted(list(DOCS.rglob("*.md")) + list(DOCS.rglob("*.mdx")))
    cambios: list[tuple[Path, str, str]] = []  # (fichero, texto nuevo, motivo)
    ya = 0

    for p in documentos:
        texto = leer(p)
        front, cuerpo = partir_front_matter(texto)

        if front is None:
            titulo = titulo_de(cuerpo, p.stem)
            nuevo = f'---\ntitle: "{titulo}"\n---\n\n' + texto.lstrip("\n")
            cambios.append((p, nuevo, f'sin front matter -> title: "{titulo}"'))
            continue

        if RE_TITLE.search(front):
            ya += 1
            continue

        # Front matter presente pero sin `title`. Pasa en cuanto alguien escribe una página
        # nueva copiando solo `sidebar_position` de otra, y no es inofensivo: sin `title`,
        # Docusaurus rellena el de la pestaña y el del sidebar con el H1 o con el nombre del
        # fichero, y la invariante 3 —`title` == H1— deja de poder comprobarse.
        titulo = titulo_de(cuerpo, p.stem)
        nuevo = "---\n" + f'title: "{titulo}"\n' + front.strip("\n") + "\n---\n" + cuerpo
        cambios.append((p, nuevo, f'front matter sin title -> title: "{titulo}"'))

    print(f"documentos       : {len(documentos)}")
    print(f"con `title` ya   : {ya}")
    print(f"pendientes       : {len(cambios)}")
    for p, _, motivo in cambios[:10]:
        print(f"    {p.relative_to(REPO).as_posix()}  ({motivo})")
    if len(cambios) > 10:
        print(f"    ... y {len(cambios) - 10} más")

    # El aviso de rutas se da siempre, se escriba o no: es un problema distinto del que este
    # script resuelve, y quien lo bloquea es `check_docs.py`. Por eso NO cambia el código de
    # salida de aquí, que habla solo del front matter.
    malos = rutas_no_conformes()
    if malos:
        print(f"\nAVISO  {len(malos)} rutas bajo docs/ con mayúsculas o caracteres no ASCII:")
        for rel in malos[:10]:
            print(f"    docs/{rel}")
        if len(malos) > 10:
            print(f"    ... y {len(malos) - 10} más")
        print("  Este script NO las renombra: renombrar cambia la URL publicada y eso se")
        print("  decide, no se automatiza. Renómbralas a mano (minúscula ASCII), corrige los")
        print("  enlaces que apunten a ellas y vuelve a pasar check_docs.py.")

    if args.apply:
        for p, nuevo, _ in cambios:
            escribir(p, nuevo)
        print(f"\nescritos: {len(cambios)}")
        if cambios:
            print("Siguiente paso obligatorio: declararlos en scripts/build_nav.py y aplicarlo:")
            print("  python scripts/build_nav.py --apply")
        return 0

    if cambios:
        print("\nPara arreglarlo: python scripts/add_frontmatter.py --apply")
    return 1 if (args.check and cambios) else 0


if __name__ == "__main__":
    raise SystemExit(main())
