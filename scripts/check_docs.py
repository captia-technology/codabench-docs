#!/usr/bin/env python3
"""Comprueba las invariantes de `docs/`. Pensado para correr en cada PR.

    python scripts/check_docs.py          # informe completo
    python scripts/check_docs.py -q       # solo lo que falla

Sale con código 1 si falla alguna comprobación BLOQUEANTE. Las comprobaciones marcadas
como AVISO informan pero no rompen: señalan calidad editorial, no algo que deje el sitio
publicado en mal estado.

Relación con las otras dos piezas
--------------------------------
Las invariantes están escritas tres veces, y las tres tienen que decir lo mismo:

- `.claude/hooks/validar_doc.py` valida UN documento en el momento de escribirlo, y solo con
  lo que se puede saber mirando ese fichero (front matter, H1, imágenes, datos personales).
- este script valida el ÁRBOL entero: además de lo anterior, resuelve cada enlace y cada
  imagen contra el sistema de ficheros y busca imágenes que no use nadie.
- `.claude/rules/documentacion.md` se las explica a quien escribe.

Los patrones de la invariante 8 (correos, IPs, credenciales, lista privada) son literalmente
los mismos que los del hook. Si divergen, un documento pasaría el hook y caería en CI —o al
revés—, que es la peor forma de tener dos validadores.

Lo que NO comprueba este script
-------------------------------
La invariante 10 (todo documento declarado en `SECCIONES`, y en la raíz de `docs/` solo la
portada y el mapa) la comprueba `scripts/build_nav.py --check`, que es quien tiene la
declaración de la navegación delante. Ambos corren en CI.
"""

from __future__ import annotations

import argparse
import io
import re
import sys
import unicodedata
from pathlib import Path

# El informe está en español y lleva tildes, comillas angulares y rayas. En Linux (el CI) la
# salida ya es UTF-8, pero la consola de Windows —donde se escribe la documentación— arranca
# con la página de códigos del sistema: en cp1252 el texto sale ilegible y en cp850 un `—`
# revienta el print con UnicodeEncodeError. Perder el informe justo cuando alguien intenta leer
# por qué ha fallado algo es el peor momento posible, así que se fuerza UTF-8.
for _flujo in (sys.stdout, sys.stderr):
    try:
        _flujo.reconfigure(encoding="utf-8")
    except (AttributeError, OSError, ValueError):
        pass

REPO = Path(__file__).resolve().parent.parent
DOCS = REPO / "docs"

RE_MD_IMG = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
RE_MD_LINK = re.compile(r"(?<!!)\[[^\]]*\]\(([^)]+)\)")
RE_HTML_IMG = re.compile(r"<img[^>]*>")
RE_H1 = re.compile(r"^# (?!#)", re.MULTILINE)
RE_H1_TEXTO = re.compile(r"^#\s+(?P<t>.+?)\s*$", re.MULTILINE)
RE_FRONTMATTER = re.compile(r"\A---\s*\n")
RE_FM_BLOQUE = re.compile(r"\A---\s*\n(?P<fm>.*?)\n---\s*\n", re.S)
RE_FM_TITLE = re.compile(r'^title:\s*"?(?P<t>.*?)"?\s*$', re.M)
# El mismo rango que usa scripts/add_frontmatter.py al generar el título.
RE_EMOJI = re.compile("[\U0001f300-\U0001faff☀-➿️‍⏱⏲⌛⌚]+")
# El rótulo de la invariante 11, tal cual: negrita, dos puntos dentro de la negrita.
RE_OBJETIVO = re.compile(r"^\*\*Objetivo:\*\*", re.M)

# --- Invariante 8, los patrones ---------------------------------------------------------
# Copiados literalmente de .claude/hooks/validar_doc.py. No los toques aquí sin tocarlos allí.
RE_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
RE_IP = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
# Credenciales. El sitio es público y esta guía habla de subir recursos a una plataforma: un
# token pegado en un ejemplo se publica igual que el resto del texto.
RE_SECRETO = re.compile(
    r"(?:api[_-]?key|secret|password|passwd|authorization)\s*[:=]\s*\S+"
    r"|Bearer\s+[A-Za-z0-9._~+/-]{16,}",
    re.I,
)
DOMINIOS_DEMO = ("ejemplo.com", "example.com")


def es_demo(correo: str) -> bool:
    """¿El correo pertenece a un dominio de ejemplo?

    Se compara el DOMINIO, no el sufijo de la cadena. Con `endswith` sobre el correo entero,
    `alguien@malejemplo.com` y `soporte@miejemplo.com` pasaban por demo: son dominios reales
    que terminan en «ejemplo.com». El fallo se cuela hacia el lado caro —un correo de verdad
    publicado— y no hacia el falso positivo.
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

# Documentos que no llevan el rótulo `**Objetivo:**` porque no son páginas de procedimiento:
# la portada es una composición de componentes y el mapa lo genera build_nav.py.
SIN_OBJETIVO = {"index.mdx", "mapa-de-la-guia.md"}

# Extensiones que cuentan como imagen para la invariante 9 (ninguna huérfana). Se listan
# todas las que Docusaurus sabe empaquetar, y no solo `.png`, porque una captura en `.webp`
# olvidada pesa y confunde exactamente igual que una en `.png`.
EXT_IMAGEN = (".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".avif")


def privados() -> list[str]:
    """Identificadores que no deben publicarse, si el equipo mantiene la lista.

    `scripts/privados.txt` no se versiona (ver `.gitignore`): el repositorio es privado pero el
    sitio no, y una lista de nombres de cliente dentro del repo sería justo el dato que se
    quiere proteger. Una línea por identificador; `#` comenta.

    Sin el fichero la comprobación no se salta: simplemente no hay nada que buscar, y el resto
    de la invariante 8 (correos, IPs, credenciales) sigue en pie.
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


def no_es_ascii(nombre: str) -> bool:
    """¿El nombre lleva algún carácter fuera de ASCII?

    Misma expresión que usa el hook, a propósito: normaliza en NFKD y descarta lo que no
    sobrevive a ASCII. Si algo cambió, el nombre traía tildes, comillas tipográficas o rayas.
    """
    return nombre != unicodedata.normalize("NFKD", nombre).encode("ascii", "ignore").decode()


def columnas(linea: str) -> int:
    """Celdas que Markdown ve en una fila de tabla.

    El pipe escapado (`\\|`) NO separa; el que va dentro de `código` SÍ separa, que es
    justo lo que rompe las tablas sin avisar.
    """
    s = linea.strip().replace("\\|", "\x00")
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return len(s.split("|"))


def filas_descuadradas(texto: str) -> list[tuple[int, int, int, str]]:
    """Filas de tabla cuyo número de celdas no coincide con el de su cabecera."""
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


def read(p: Path) -> str:
    return io.open(p, encoding="utf-8").read()


def existe_exacto(destino: Path) -> tuple[bool, str]:
    """¿Existe el fichero con ESA caja exacta?

    `Path.is_file()` no sirve: en Windows —donde se escribe— el sistema de ficheros es
    insensible a mayúsculas y da por bueno un enlace a `Phases.md` cuando el fichero se llama
    `phases.md`. En Linux —donde corre el CI y donde compila Docusaurus— eso es un enlace
    roto, y el fallo aparece en el despliegue y no en el portátil de quien lo escribió. Se
    comprueba contra el listado real del directorio.
    """
    padre = destino.parent
    if not padre.is_dir():
        return False, "el directorio no existe"
    nombres = {p.name for p in padre.iterdir()}
    if destino.name in nombres:
        return True, ""
    parecidos = [n for n in nombres if n.lower() == destino.name.lower()]
    if parecidos:
        return False, f"error de mayúsculas, el fichero real es '{parecidos[0]}'"
    return False, "no existe"


def main() -> int:
    ap = argparse.ArgumentParser(description="Comprueba las invariantes de docs/.")
    ap.add_argument("-q", "--quiet", action="store_true", help="solo mostrar fallos")
    args = ap.parse_args()

    if not DOCS.is_dir():
        print(f"FALLO  no existe {DOCS.relative_to(REPO).as_posix()}/")
        return 1

    # `.mdx` también: la portada es MDX y sin esto se quedaría fuera de TODAS las
    # comprobaciones, incluida la de datos personales, que es la que no puede fallar.
    mds = sorted(list(DOCS.rglob("*.md")) + list(DOCS.rglob("*.mdx")))
    imagenes = sorted(p for p in DOCS.rglob("*") if p.suffix.lower() in EXT_IMAGEN)
    identificadores = privados()
    fallos: list[str] = []
    avisos: list[str] = []
    usadas: set[Path] = set()

    # BLOQUEANTE (invariante 7) — rutas ASCII y en minúscula, ficheros Y carpetas.
    #
    # Docusaurus construye la URL desde la ruta del fichero: `docs/Evaluación/Phases.md` se
    # publica en `/Evaluaci%C3%B3n/Phases`. Aquí se prohíbe de entrada en vez de exigir un
    # `slug` transliterado como hace el manual de captia.ai, porque allí hay rutas heredadas
    # que respetar y aquí no hay ninguna: el árbol se está creando ahora. Una sola excepción
    # obliga a recordar cuál de las dos convenciones toca al escribir el siguiente enlace, y
    # los enlaces que se equivocan devuelven 404 sin que el build diga nada.
    #
    # Se recorre el árbol entero y no solo los `.md`: una captura llamada `Details.png` da el
    # mismo problema en la URL del asset, y `_category_.json` (que genera build_nav.py) es la
    # única excepción legítima, por ser un nombre que impone Docusaurus.
    for p in sorted(DOCS.rglob("*")):
        nombre = p.name
        if nombre == "_category_.json":
            continue
        rel = p.relative_to(REPO).as_posix()
        que = "la carpeta" if p.is_dir() else "el fichero"
        if no_es_ascii(nombre):
            fallos.append(
                f"{rel}: {que} tiene caracteres no ASCII; su URL saldría percent-encoded. "
                f"Renómbralo transliterado y en minúscula"
            )
        if nombre != nombre.lower():
            fallos.append(
                f"{rel}: {que} tiene mayúsculas; bajo docs/ las rutas van en minúscula, y una "
                f"sola excepción parte el sitio en dos convenciones de URL"
            )

    for md in mds:
        rel = md.relative_to(REPO).as_posix()
        text = read(md)

        # BLOQUEANTE (invariante 4) — URLs efímeras de GitHub. Caducan y exigen sesión
        # iniciada: en el sitio publicado no se ve nada.
        if "user-attachments" in text:
            fallos.append(f"{rel}: referencia a github.com/user-attachments")

        # BLOQUEANTE (invariante 4) — Docusaurus NO resuelve rutas relativas en <img> JSX;
        # solo las de la sintaxis markdown se convierten a require(). Un <img src="./x.png">
        # compila sin quejarse y da una imagen rota en el sitio publicado.
        for tag in RE_HTML_IMG.findall(text):
            fallos.append(f"{rel}: <img> en crudo (usa ![alt](./fichero.png)) -> {tag[:60]}")

        # BLOQUEANTE (invariante 4) — toda imagen referenciada debe existir y ser local.
        for ref in RE_MD_IMG.findall(text):
            if ref.startswith(("http://", "https://")):
                fallos.append(
                    f"{rel}: imagen remota {ref[:60]} -> co-ubícala junto al .md; una URL "
                    f"ajena puede cambiar o desaparecer sin que nos enteremos"
                )
                continue
            if ref.startswith("../") or ref.startswith("/"):
                # La invariante 4 pide co-ubicación, y no es manía: una imagen en un
                # directorio central resuelve igual pero deja de viajar con su documento.
                # El día que la página se mueve de sección, el `../` apunta a otro sitio y la
                # imagen se rompe en producción sin que el build diga nada.
                fallos.append(
                    f"{rel}: imagen fuera de la carpeta del documento -> {ref} "
                    f"(co-ubícala junto al .md)"
                )
                continue
            destino = md.parent / ref.split("#")[0]
            ok, motivo = existe_exacto(destino)
            if ok:
                usadas.add(destino.resolve())
            else:
                fallos.append(f"{rel}: imagen inexistente -> {ref} ({motivo})")

        # BLOQUEANTE (invariante 5) — todo enlace relativo a otro documento debe resolver.
        # También los `.mdx`: la portada lo es, y un enlace a `../index.mdx` se rompe igual.
        for ref in RE_MD_LINK.findall(text):
            if ref.startswith(("http://", "https://", "#", "mailto:", "/")):
                continue
            if not ref.split("#")[0].endswith((".md", ".mdx")):
                continue
            ok, motivo = existe_exacto(md.parent / ref.split("#")[0])
            if not ok:
                fallos.append(f"{rel}: enlace roto -> {ref} ({motivo})")

        # BLOQUEANTE (invariante 8) — nada publicable que identifique a nadie.
        #
        # El repositorio es privado; el sitio, público. Todo lo que entre aquí sale publicado,
        # y una vez publicado ya está indexado. Los patrones son los del hook, letra por letra.
        for m in RE_EMAIL.finditer(text):
            if not es_demo(m.group(0)):
                fallos.append(f"{rel}: correo no demo -> {m.group(0)} (usa @ejemplo.com)")
        for m in RE_IP.finditer(text):
            if m.group(0) not in IPS_DOC:
                fallos.append(f"{rel}: dirección IP -> {m.group(0)}")
        for m in RE_SECRETO.finditer(text):
            fallos.append(f"{rel}: parece una credencial -> {m.group(0)[:40]}...")
        for m in RE_URL_CODABENCH.finditer(text):
            if m.group(1).lower() not in HOSTS_CODABENCH:
                fallos.append(
                    f"{rel}: URL de una instancia de Codabench que no es la pública "
                    f"-> {m.group(0)[:60]} (enlaza a www.codabench.org o docs.codabench.org)"
                )
        for ident in identificadores:
            if re.search(re.escape(ident), text, re.I):
                fallos.append(
                    f"{rel}: menciona un identificador de scripts/privados.txt "
                    f"-> {ident[:24]}..."
                )

        # BLOQUEANTE (invariante 2) — un solo H1 por página.
        # Varios H1 rompen la jerarquía de encabezados para lectores de pantalla, y además
        # dejan media página fuera del índice lateral: el TOC de Docusaurus arranca en H2, así
        # que una sección escrita con `#` no aparece en él. Lo arregla
        # scripts/normalize_headings.py.
        n_h1 = len(RE_H1.findall(text))
        if n_h1 > 1:
            fallos.append(
                f"{rel}: {n_h1} encabezados H1 (debe haber 1; usa scripts/normalize_headings.py)"
            )
        elif n_h1 == 0 and md.suffix.lower() == ".md":
            # La invariante dice UN H1, no «como mucho uno». Sin H1, Docusaurus pinta el
            # `title` del front matter como encabezado y la página se ve bien, así que el
            # defecto es invisible; pero la comprobación de abajo se queda sin nada que
            # cotejar y un `title` equivocado deja de detectarse. La portada es `.mdx` y
            # queda fuera a propósito: su encabezado lo pone el componente de portada.
            fallos.append(
                f"{rel}: sin encabezado H1. El `title` del front matter se queda sin nada "
                f"con lo que contrastarse"
            )

        # BLOQUEANTE (invariantes 1 y 3) — front matter con `title`, y ese `title` diciendo lo
        # mismo que el H1.
        #
        # No es cosmético: el `title` es lo que sale en la pestaña del navegador, en las migas
        # de pan y en los resultados del buscador, mientras que el H1 es lo que se lee en la
        # página. Cuando se separan, el lector busca una cosa y encuentra otra. El riesgo
        # concreto aquí es el copiar-pegar: estas páginas nacen troceando un documento, y una
        # página creada a partir de su vecina hereda el `title` de la vecina.
        bloque = RE_FM_BLOQUE.match(text)
        if not RE_FRONTMATTER.match(text):
            fallos.append(
                f"{rel}: sin front matter; hace falta al menos `title` "
                f"(lo genera scripts/build_nav.py --apply)"
            )
        elif not bloque:
            fallos.append(f"{rel}: front matter abierto y sin cerrar con `---`")
        else:
            mt = RE_FM_TITLE.search(bloque.group("fm"))
            if not mt:
                fallos.append(f"{rel}: el front matter no declara `title`")
            else:
                mh = RE_H1_TEXTO.search(text[bloque.end():])
                if mh:
                    h1 = RE_EMOJI.sub("", mh.group("t")).strip().strip("–-—").strip()
                    if mt.group("t").strip() != h1:
                        fallos.append(
                            f"{rel}: el title del front matter no coincide con el H1 "
                            f"-> title={mt.group('t')!r} vs H1={h1!r}"
                        )
                if RE_EMOJI.search(mt.group("t")):
                    fallos.append(
                        f"{rel}: el title del front matter lleva emoji -> {mt.group('t')!r}"
                    )

        # BLOQUEANTE (invariante 6) — toda fila de tabla debe tener las celdas de su cabecera.
        #
        # Buena parte de esta guía son tablas —inventarios de campos de la UI, errores y su
        # causa— y una fila descuadrada NO rompe el build: Markdown la renderiza igual,
        # recortando o inventando celdas en silencio, y el lector se encuentra una descripción
        # cortada a media frase.
        #
        # La causa típica no es un error de tecleo, sino una regla poco conocida de GFM: un
        # pipe dentro de `código` SEPARA CELDAS igual que uno suelto, y hay que escribirlo
        # `\|`. En una guía que documenta comandos y rutas de ficheros eso aparece solo: basta
        # una celda que muestre `a|b` para que la fila entera pierda su última columna.
        for n_linea, esperadas, hay, contenido in filas_descuadradas(text):
            fallos.append(
                f"{rel}:{n_linea}: fila de tabla con {hay} celdas y cabecera de {esperadas} "
                f"-> {contenido[:60]}... (¿un `|` sin escapar? dentro de `código` también "
                f"separa: escríbelo `\\|`)"
            )

        # AVISO (invariante 11) — el rótulo `**Objetivo:**`.
        #
        # De su primera frase sale la `description` del front matter, igual que en el manual de
        # captia.ai sale de «**Objetivo Principal:**». Va como AVISO y no como fallo a
        # propósito: que falte es una página peor escrita y una `description` que build_nav.py
        # no puede rellenar, no un sitio roto, y tumbar el CI por una cuestión editorial acaba
        # enseñando a saltarse el CI.
        if md.name not in SIN_OBJETIVO and not RE_OBJETIVO.search(text):
            avisos.append(
                f"{rel}: sin el rótulo `**Objetivo:**` al principio del cuerpo; build_nav.py "
                f"no tiene de dónde sacar la `description`"
            )

    # BLOQUEANTE (invariante 9) — imágenes en docs/ que ningún documento referencia.
    # Una captura huérfana es casi siempre el resto de una pantalla que ya se rehízo: pesa en
    # el repositorio, se queda desactualizada y algún día alguien la enlaza creyéndola vigente.
    for img in imagenes:
        if img.resolve() not in usadas:
            fallos.append(f"{img.relative_to(REPO).as_posix()}: imagen huérfana, nadie la usa")

    if not args.quiet:
        print(f"documentos       : {len(mds)}")
        print(f"imágenes en docs/: {len(imagenes)}  (referenciadas: {len(usadas)})")
        print(f"lista privada    : {len(identificadores)} identificador(es)"
              f"{'' if identificadores else ' (scripts/privados.txt no existe)'}")
        print(f"avisos           : {len(avisos)}")
        print()

    for f in fallos:
        print(f"FALLO  {f}")
    if not fallos:
        print("OK: todas las comprobaciones bloqueantes pasan")
    if avisos and not args.quiet:
        print(f"\nAVISOS ({len(avisos)}), no bloquean:")
        for a in avisos:
            print(f"  {a}")

    return 1 if fallos else 0


if __name__ == "__main__":
    raise SystemExit(main())
