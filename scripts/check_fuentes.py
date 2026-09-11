#!/usr/bin/env python3
"""Comprueba que las URLs externas que cita la guía siguen vivas.

    python scripts/check_fuentes.py             # comprueba todas
    python scripts/check_fuentes.py --listar    # solo las lista, sin tocar la red
    python scripts/check_fuentes.py --timeout 20

Sale con código 1 si alguna URL falla.

Por qué existe
--------------
Esta guía se apoya en documentación ajena. Casi todo lo que afirma sobre pantallas, campos y
formatos está contrastado contra `docs.codabench.org` y contra tutoriales de terceros, y esas
referencias son la única forma que tiene el lector de ir más allá de lo que aquí se cuenta. Un
enlace roto no rompe el build ni lo detecta `check_docs.py` —que solo valida los enlaces
*relativos*, los de dentro del repositorio—, así que se degrada en silencio: la página sigue
publicándose, con una fuente que ya no lleva a ninguna parte.

Hay además un caso propio de este sitio que conviene vigilar: la documentación de Codabench
vive bajo rutas con versión (`/latest/…` y `/v1.23/…`). Cuando se publica una versión nueva, un
enlace a `/latest/` puede seguir respondiendo 200 pero describiendo otra pantalla, y uno a una
versión concreta puede desaparecer. Este script detecta lo segundo; para lo primero está
`scripts/check_codabench.py`, que compara la versión publicada con la que este sitio declara.

Por qué NO corre en CI
----------------------
Necesita red, y las URLs son de terceros: caen, se mueven, devuelven 429 cuando les llegan
muchas peticiones seguidas y a veces rechazan las que no vienen de un navegador. Meterlo en el
pipeline convertiría el CI en algo que falla por motivos ajenos al repositorio, y un CI que
falla sin culpa del cambio se acaba ignorando —que es peor que no tenerlo—. Se pasa a mano
antes de una revisión de contenido, o desde una tarea programada que avise sin bloquear nada.

Cómo comprueba cada URL
-----------------------
Primero HEAD, que no descarga el cuerpo. Si el servidor no lo admite —bastantes responden 403,
405 o 501 a HEAD aunque el GET funcione perfectamente— se reintenta con GET, leyendo solo el
primer byte y cerrando. Se envía un User-Agent propio porque el de `urllib` por defecto es
motivo suficiente para que algunos servidores devuelvan 403.

Solo biblioteca estándar: `urllib`. Este repositorio no tiene dependencias de Python y no es
sitio para estrenar una.
"""

from __future__ import annotations

import argparse
import io
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

REPO = Path(__file__).resolve().parent.parent
DOCS = REPO / "docs"
DOCS_MAP = REPO / "docs-map.json"

# Se corta en el primer carácter que no puede formar parte de una URL en Markdown: el `)` cierra
# un enlace `[texto](url)`, el `>` un autoenlace `<url>`, y las comillas y los espacios separan.
RE_URL = re.compile(r"https?://[^\s<>\"'`\)\]\}]+")

# Sufijos de puntuación que casi siempre son del texto, no de la URL: «...según docs.x.org.» o
# «(ver https://x/y).». Se recortan por la derecha.
PUNTUACION_FINAL = ".,;:!?«»"

# No son fuentes, son marcadores de ejemplo dentro de la prosa. Pedirlas no dice nada útil.
HOSTS_IGNORADOS = ("localhost", "127.0.0.1", "example.com", "ejemplo.com")

AGENTE = "check_fuentes/1.0 (guía de Codabench de CAPTIA Technology)"


def _consola_utf8() -> None:
    """La consola de Windows es cp1252 y revienta al imprimir caracteres que no cubre."""
    for flujo in (sys.stdout, sys.stderr):
        if hasattr(flujo, "reconfigure"):
            flujo.reconfigure(encoding="utf-8", errors="replace")


def leer(p: Path) -> str:
    return io.open(p, encoding="utf-8").read()


def limpiar(url: str) -> str:
    """Recorta la puntuación de la frase y los paréntesis que no abrió la propia URL."""
    url = url.rstrip(PUNTUACION_FINAL)
    while url.endswith(")") and url.count("(") < url.count(")"):
        url = url[:-1].rstrip(PUNTUACION_FINAL)
    return url


def ignorada(url: str) -> bool:
    host = (urlparse(url).hostname or "").lower()
    return any(host == h or host.endswith("." + h) for h in HOSTS_IGNORADOS)


def urls_de_markdown(texto: str) -> set[str]:
    """URLs del cuerpo, saltando los bloques de código.

    Dentro de un bloque de código las URLs son ejemplos de comandos o de ficheros de
    configuración, no fuentes que la guía cite: comprobarlas dispararía falsos fallos.
    """
    encontradas: set[str] = set()
    valla = ""
    for linea in texto.split("\n"):
        despojada = linea.lstrip()
        if valla:
            if despojada.startswith(valla):
                valla = ""
            continue
        if despojada.startswith("```") or despojada.startswith("~~~"):
            valla = despojada[0] * 3
            continue
        for bruta in RE_URL.findall(linea):
            url = limpiar(bruta)
            if url and not ignorada(url):
                encontradas.add(url)
    return encontradas


def urls_de_json(dato) -> set[str]:
    """Recorre `docs-map.json` entero: las fuentes viven en `documents[].sources[].paths`,
    pero también hay URLs en `_fuentes`, y una copia del recorrido se quedaría corta en
    cuanto el esquema crezca."""
    encontradas: set[str] = set()
    if isinstance(dato, str):
        for bruta in RE_URL.findall(dato):
            url = limpiar(bruta)
            if url and not ignorada(url):
                encontradas.add(url)
    elif isinstance(dato, dict):
        for clave, valor in dato.items():
            encontradas |= urls_de_json(clave)
            encontradas |= urls_de_json(valor)
    elif isinstance(dato, list):
        for elemento in dato:
            encontradas |= urls_de_json(elemento)
    return encontradas


def recopilar() -> dict[str, list[str]]:
    """{url: [ficheros que la citan]}, deduplicado."""
    citas: dict[str, list[str]] = {}

    def anotar(url: str, origen: str) -> None:
        citas.setdefault(url, [])
        if origen not in citas[url]:
            citas[url].append(origen)

    if DOCS.is_dir():
        for p in sorted(list(DOCS.rglob("*.md")) + list(DOCS.rglob("*.mdx"))):
            origen = p.relative_to(REPO).as_posix()
            for url in urls_de_markdown(leer(p)):
                anotar(url, origen)

    if DOCS_MAP.is_file():
        try:
            datos = json.loads(leer(DOCS_MAP))
        except json.JSONDecodeError as e:
            print(f"AVISO  docs-map.json no es JSON válido ({e}); se omite.")
        else:
            for url in urls_de_json(datos):
                anotar(url, DOCS_MAP.name)
    else:
        print("AVISO  no hay docs-map.json todavía; se comprueban solo las URLs de docs/.")
        print("       Lo genera: python scripts/build_nav.py --apply")

    return citas


def pedir(url: str, timeout: float) -> tuple[int, str, str]:
    """Devuelve (código, url final, detalle). Código 0 si ni siquiera se pudo conectar."""
    for metodo in ("HEAD", "GET"):
        peticion = urllib.request.Request(url, method=metodo, headers={"User-Agent": AGENTE})
        try:
            with urllib.request.urlopen(peticion, timeout=timeout) as r:
                if metodo == "GET":
                    r.read(1)  # basta para saber que el cuerpo empieza a llegar
                return r.status, r.geturl(), ""
        except urllib.error.HTTPError as e:
            # 403, 405 y 501 son las respuestas típicas de un servidor que no admite HEAD.
            # El resto de códigos son del recurso, no del método: no se reintenta.
            if metodo == "HEAD" and e.code in (403, 405, 501):
                continue
            return e.code, e.url or url, e.reason or ""
        except Exception as e:  # DNS, certificado, timeout, redirección infinita
            if metodo == "HEAD":
                continue
            return 0, url, f"{type(e).__name__}: {e}"
    return 0, url, "sin respuesta"


def misma_url(a: str, b: str) -> bool:
    return a.rstrip("/") == b.rstrip("/")


def main() -> int:
    _consola_utf8()
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--listar", action="store_true",
                    help="solo lista las URLs y quién las cita; no toca la red")
    ap.add_argument("--timeout", type=float, default=10.0,
                    help="segundos de espera por petición (por defecto 10)")
    args = ap.parse_args()

    citas = recopilar()
    if not citas:
        print("No hay ninguna URL externa que comprobar.")
        return 0

    print(f"\nURLs externas distintas: {len(citas)}\n")

    if args.listar:
        for url in sorted(citas):
            print(f"  {url}")
            for origen in citas[url]:
                print(f"      {origen}")
        return 0

    fallos: list[str] = []
    avisos: list[str] = []
    for url in sorted(citas):
        codigo, final, detalle = pedir(url, args.timeout)

        if codigo == 0:
            marca, resumen = "FALLO", "---"
            fallos.append(f"{url} -> no se pudo conectar ({detalle})")
        elif codigo == 429:
            # No dice nada del enlace: dice que se ha pedido demasiado deprisa.
            marca, resumen = "aviso", "429"
            avisos.append(f"{url} -> 429, el servidor limita el ritmo; reintenta más tarde")
        elif 200 <= codigo < 300:
            marca, resumen = "ok   ", str(codigo)
            if not misma_url(final, url):
                avisos.append(f"{url}\n           redirige a {final}")
        else:
            marca, resumen = "FALLO", str(codigo)
            fallos.append(f"{url} -> {codigo} {detalle}".rstrip())

        print(f"  {marca} {resumen:>3}  {url}")

    if avisos:
        print(f"\n--- avisos ({len(avisos)}) ---")
        print("Responden, pero conviene mirarlos: una redirección permanente significa que la")
        print("guía cita una URL que ya no es la buena, y arreglarla ahorra un salto al lector.")
        for a in avisos:
            print(f"  {a}")

    if fallos:
        print(f"\n--- fallos ({len(fallos)}) ---")
        for f in fallos:
            print(f"  {f}")
        print("\nQuién cita cada una:")
        for f in fallos:
            url = f.split(" -> ")[0].split("\n")[0]
            for origen in citas.get(url, []):
                print(f"  {origen}   {url}")
        print("\nAntes de tocar nada: comprueba la URL en un navegador. Un 403 o un timeout")
        print("puede ser el servidor rechazando una petición automática, no un enlace muerto.")
        print("Si la fuente se ha movido de verdad, actualiza la página que la cita y, si era")
        print("una URL con versión de docs.codabench.org, pasa también:")
        print("  python scripts/check_codabench.py")
        return 1

    print(f"\nOK: las {len(citas)} URLs externas responden.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
