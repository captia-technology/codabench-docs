#!/usr/bin/env python3
"""Deja un solo H1 por documento y baja el resto a H2.

Por qué
-------
Esta guía nace de repartir un único documento de 236 líneas en 21 páginas, y va a seguir
creciendo por el mismo camino: se corta un bloque de un sitio y se pega en otro. Esa operación
es justo la que deja dos `# ` en la misma página —el que ya traía el bloque y el título nuevo
que se le pone encima—, y el resultado rompe tres cosas:

1. **La página no pasa la validación.** «Un solo H1 por documento» es invariante bloqueante:
   la comprueban `scripts/check_docs.py` (lo mismo que corre en CI) y el hook
   `.claude/hooks/validar_doc.py`. Este script es el arreglo mecánico de ese fallo; no hace
   falta corregir los encabezados a mano uno a uno.
2. **El índice de la derecha se queda corto.** El de Docusaurus se construye desde H2 en
   adelante (`tableOfContents: { minHeadingLevel: 2 }` en `docusaurus.config.js`), así que una
   sección escrita en H1 no aparece en él: el lector no la ve en el índice de la página.
3. **Accesibilidad.** Varios H1 en una página rompen la jerarquía de encabezados en la que se
   apoyan los lectores de pantalla para navegar.

Qué hace
--------
Conserva el PRIMER `# ` del cuerpo de cada fichero —el título— y convierte los siguientes en
`## `. No toca los `##` ni los niveles inferiores, ni el contenido, ni el front matter, ni lo
que haya dentro de un bloque de código.

    python scripts/normalize_headings.py            # informe, no escribe (código 0)
    python scripts/normalize_headings.py --check    # informe, código 1 si queda trabajo
    python scripts/normalize_headings.py --apply    # reescribe los documentos

Idempotente: sobre un documento ya normalizado no cambia nada.

Dos detalles que no son obvios
------------------------------
- **El front matter se salta entero.** Sus líneas de comentario YAML empiezan por `# `, y esta
  plantilla lleva front matter en todas las páginas. Sin saltarlo, un comentario como
  `# sidebar_position lo pone build_nav.py` se tomaría por el título del documento y el H1 de
  verdad acabaría degradado a H2, que es exactamente lo contrario de lo que hay que hacer.
- **Solo `.md`.** La portada es `docs/index.mdx` y compone JSX; ahí los encabezados salen del
  componente `Portada`, no de líneas Markdown, y reescribir a ciegas dentro de JSX es más
  riesgo que beneficio. Si alguna vez la portada tuviera dos H1, lo dirá `check_docs.py`.
"""

from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DOCS = REPO / "docs"


def _consola_utf8() -> None:
    """La consola de Windows es cp1252 y revienta al imprimir caracteres que no cubre."""
    for flujo in (sys.stdout, sys.stderr):
        if hasattr(flujo, "reconfigure"):
            flujo.reconfigure(encoding="utf-8", errors="replace")


def leer(p: Path) -> str:
    return io.open(p, encoding="utf-8").read()


def escribir(p: Path, s: str) -> None:
    io.open(p, "w", encoding="utf-8", newline="\n").write(s)


def fin_del_front_matter(lineas: list[str]) -> int:
    """Índice de la primera línea del cuerpo. 0 si el documento no lleva front matter."""
    if not lineas or lineas[0].strip() != "---":
        return 0
    for i in range(1, len(lineas)):
        if lineas[i].strip() == "---":
            return i + 1
    # Front matter sin cerrar: es un error de sintaxis que denuncia `check_docs.py`. Aquí se
    # trata el fichero entero como cuerpo antes que arriesgarse a saltárselo completo.
    return 0


def normalizar(texto: str) -> tuple[str, int]:
    """Devuelve (texto nuevo, cuántos H1 se bajaron a H2)."""
    lineas = texto.split("\n")
    visto_titulo = False
    bajados = 0
    valla = ""  # delimitador del bloque de código abierto; "" si no hay ninguno

    for i in range(fin_del_front_matter(lineas), len(lineas)):
        linea = lineas[i]
        despojada = linea.lstrip()

        # Los bloques de código se saltan enteros: un `# comentario` de shell o un `#!/usr/bin`
        # dentro de un ejemplo no es un encabezado y degradarlo cambiaría el ejemplo. Se
        # aceptan las dos vallas de CommonMark, ``` y ~~~.
        if valla:
            if despojada.startswith(valla):
                valla = ""
            continue
        if despojada.startswith("```") or despojada.startswith("~~~"):
            valla = despojada[0] * 3
            continue

        # Un `# ` sangrado cuatro espacios es un bloque de código indentado, no un H1: por eso
        # se mira la línea sin despojar.
        if not linea.startswith("# "):
            continue
        if not visto_titulo:
            visto_titulo = True
            continue
        lineas[i] = "#" + linea
        bajados += 1

    return "\n".join(lineas), bajados


def main() -> int:
    _consola_utf8()
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--apply", action="store_true",
                    help="reescribe los documentos que lo necesiten")
    ap.add_argument("--check", action="store_true",
                    help="no escribe; sale con código 1 si queda algo por normalizar")
    args = ap.parse_args()

    if not DOCS.is_dir():
        print(f"No existe {DOCS.relative_to(REPO).as_posix()}/: nada que normalizar.")
        return 0

    tocados: list[tuple[Path, int]] = []
    total = 0
    for md in sorted(DOCS.rglob("*.md")):
        texto = leer(md)
        nuevo, n = normalizar(texto)
        if not n:
            continue
        tocados.append((md, n))
        total += n
        if args.apply:
            escribir(md, nuevo)

    verbo = "normalizados" if args.apply else "por normalizar"
    print(f"documentos {verbo}: {len(tocados)}  (encabezados bajados a H2: {total})")
    for md, n in tocados[:10]:
        print(f"    {md.relative_to(REPO).as_posix()}  ({n})")
    if len(tocados) > 10:
        print(f"    ... y {len(tocados) - 10} más")

    if tocados and not args.apply:
        print("\nPara arreglarlo: python scripts/normalize_headings.py --apply")

    # `--check` es el modo pensado para encadenar con otras comprobaciones, así que tiene que
    # distinguirse en el código de salida; sin flags es solo un informe.
    return 1 if (args.check and tocados) else 0


if __name__ == "__main__":
    raise SystemExit(main())
