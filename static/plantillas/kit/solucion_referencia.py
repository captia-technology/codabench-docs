#!/usr/bin/env python3
"""Solución de referencia: la más sencilla que tiene sentido, sin instalar nada.

Lee train.csv y test.csv de la carpeta que se le indique (por defecto, la actual)
y escribe submission.csv en la carpeta actual, listo para comprobar y comprimir.

Qué se predice lo dice config.json, junto a este fichero:
  - si es un número, la media de cada grupo a cada hora del día;
  - si es una clase, la clase más frecuente de cada grupo a cada hora.
Si los datos no tienen grupo o fecha, agrupa por lo que haya. Y cuando una
combinación no aparece en el entrenamiento, usa la media (o la clase más
frecuente) de todo train.csv.

Uso:  python solucion_referencia.py [carpeta_con_train_y_test]

Es un punto de partida: para mejorarla, cambia cómo se calcula `prediccion`.
"""

import csv
import json
import os
import re
import sys
from pathlib import Path

# La hora se lee tal como está escrita en la fecha: ISO 8601 («2026-02-10T08:15:00+01:00»)
# o día/mes/año («10/02/2026 8:15»), que es como la reescribe Excel en español.
RE_ISO = re.compile(
    r"^(\d{4})-(\d{2})-(\d{2})(?:[T ](\d{2}):(\d{2})(?::(\d{2})(?:[.,]\d+)?)?)?\s*(Z|[+-]\d{2}:?\d{2})?$"
)
RE_DMA = re.compile(r"^(\d{1,2})/(\d{1,2})/(\d{4})(?:[ T](\d{1,2}):(\d{2})(?::(\d{2}))?)?$")


def leer_config():
    with open(str(Path(__file__).resolve().parent / "config.json"), encoding="utf-8") as f:
        return json.load(f)


def hora_de(texto):
    """La hora del día (0-23) de una fecha, o None si no se puede leer."""
    m = RE_ISO.match(texto.strip()) or RE_DMA.match(texto.strip())
    if not m:
        return None
    return int(m.group(4)) if m.group(4) is not None else 0


def leer(ruta):
    with open(ruta, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def mas_frecuente(cuentas):
    """La clase más frecuente; en un empate, la primera en orden alfabético."""
    maximo = max(cuentas.values())
    return min(clase for clase, n in cuentas.items() if n == maximo)


def main():
    config = leer_config()
    columna, tipo, id_col = config["columna"], config["tipo"], config.get("id", "id")
    grupo, tiempo = config.get("grupo"), config.get("tiempo")
    carpeta = sys.argv[1] if len(sys.argv) > 1 else "."

    def clave(fila):
        return (fila[grupo] if grupo else None, hora_de(fila[tiempo]) if tiempo else None)

    entrenamiento = leer(os.path.join(carpeta, "train.csv"))
    if tipo == "numero":
        sumas, cuentas = {}, {}
        total = 0.0
        for fila in entrenamiento:
            valor = float(fila[columna])
            k = clave(fila)
            sumas[k] = sumas.get(k, 0.0) + valor
            cuentas[k] = cuentas.get(k, 0) + 1
            total += valor
        global_ = round(total / len(entrenamiento), 4)

        def prediccion(fila):
            k = clave(fila)
            return round(sumas[k] / cuentas[k], 4) if k in cuentas else global_

    else:
        por_clave, todas = {}, {}
        for fila in entrenamiento:
            valor = fila[columna]
            todas[valor] = todas.get(valor, 0) + 1
            cuentas_k = por_clave.setdefault(clave(fila), {})
            cuentas_k[valor] = cuentas_k.get(valor, 0) + 1
        global_ = mas_frecuente(todas)

        def prediccion(fila):
            k = clave(fila)
            return mas_frecuente(por_clave[k]) if k in por_clave else global_

    prueba = leer(os.path.join(carpeta, "test.csv"))
    with open("submission.csv", "w", newline="", encoding="utf-8") as f:
        escritor = csv.writer(f, lineterminator="\n")
        escritor.writerow([id_col, columna])
        for fila in prueba:
            escritor.writerow([fila[id_col], prediccion(fila)])
    print("submission.csv escrito: {} filas. Compruébalo con validar_envio.py".format(len(prueba)))


if __name__ == "__main__":
    main()
