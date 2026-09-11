#!/usr/bin/env python3
"""¿Sigue siendo cierta la versión de Codabench con la que esta guía dice estar contrastada?

    python scripts/check_codabench.py            # informe: ¿hay versión nueva? ¿qué revisar?
    python scripts/check_codabench.py --fijar    # cierre mecánico: sube la etiqueta de versión

Códigos de salida: 0 al día · 1 hay algo que revisar · 2 no se pudo consultar la API.

Por qué existe
--------------
Este sitio afirma —en la etiqueta de versión del navbar, en el pie de todas las páginas y en
`docs-map.json`— estar contrastado con **Codabench v1.23**. No es un adorno: es lo que sostiene
todo lo demás, porque la guía describe pantallas y campos de un producto que no es nuestro.

Y esa es justo la diferencia con el manual de captia.ai, del que se replica este patrón: allí
el producto vive en un repositorio hermano y la versión se lee de su `package.json`. Aquí
**Codabench es externo**. No hay repositorio que mirar en local, así que la referencia es la
última release publicada en GitHub, que es lo que este script consulta:

    https://api.github.com/repos/codalab/codabench/releases/latest

Cuando Codabench publica una versión y nadie toca la guía, la afirmación pasa a ser falsa en
silencio: no hay build, ni validador, ni enlace roto que lo note. Este comando es el aviso.

Lo que NO hace, a propósito
---------------------------
No revisa contenido. Que una versión nueva cambie —o no— las pantallas que aquí se describen
solo se sabe abriendo Codabench y recorriéndolas. Este script señala qué páginas dependen de
qué fuentes (lo lee de `docs-map.json`) para que esa revisión sea acotada, y nada más.

Y `--fijar` **no se ejecuta antes** de haber hecho esa revisión. Subir la etiqueta de versión
sin haber comprobado el contenido no actualiza nada: convierte una afirmación caducada en una
afirmación falsa, que es peor. La caducada se detecta comparando versiones —justamente con este
script—; la falsa solo la descubre un lector siguiendo instrucciones que ya no encajan con lo
que tiene en pantalla.

Solo biblioteca estándar: `urllib`. Sin red, falla con un mensaje y código 2, no con un
traceback.
"""

from __future__ import annotations

import argparse
import io
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CONFIG = REPO / "docusaurus.config.js"
DOCS = REPO / "docs"
DOCS_MAP = REPO / "docs-map.json"

API_RELEASE = "https://api.github.com/repos/codalab/codabench/releases/latest"
AGENTE = "check_codabench/1.0 (guía de Codabench de CAPTIA Technology)"

# La etiqueta se escribe siempre igual: «Codabench v1.23». Buscar la frase entera, y no un
# `v1.23` suelto, es lo que evita tocar las URLs de la documentación oficial, que llevan la
# versión en la ruta (`docs.codabench.org/v1.23/...`) y NO deben reescribirse a ciegas.
RE_ETIQUETA = re.compile(r"Codabench v\d+(?:\.\d+)*")
RE_VERSION = re.compile(r"\d+(?:\.\d+)*")
RE_LABEL = re.compile(r"current:\s*\{[^}]*?label:\s*['\"]([^'\"]+)['\"]", re.S)
RE_COPYRIGHT = re.compile(r"copyright:\s*[`'\"](.+?)[`'\"]\s*,", re.S)
RE_REVISION = re.compile(r"(\"revision_contrastada\"\s*:\s*\")([^\"]*)(\")")

# ---------------------------------------------------------------------------
# DÓNDE VIVE LA ETIQUETA. Lista explícita, no un barrido por todo el repositorio.
#
# `docs-meta/` queda fuera a propósito: son registros fechados de lo que se decidió en su
# momento y contra qué versión se contrastó. Reescribirles la versión los convertiría en un
# historial falso, que es el único tipo de documento peor que ninguno.
#
# `docs-map.json` tampoco está: lo genera `scripts/build_nav.py`, y se regenera solo en cuanto
# se le pasa `--apply`. Lo que sí se toca es el literal DENTRO de `build_nav.py`, que es de
# donde sale.
# ---------------------------------------------------------------------------

FICHEROS_ETIQUETA = [
    ("docusaurus.config.js", "la etiqueta del navbar y el pie de página"),
    ("README.md", "la presentación del repositorio"),
    ("CLAUDE.md", "el índice que leen los agentes"),
    (".claude/rules/documentacion.md", "las plantillas que se copian al escribir"),
]

GLOB_DOCS = ("docs/**/*.md", "docs/**/*.mdx")
INTOCABLES = ("docs-meta/", "docs-map.json", "package-lock.json")


class SinRespuesta(Exception):
    """No se pudo consultar la API. Se distingue de «hay versión nueva» en el código de salida."""


def _consola_utf8() -> None:
    """La consola de Windows es cp1252 y revienta al imprimir caracteres que no cubre."""
    for flujo in (sys.stdout, sys.stderr):
        if hasattr(flujo, "reconfigure"):
            flujo.reconfigure(encoding="utf-8", errors="replace")


def leer(p: Path) -> str:
    return io.open(p, encoding="utf-8").read()


def escribir(p: Path, s: str) -> None:
    io.open(p, "w", encoding="utf-8", newline="\n").write(s)


def token(etiqueta: str) -> str:
    """«Codabench v1.23», «v1.23» y «1.23» son la misma versión. Devuelve «1.23»."""
    m = RE_VERSION.search(etiqueta or "")
    return m.group(0) if m else ""


# --- lo que declara este sitio ---------------------------------------------------------------

def declarado() -> dict[str, str]:
    """{dónde: etiqueta} en cada sitio donde este repositorio afirma una versión."""
    sitios: dict[str, str] = {}

    if CONFIG.is_file():
        texto = leer(CONFIG)
        m = RE_LABEL.search(texto)
        if m:
            sitios["docusaurus.config.js (versions.current.label)"] = m.group(1)
        m = RE_COPYRIGHT.search(texto)
        if m:
            e = RE_ETIQUETA.search(m.group(1))
            if e:
                sitios["docusaurus.config.js (copyright)"] = e.group(0)

    if DOCS_MAP.is_file():
        try:
            datos = json.loads(leer(DOCS_MAP))
        except json.JSONDecodeError:
            sitios["docs-map.json"] = "(JSON no válido)"
        else:
            for id_fuente, meta in (datos.get("_fuentes") or {}).items():
                if isinstance(meta, dict) and "revision_contrastada" in meta:
                    sitios[f"docs-map.json (_fuentes.{id_fuente})"] = str(
                        meta["revision_contrastada"])

    return sitios


def por_fuente() -> dict[str, list[str]]:
    """{fuente: [documentos que dependen de ella]}, leyendo `docs-map.json`.

    Es la pregunta que ese fichero existe para responder: si Codabench cambia, qué páginas hay
    que volver a mirar. Aquí las fuentes son URLs de la documentación oficial en vez de rutas
    de un repositorio, porque el producto es externo.
    """
    if not DOCS_MAP.is_file():
        return {}
    try:
        datos = json.loads(leer(DOCS_MAP))
    except json.JSONDecodeError:
        return {}
    agrupado: dict[str, list[str]] = {}
    for doc in datos.get("documents", []):
        nombre = doc.get("doc", "?")
        for fuente in doc.get("sources", []):
            for ruta in fuente.get("paths", []):
                agrupado.setdefault(ruta, []).append(nombre)
    return agrupado


# --- lo que publica Codabench ----------------------------------------------------------------

def ultima_release(timeout: float) -> dict:
    """La release más reciente de codalab/codabench. Lanza SinRespuesta si no se puede saber."""
    cabeceras = {"User-Agent": AGENTE, "Accept": "application/vnd.github+json"}
    # La API sin autenticar permite 60 peticiones por hora y por IP. Con un token del entorno
    # sube a 5.000; no hace falta ningún permiso, así que sirve cualquiera de solo lectura.
    ficha = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if ficha:
        cabeceras["Authorization"] = f"Bearer {ficha}"

    peticion = urllib.request.Request(API_RELEASE, headers=cabeceras)
    try:
        with urllib.request.urlopen(peticion, timeout=timeout) as r:
            crudo = r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        if e.code in (403, 429):
            raise SinRespuesta(
                f"la API de GitHub responde {e.code}: se ha agotado el límite de peticiones "
                "sin autenticar (60/hora). Exporta GITHUB_TOKEN y vuelve a intentarlo, o "
                "espera un rato.") from e
        if e.code == 404:
            raise SinRespuesta(
                "la API responde 404: o el repositorio codalab/codabench cambió de nombre, o "
                "no tiene ninguna release publicada. Compruébalo a mano antes de tocar nada."
            ) from e
        raise SinRespuesta(f"la API de GitHub responde {e.code} ({e.reason}).") from e
    except urllib.error.URLError as e:
        raise SinRespuesta(
            f"no se pudo conectar con api.github.com ({e.reason}). Este comando necesita red; "
            "sin ella no hay nada con lo que comparar.") from e
    except Exception as e:  # timeout, certificado, proxy que devuelve basura
        raise SinRespuesta(f"no se pudo consultar la API ({type(e).__name__}: {e}).") from e

    try:
        return json.loads(crudo)
    except json.JSONDecodeError as e:
        raise SinRespuesta(
            "la API devolvió algo que no es JSON. Suele ser un proxy o un portal de red "
            "interceptando la petición.") from e


# --- informe ---------------------------------------------------------------------------------

def informe(timeout: float) -> int:
    sitios = declarado()
    if not sitios:
        print("No se encontró ninguna versión declarada en este repositorio.")
        print("Se esperaba al menos `versions.current.label` en docusaurus.config.js.")
        return 1

    print("versión que declara este sitio:")
    for donde, valor in sitios.items():
        print(f"  {valor:<20}  {donde}")

    tokens = {token(v) for v in sitios.values() if token(v)}
    coherente = len(tokens) == 1
    if not coherente:
        print("\nINCOHERENCIA: este repositorio afirma más de una versión a la vez. El navbar,")
        print("el pie de página y docs-map.json tienen que decir lo mismo; hoy no lo dicen, así")
        print("que el sitio publicado se contradice a sí mismo. Arréglalo antes de seguir.")

    try:
        release = ultima_release(timeout)
    except SinRespuesta as e:
        print(f"\nNo se pudo consultar la última release de Codabench: {e}")
        print("(Si solo querías comparar con una versión concreta: --fijar --version X.Y)")
        return 2

    etiqueta_release = release.get("tag_name") or release.get("name") or ""
    publicada = token(etiqueta_release)
    print("\núltima release publicada de codalab/codabench:")
    print(f"  {etiqueta_release or '(sin etiqueta)':<20}  {release.get('name') or ''}"
          f"  {(release.get('published_at') or '')[:10]}")
    if release.get("html_url"):
        print(f"  {release['html_url']}")

    if not publicada:
        print("\nLa release no trae un número de versión reconocible en `tag_name` ni en `name`.")
        print("Míralo a mano en la URL de arriba.")
        return 2

    documentada = sorted(tokens)[0] if tokens else ""
    if coherente and publicada == documentada:
        print(f"\nAl día: la guía dice describir la misma versión que publica Codabench "
              f"({documentada}).")
        return 0

    if coherente:
        print(f"\nHAY VERSIÓN NUEVA: Codabench publica {publicada} y esta guía afirma estar")
        print(f"contrastada con {documentada}. Esa afirmación está en el sitio publicado, en el")
        print("pie de todas las páginas, así que hoy puede ser falsa.")

    fuentes = por_fuente()
    print("\n--- qué cubre cada fuente (docs-map.json) ---")
    if not fuentes:
        print("  docs-map.json no existe o no declara fuentes todavía. Genéralo con:")
        print("    python scripts/build_nav.py --apply")
        print("  Sin él no se puede acotar la revisión y hay que mirar la guía entera.")
    else:
        for fuente, docs in sorted(fuentes.items(), key=lambda kv: (-len(kv[1]), kv[0])):
            print(f"  {fuente}")
            for d in sorted(docs):
                print(f"      {d}")

    print("\n--- qué hacer ---")
    print("  1. Abrir Codabench y recorrer las pantallas que describen las páginas de arriba,")
    print("     empezando por las fuentes que cubren más páginas. Es trabajo de criterio: hay")
    print("     versiones que no mueven ni un campo del formulario y otras que renombran media")
    print("     interfaz. NO subir la etiqueta antes de esto.")
    print("  2. Corregir lo que haya cambiado, respetando la plantilla de página.")
    print("  3. Comprobar que las fuentes citadas siguen vivas —la documentación oficial usa")
    print("     rutas con versión— :")
    print("       python scripts/check_fuentes.py")
    print("  4. Solo entonces, cerrar el ciclo:")
    print("       python scripts/check_codabench.py --fijar")
    print("  5. Y volver a pasar las comprobaciones de siempre:")
    print("       python scripts/check_docs.py")
    print("       python scripts/build_nav.py --apply")
    print("       npm run build")
    return 1


# --- cierre mecánico -------------------------------------------------------------------------

def apariciones(texto_buscado: str) -> dict[str, int]:
    """Cuántas veces aparece una cadena en cada fichero versionado, según git."""
    try:
        salida = subprocess.run(
            ["git", "grep", "-c", "-F", texto_buscado, "--", ":!package-lock.json"],
            cwd=REPO, capture_output=True, text=True, encoding="utf-8", errors="replace")
    except OSError:
        return {}
    conteo: dict[str, int] = {}
    for linea in salida.stdout.splitlines():
        if ":" in linea:
            f, n = linea.rsplit(":", 1)
            if n.strip().isdigit():
                conteo[f.replace("\\", "/")] = int(n)
    return conteo


def fijar(timeout: float, version_manual: str | None, forzar: bool) -> int:
    sitios = declarado()
    tokens = {token(v) for v in sitios.values() if token(v)}
    if len(tokens) != 1:
        print("No se puede fijar: este repositorio declara versiones distintas en sitios")
        print("distintos (o ninguna). Únifícalas a mano primero:")
        for donde, valor in sitios.items():
            print(f"  {valor:<20}  {donde}")
        return 1
    vieja = sorted(tokens)[0]

    if version_manual:
        nueva = token(version_manual)
        if not nueva:
            print(f"«{version_manual}» no contiene un número de versión reconocible.")
            return 1
    else:
        try:
            release = ultima_release(timeout)
        except SinRespuesta as e:
            print(f"No se pudo consultar la última release de Codabench: {e}")
            print("Si ya sabes qué versión quieres fijar, pásala: --fijar --version 1.24")
            return 2
        nueva = token(release.get("tag_name") or release.get("name") or "")
        if not nueva:
            print("La release publicada no trae un número de versión reconocible.")
            return 2

    if nueva == vieja and not forzar:
        print(f"La guía ya dice {vieja}. Nada que fijar (--forzar reescribe igualmente).")
        return 0

    antigua_etiqueta = f"Codabench v{vieja}"
    nueva_etiqueta = f"Codabench v{nueva}"
    print(f"subiendo la etiqueta de versión: {antigua_etiqueta} -> {nueva_etiqueta}")
    print("(esto NO revisa contenido; se da por hecho que ya lo has contrastado con la UI)\n")

    for rel, motivo in FICHEROS_ETIQUETA:
        p = REPO / rel
        if not p.is_file():
            continue
        t = leer(p)
        n = t.count(antigua_etiqueta)
        if n:
            escribir(p, t.replace(antigua_etiqueta, nueva_etiqueta))
            print(f"  {n:3d}  {rel}   ({motivo})")

    n_docs = f_docs = 0
    for patron in GLOB_DOCS:
        for p in sorted(REPO.glob(patron)):
            t = leer(p)
            c = t.count(antigua_etiqueta)
            if c:
                escribir(p, t.replace(antigua_etiqueta, nueva_etiqueta))
                n_docs += c
                f_docs += 1
    print(f"  {n_docs:3d}  docs/ ({f_docs} páginas)   (la afirmación que lee el usuario)")

    # `docs-map.json` es generado: lo que se toca es el literal del que sale, dentro de
    # build_nav.py. Se sustituye solo el número, para respetar cómo esté escrito el valor
    # («Codabench v1.23» o «1.23»).
    p = REPO / "scripts" / "build_nav.py"
    if p.is_file():
        t = leer(p)
        t2, n = RE_REVISION.subn(
            lambda m: m.group(1) + m.group(2).replace(vieja, nueva) + m.group(3), t)
        if n and t2 != t:
            escribir(p, t2)
            print(f"  {n:3d}  scripts/build_nav.py   (la revisión que se escribe en docs-map)")
        elif not n:
            print("  AVISO  no se encontró `revision_contrastada` en scripts/build_nav.py;")
            print("         revísalo a mano.")

    restantes = apariciones(f"v{vieja}")
    intocadas = {f: n for f, n in restantes.items()
                 if any(f.startswith(i) or f == i for i in INTOCABLES)}
    otras = {f: n for f, n in restantes.items() if f not in intocadas}

    if intocadas:
        print(f"\n  Sin tocar a propósito ({sum(intocadas.values())} apariciones): son registros")
        print("  fechados o ficheros generados, y reescribirlos falsearía lo que cuentan.")
        for f, n in sorted(intocadas.items()):
            print(f"    {n:3d}  {f}")

    if otras:
        print(f"\n  QUEDAN APARICIONES DE v{vieja} SIN TOCAR. Casi todas serán URLs de la")
        print("  documentación oficial, que lleva la versión en la ruta")
        print(f"  (docs.codabench.org/v{vieja}/...). NO se cambian solas a propósito: la")
        print(f"  documentación de la versión {nueva} puede no existir en esa ruta todavía, y")
        print("  el enlace quedaría en 404. Míralas una a una y comprueba con:")
        print("    python scripts/check_fuentes.py")
        for f, n in sorted(otras.items()):
            print(f"    {n:3d}  {f}")

    print("\nSiguiente paso obligatorio:")
    print("  python scripts/build_nav.py --apply   # regenera docs-map.json con la revisión nueva")
    print("  python scripts/check_docs.py")
    print("  npm run build")
    return 0


def main() -> int:
    _consola_utf8()
    ap = argparse.ArgumentParser(
        description="Compara la versión de Codabench que declara este sitio con la última "
                    "release publicada del producto.",
        epilog="--fijar es el cierre MECÁNICO del ciclo y va DESPUÉS de revisar la guía contra "
               "la UI. Subir la etiqueta sin revisar el contenido convierte una afirmación "
               "caducada en una falsa, que es peor: la caducada se detecta comparando "
               "versiones, la falsa solo la descubre un lector siguiendo instrucciones que ya "
               "no encajan con su pantalla.")
    ap.add_argument("--fijar", action="store_true",
                    help="sube la etiqueta de versión donde aparece (NO antes de revisar)")
    ap.add_argument("--version",
                    help="versión a fijar; con ella no hace falta consultar la API")
    ap.add_argument("--forzar", action="store_true",
                    help="con --fijar, reescribe aunque la versión ya coincida")
    ap.add_argument("--timeout", type=float, default=10.0,
                    help="segundos de espera de la API de GitHub (por defecto 10)")
    args = ap.parse_args()

    if args.version and not args.fijar:
        print("--version solo tiene sentido con --fijar. Sin él, este comando informa de lo que")
        print("hay publicado, y eso no se elige a mano.")
        return 1

    if args.fijar:
        return fijar(args.timeout, args.version, args.forzar)
    return informe(args.timeout)


if __name__ == "__main__":
    raise SystemExit(main())
