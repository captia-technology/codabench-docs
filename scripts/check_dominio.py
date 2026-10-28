#!/usr/bin/env python3
"""Comprueba que la guia se sirve correctamente en su dominio.

    python scripts/check_dominio.py                      # contra el dominio de produccion
    python scripts/check_dominio.py --url https://otro   # contra cualquier otro destino

Sale con codigo 1 si algo falla. Pensado para pasarlo DESPUES de asignar el dominio en Vercel,
y para volver a pasarlo cada vez que se toque el dominio o la configuracion de `url`.

Que comprueba y por que
-----------------------
No basta con que la portada devuelva 200. Los tres fallos que de verdad rompen un sitio estatico
servido en un dominio nuevo son mas silenciosos:

1. **El `baseUrl` no coincide con la ruta en la que se sirve.** La pagina responde 200 y el HTML
   llega entero, pero el CSS y el JS se piden a una ruta que no existe. Se ve como texto sin
   estilos. Por eso aqui no se mira solo el HTML: se extraen los assets que la pagina declara y
   se piden uno a uno.
2. **La navegacion directa falla.** Entrar escribiendo una URL interna en la barra del navegador
   no es lo mismo que llegar a ella navegando: lo primero lo resuelve el servidor, lo segundo el
   router del navegador. Aqui se piden en frio.
3. **El canonical se quedo congelado.** Es texto incrustado en el HTML durante el build, asi que
   sobrevive a un cambio de dominio hasta que se vuelve a desplegar, y deja a Google apuntando al
   sitio antiguo.

Ademas se comprueba que ninguna ruta redirige a `*.vercel.app`: seria contenido duplicado y la
URL visible dejaria de ser la del dominio propio.

El sitio pide credencial
------------------------
Lo primero que se comprueba es lo contrario de todo lo anterior: que SIN credencial una pagina
lleva al formulario de `/acceso`, que el formulario se sirve, y que los assets devuelven 401
(`middleware.js`, ver `docs-meta/06-control-de-acceso.md`). Un 200 en una pagina es el fallo mas
grave que puede tener el sitio, y ningun otro control lo detecta.

Para el resto la comprobacion entra como un cliente mas, con dos variables de entorno:

    DOCS_CREDENCIAL                    usuario:contraseña de la entrada reservada al equipo
    VERCEL_AUTOMATION_BYPASS_SECRET    solo contra una preview, que ademas tiene Vercel
                                       Authentication delante

Nunca como argumentos: acabarian en el historial de la shell. Sin `DOCS_CREDENCIAL` solo se
comprueba que el sitio esta cerrado, y el resultado es FALLO porque el resto no se ha mirado.
"""

from __future__ import annotations

import argparse
import base64
import os
import re
import sys
import urllib.error
import urllib.request
from urllib.parse import urljoin, urlparse

# Mientras `docs.codabench.captia.ai` no resuelva, produccion vive en el dominio de Vercel. El dia
# que se asigne el subdominio, se cambia aqui: el canonical y el sitemap pasaran a declararlo.
DOMINIO_POR_DEFECTO = "https://codabench-docs.vercel.app"

# Muestra representativa: la portada, un indice de seccion, una pagina de cada tramo del recorrido
# y el mapa. No es exhaustiva a proposito —los enlaces los vigila el build con `onBrokenLinks`—,
# sino la minima que detecta un dominio mal montado.
RUTAS = [
    "/",
    "/empezar",
    "/competicion/details",
    "/recursos/scoring-program",
    "/evaluacion/leaderboards",
    "/mapa-de-la-guia",
]

RE_ASSET = re.compile(r'(?:href|src)="(/[^"]+\.(?:css|js|png|svg|woff2?))"')
RE_CANONICAL = re.compile(r'<link[^>]*rel="canonical"[^>]*href="([^"]+)"')


CREDENCIAL = os.environ.get("DOCS_CREDENCIAL", "")
BYPASS = os.environ.get("VERCEL_AUTOMATION_BYPASS_SECRET", "")


def cabeceras(con_credencial: bool) -> dict[str, str]:
    h = {"User-Agent": "check_dominio/1.0"}
    if BYPASS:
        h["x-vercel-protection-bypass"] = BYPASS
    if con_credencial and CREDENCIAL:
        h["Authorization"] = "Basic " + base64.b64encode(CREDENCIAL.encode("utf-8")).decode("ascii")
    return h


class _SinRedirecciones(urllib.request.HTTPRedirectHandler):
    """Sin credencial, la redireccion a /acceso ES la respuesta que se quiere ver."""

    def redirect_request(self, *args, **kwargs):
        return None


_abrir_sin_redirecciones = urllib.request.build_opener(_SinRedirecciones()).open


def sin_credencial(url: str, navegador: bool = False, timeout: int = 20) -> tuple[int, str, str]:
    """Pide sin credencial y sin seguir redirecciones. Devuelve (codigo, Location o error, cuerpo).

    `navegador` anuncia que se espera HTML, como al escribir la URL: es lo que distingue en el
    middleware una pagina (se redirige al formulario) de un asset (401).
    """
    h = cabeceras(con_credencial=False)
    if navegador:
        h["Accept"] = "text/html"
    try:
        with _abrir_sin_redirecciones(urllib.request.Request(url, headers=h), timeout=timeout) as r:
            return r.status, "", r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.headers.get("Location", ""), ""
    except Exception as e:  # DNS sin resolver, certificado, timeout
        return 0, f"{type(e).__name__}: {e}", ""


def pedir(url: str, timeout: int = 20) -> tuple[int, str, str]:
    """Devuelve (codigo, url_final, cuerpo). No sigue redirecciones en silencio."""
    peticion = urllib.request.Request(url, headers=cabeceras(con_credencial=True))
    try:
        with urllib.request.urlopen(peticion, timeout=timeout) as r:
            return r.status, r.geturl(), r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, url, ""
    except Exception as e:  # DNS sin resolver, certificado, timeout
        return 0, f"{type(e).__name__}: {e}", ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default=DOMINIO_POR_DEFECTO, help="base del sitio a comprobar")
    args = ap.parse_args()
    base = args.url.rstrip("/")
    host_esperado = urlparse(base).netloc

    fallos: list[str] = []
    print(f"comprobando {base}\n")

    # --- 0. Sin credencial no se sirve nada: las paginas llevan al formulario ---
    codigo, destino, _ = sin_credencial(base + "/", navegador=True)
    cerrado = codigo in (302, 303, 307) and destino.startswith("/acceso")
    print(f"  {'ok  ' if cerrado else 'FALLO'} {codigo or '---'}  / sin credencial (se espera ir a /acceso)")
    if codigo == 0:
        fallos.append(f"/: no se pudo conectar -> {destino}")
    elif codigo == 200:
        fallos.append("/ sin credencial devuelve 200: LA GUIA ESTA ABIERTA")
    elif not cerrado:
        fallos.append(f"/ sin credencial devuelve {codigo} -> {destino or 'sin Location'}, se esperaba ir a /acceso")

    codigo, _, cuerpo = sin_credencial(base + "/acceso", navegador=True)
    formulario = codigo == 200 and 'name="contrasena"' in cuerpo
    print(f"  {'ok  ' if formulario else 'FALLO'} {codigo or '---'}  /acceso sirve el formulario")
    if codigo and not formulario:
        fallos.append(f"/acceso devuelve {codigo} sin formulario: nadie podria entrar")

    if not CREDENCIAL:
        print("\nSin DOCS_CREDENCIAL solo se puede comprobar que el sitio esta cerrado.")
        fallos.append("falta DOCS_CREDENCIAL: paginas, assets, canonical y sitemap sin comprobar")
        for f in fallos:
            print(f"FALLO  {f}")
        return 1
    print()

    # --- 1. Las paginas responden, en frio y sin redirigir fuera del dominio ---
    cuerpos: dict[str, str] = {}
    for ruta in RUTAS:
        codigo, final, cuerpo = pedir(base + ruta)
        host_final = urlparse(final).netloc if codigo else ""
        marca = "ok  " if codigo == 200 else "FALLO"
        print(f"  {marca} {codigo or '---'}  {ruta}")
        if codigo == 0:
            fallos.append(f"{ruta}: no se pudo conectar -> {final}")
            continue
        if codigo != 200:
            fallos.append(f"{ruta}: devuelve {codigo}, se esperaba 200")
            continue
        if host_final and host_final != host_esperado:
            fallos.append(f"{ruta}: acaba en otro host -> {host_final}")
        if "vercel.app" in host_final and "vercel.app" not in host_esperado:
            fallos.append(f"{ruta}: redirige a vercel.app, la URL visible cambiaria")
        cuerpos[ruta] = cuerpo

    if not cuerpos:
        print("\nNo respondio ninguna pagina: el dominio no esta operativo todavia.")
        for f in fallos:
            print(f"FALLO  {f}")
        return 1

    # --- 2. Los assets que declara la portada existen de verdad ---
    portada = cuerpos.get("/", "")
    assets = sorted(set(RE_ASSET.findall(portada)))[:12]
    print(f"\n  assets declarados por la portada: {len(set(RE_ASSET.findall(portada)))}"
          f" (se comprueban {len(assets)})")
    for a in assets:
        codigo, _, _ = pedir(urljoin(base, a))
        if codigo != 200:
            fallos.append(f"asset {a}: devuelve {codigo}")
            print(f"  FALLO {codigo}  {a}")
    if not assets:
        fallos.append("la portada no declara ningun asset; ¿HTML incompleto?")

    css = [a for a in assets if a.endswith(".css")]
    js = [a for a in assets if a.endswith(".js")]
    if not css:
        fallos.append("la portada no carga ninguna hoja de estilos")
    if not js:
        fallos.append("la portada no carga ningun script")

    # Y esos mismos assets, sin credencial, tampoco se sirven: los chunks de JS llevan el texto
    # de las paginas, asi que un `matcher` que excluyera los estaticos abriria la guia entera.
    imagenes = [a for a in assets if a.endswith((".png", ".svg"))]
    muestra = js[:1] + imagenes[:1]
    cerrados = 0
    for a in muestra:
        codigo, _, _ = sin_credencial(urljoin(base, a))
        if codigo == 401:
            cerrados += 1
        else:
            fallos.append(f"asset {a} sin credencial devuelve {codigo}, se esperaba 401")
            print(f"  FALLO {codigo}  {a} sin credencial")
    print(f"  sin credencial: {cerrados} de {len(muestra)} assets devuelven 401")

    # --- 3. El canonical declara el dominio esperado ---
    print()
    canonicos_ok = 0
    for ruta, cuerpo in cuerpos.items():
        m = RE_CANONICAL.search(cuerpo)
        if not m:
            fallos.append(f"{ruta}: sin <link rel=canonical>")
            print(f"  FALLO {ruta}: sin canonical")
            continue
        host_canonico = urlparse(m.group(1)).netloc
        if host_canonico == host_esperado:
            canonicos_ok += 1
        else:
            fallos.append(f"{ruta}: canonical apunta a {host_canonico}, no a {host_esperado}")
            print(f"  FALLO canonical de {ruta} -> {m.group(1)}")
    print(f"  canonical: {canonicos_ok} de {len(cuerpos)} apuntan a {host_esperado}")

    # --- 4. El sitemap declara el dominio esperado ---
    codigo, _, sitemap = pedir(base + "/sitemap.xml")
    if codigo != 200:
        fallos.append(f"/sitemap.xml devuelve {codigo}")
    else:
        urls = re.findall(r"<loc>([^<]+)</loc>", sitemap)
        malas = [u for u in urls if urlparse(u).netloc != host_esperado]
        print(f"  sitemap  : {len(urls)} URLs, {len(malas)} fuera de {host_esperado}")
        if malas:
            fallos.append(f"el sitemap declara {len(malas)} URLs de otro host, p.ej. {malas[0]}")

    print()
    for f in fallos:
        print(f"FALLO  {f}")
    if not fallos:
        print(f"OK: la guia se sirve correctamente en {base}")
    return 1 if fallos else 0


if __name__ == "__main__":
    raise SystemExit(main())
