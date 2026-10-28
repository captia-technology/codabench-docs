#!/usr/bin/env python3
"""Genera la credencial con la que un cliente entra a la guía, y valida la lista de accesos.

    python scripts/credencial_cliente.py cliente-ejemplo   # contraseña nueva y su entrada
    python scripts/credencial_cliente.py --check           # valida DOCS_ACCESOS antes de pegarla
    python scripts/credencial_cliente.py --secreto         # valor nuevo para DOCS_SESION_SECRETO

Cómo encaja
-----------
La guía pide usuario y contraseña (`middleware.js`). La lista de quién entra es la variable
`DOCS_ACCESOS` del proyecto en Vercel: una entrada `usuario:hash` por cliente. Este script cubre
las dos cosas que se hacen a mano y en las que es fácil equivocarse:

1. **Dar de alta o rotar**: genera una contraseña aleatoria y la entrada que hay que añadir a la
   variable. La contraseña se imprime UNA vez y no se guarda en ningún sitio; si se pierde, se
   genera otra.
2. **`--check`**: valida el valor de `DOCS_ACCESOS` antes de pegarlo en Vercel. Una entrada mal
   formada no rompe el despliegue: el middleware la ignora, y ese cliente se queda fuera sin más
   aviso que una línea en los logs de Vercel.

Por qué un hash y no la contraseña
----------------------------------
Quien pueda leer las variables del proyecto en Vercel no debe poder entrar a la guía con lo que
lee. El hash es `sha256("usuario:contraseña")`: el usuario hace de sal, así que dos clientes con
la misma contraseña no comparten hash. No hace falta un hash lento (bcrypt, scrypt) porque las
contraseñas no las elige nadie: salen de aquí con unos 124 bits de azar.

Es el mismo script que el del manual de captia.ai (`my-qa-captia-ai-app`), y una entrada vale
igual en los dos: el hash no depende del sitio, así que la misma lista sirve a ambos proyectos.

El procedimiento completo —dónde se pega, por qué hay que redesplegar— está en
`docs-meta/06-control-de-acceso.md`.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import secrets
import sys

# Lo mismo que acepta `middleware.js`. Si cambia uno, cambia el otro.
RE_USUARIO = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")
RE_ENTRADA = re.compile(r"^([a-z0-9][a-z0-9._-]*):([0-9a-f]{64})$")

# Sin i, l, o, 0 ni 1: la contraseña se dicta y se copia a mano, y esos se confunden.
# 31 símbolos x 25 posiciones = 124 bits.
ALFABETO = "abcdefghjkmnpqrstuvwxyz23456789"
SECRETO_MINIMO = 32  # el mismo mínimo que exige el middleware
GRUPOS, LARGO_GRUPO = 5, 5


def generar_contrasena() -> str:
    return "-".join(
        "".join(secrets.choice(ALFABETO) for _ in range(LARGO_GRUPO)) for _ in range(GRUPOS)
    )


def entrada(usuario: str, contrasena: str) -> str:
    """La línea de `DOCS_ACCESOS`. El middleware calcula lo mismo con lo que llega del navegador."""
    digest = hashlib.sha256(f"{usuario}:{contrasena}".encode("utf-8")).hexdigest()
    return f"{usuario}:{digest}"


def alta(usuario: str) -> int:
    usuario = usuario.strip().lower()
    if not RE_USUARIO.match(usuario):
        print(
            f"usuario no válido: {usuario!r}. Minúsculas, cifras, '.', '_' o '-', empezando por"
            " letra o cifra, hasta 64 caracteres.",
            file=sys.stderr,
        )
        return 1
    contrasena = generar_contrasena()
    print(f"usuario     {usuario}")
    print(f"contraseña  {contrasena}")
    print()
    print("Entrada para DOCS_ACCESOS (añádela tras una coma; si el usuario ya existía, sustituye la suya):")
    print(entrada(usuario, contrasena))
    print()
    print("La contraseña no se guarda en ningún sitio. Envíala por un canal distinto del de la URL.")
    print("La entrada no surte efecto hasta que se redespliega producción.")
    return 0


def check() -> int:
    valor = os.environ.get("DOCS_ACCESOS")
    if valor is None:
        print(
            "Define DOCS_ACCESOS con el valor a validar, p. ej. en PowerShell:\n"
            "  $env:DOCS_ACCESOS = Get-Content accesos.txt -Raw; python scripts/credencial_cliente.py --check",
            file=sys.stderr,
        )
        return 1

    fallos: list[str] = []
    usuarios: list[str] = []
    for n, linea in enumerate(valor.splitlines(), 1):
        for item in (x for x in re.split(r"[\s,]+", linea) if x):
            m = RE_ENTRADA.match(item)
            if not m:
                # Nunca el texto: si lo pegado era una contraseña —la línea que imprime el alta, o
                # `usuario:contraseña`—, no debe acabar en pantalla. Solo el usuario, si lo parece.
                usuario, dos_puntos, _ = item.partition(":")
                if dos_puntos and RE_USUARIO.match(usuario):
                    fallos.append(
                        f"línea {n}: la entrada de {usuario} está mal formada y el middleware la"
                        " ignorará. Tras los dos puntos va el hash de 64 caracteres que imprime el alta"
                    )
                else:
                    fallos.append(
                        f"línea {n}: hay texto que no es una entrada usuario:hash y el middleware lo"
                        " ignorará. No se muestra por si fuera una contraseña"
                    )
                continue
            if m.group(1) in usuarios:
                fallos.append(f"usuario repetido, solo valdría la última entrada: {m.group(1)}")
            usuarios.append(m.group(1))

    if not usuarios:
        fallos.append("ninguna entrada válida: con este valor no entraría nadie")

    secreto = os.environ.get("DOCS_SESION_SECRETO")
    if secreto is not None and len(secreto) < SECRETO_MINIMO:
        fallos.append(f"DOCS_SESION_SECRETO tiene menos de {SECRETO_MINIMO} caracteres: el formulario no abriría sesiones")

    print(f"{len(set(usuarios))} accesos válidos: {', '.join(sorted(set(usuarios))) or '—'}")
    for f in dict.fromkeys(fallos):  # una línea con dos trozos malos daría el mismo aviso dos veces
        print(f"FALLO  {f}")
    return 1 if fallos else 0


def secreto() -> int:
    print(secrets.token_urlsafe(48))
    print()
    print("Valor para DOCS_SESION_SECRETO. Firma las cookies de sesión: cambiarlo cierra la sesión")
    print("de todos los clientes, que tendrán que volver a entrar. En Vercel, de tipo Secret.")
    return 0


def main() -> int:
    # Como en release_docs.py: la consola de Windows es cp1252 y la salida lleva tildes y eñes.
    for flujo in (sys.stdout, sys.stderr):
        if hasattr(flujo, "reconfigure"):
            flujo.reconfigure(encoding="utf-8", errors="replace")

    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("usuario", nargs="?", help="identificador del cliente, p. ej. cliente-ejemplo")
    ap.add_argument("--check", action="store_true", help="valida la variable DOCS_ACCESOS")
    ap.add_argument("--secreto", action="store_true", help="genera un valor para DOCS_SESION_SECRETO")
    args = ap.parse_args()
    if args.check:
        return check()
    if args.secreto:
        return secreto()
    if not args.usuario:
        ap.error("falta el usuario (o --check, o --secreto)")
    return alta(args.usuario)


if __name__ == "__main__":
    raise SystemExit(main())
