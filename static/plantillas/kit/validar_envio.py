#!/usr/bin/env python3
"""Comprueba un envío antes de subirlo, con las mismas reglas que el programa de puntuación.

Mira que el CSV esté en UTF-8 y separado por comas, que tenga las columnas que
pide config.json, que no repita ids, que haya una fila por cada id de test.csv
y, si se predice un número, que todos los valores lo sean.

Uso:  python validar_envio.py submission.csv test.csv
"""

import csv
import io
import json
import math
import re
import sys
from pathlib import Path

RE_NUMERO = re.compile(r"^[+-]?(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?$")


def fallo(mensaje):
    sys.exit("ERROR: " + mensaje)


def leer(ruta):
    """Las filas de un CSV, comprobando antes la codificación y el separador."""
    try:
        with open(ruta, "rb") as f:
            texto = f.read().decode("utf-8-sig")
    except FileNotFoundError:
        fallo("no existe {}".format(ruta))
    except UnicodeDecodeError:
        fallo("{} no está en UTF-8. Guárdalo como «CSV UTF-8 (delimitado por comas)»".format(ruta))
    cabecera = texto.split("\n", 1)[0]
    if "," not in cabecera and ";" in cabecera:
        fallo("{} separa las columnas con punto y coma; tiene que ir con comas".format(ruta))
    lector = csv.DictReader(io.StringIO(texto, newline=""))
    lector.fieldnames = [c.strip() for c in (lector.fieldnames or [])]
    return lector.fieldnames, list(lector)


def main():
    if len(sys.argv) != 3:
        sys.exit("Uso: python validar_envio.py submission.csv test.csv")
    with open(str(Path(__file__).resolve().parent / "config.json"), encoding="utf-8") as f:
        config = json.load(f)
    columna, tipo, id_col = config["columna"], config["tipo"], config.get("id", "id")

    _, prueba = leer(sys.argv[2])
    esperados = set(fila[id_col].strip() for fila in prueba)

    columnas, envio = leer(sys.argv[1])
    for falta in (id_col, columna):
        if falta not in columnas:
            fallo("falta la columna '{}'. Tiene que haber exactamente estas dos: {},{}".format(falta, id_col, columna))
    otras = [c for c in columnas if c not in (id_col, columna)]

    vistos = set()
    for linea, fila in enumerate(envio, start=2):
        clave = (fila[id_col] or "").strip()
        valor = (fila[columna] or "").strip()
        if not clave:
            fallo("línea {}: la fila no tiene id".format(linea))
        if clave in vistos:
            fallo("línea {}: el id {} está repetido".format(linea, clave))
        vistos.add(clave)
        if not valor:
            fallo("línea {}: falta la predicción para {}".format(linea, clave))
        if tipo == "numero":
            if not RE_NUMERO.match(valor) or math.isinf(float(valor)):
                fallo("línea {}: '{}' no es un número (los decimales van con punto)".format(linea, valor))

    faltan, sobran = esperados - vistos, vistos - esperados
    if faltan:
        fallo("faltan {} ids de test.csv (por ejemplo: {})".format(len(faltan), ", ".join(sorted(faltan)[:3])))
    if sobran:
        fallo("sobran {} ids que no están en test.csv (por ejemplo: {})".format(len(sobran), ", ".join(sorted(sobran)[:3])))
    if otras:
        print("Aviso: las columnas {} no se usan para puntuar.".format(", ".join(otras)))
    print("OK: {} filas. Ya puedes comprimirlo con hacer_envio_zip.py".format(len(vistos)))


if __name__ == "__main__":
    main()
