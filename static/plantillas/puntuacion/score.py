#!/usr/bin/env python3
"""Programa de puntuación genérico para competiciones de Codabench.

Compara el envío del participante con la solución, fila a fila por su id, y
escribe scores.json. Qué columna se compara y cómo se puntúa no está en el
código: lo dice config.json, que va en el mismo zip que este fichero.

    {"columna": "personas", "tipo": "numero"}       # regresión: mae, rmse, n
    {"columna": "clase", "tipo": "categoria"}      # clasificación: aciertos, f1, n
    {"columna": "...", "tipo": "...", "id": "id"}   # "id" es opcional; por defecto, "id"

Claves de scores.json, que son las Column Key del leaderboard:
  numero     mae   error absoluto medio (menor es mejor)
             rmse  raíz del error cuadrático medio (menor es mejor)
  categoria  aciertos  proporción de filas acertadas, de 0 a 1 (mayor es mejor)
             f1        F1 macro sobre las clases que hay en la solución (mayor es mejor)
  los dos    n     filas evaluadas

Solo usa la biblioteca estándar y es compatible con Python 3.7, la versión de la
imagen por defecto de Codabench: no hay nada que instalar.

Uso en Codabench (fichero metadata):  python3 $program/score.py $input $output
Uso a mano:                           python3 score.py <entrada> <salida>
    <entrada>/ref/  la solución (reference_data)
    <entrada>/res/  el envío del participante
"""

import csv
import io
import json
import math
import os
import re
import sys
from pathlib import Path

TIPOS = ("numero", "categoria")

# Lo que se acepta como número. Es más estricto que float(), que también admite
# «1_000», «inf» o «nan», y es el mismo patrón que usa la herramienta de la guía
# al calcular las referencias: así los dos cuentan exactamente las mismas filas.
RE_NUMERO = re.compile(r"^[+-]?(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?$")


def error(mensaje):
    """Termina con un mensaje que el participante pueda entender y corregir.

    Va a stderr y con código 1: es lo que Codabench enseña en el log del envío.
    Se escribe en bytes UTF-8 porque, con una consola que no lo sea, un print con
    tildes revienta y el participante vería un traceback en vez del mensaje.
    """
    texto = "ERROR: " + mensaje + "\n"
    try:
        sys.stderr.buffer.write(texto.encode("utf-8"))
        sys.stderr.flush()
    except AttributeError:
        sys.stderr.write(texto)
    sys.exit(1)


def leer_config():
    """Lee config.json junto a este fichero y comprueba que tiene sentido."""
    ruta = Path(__file__).resolve().parent / "config.json"
    if not ruta.is_file():
        error(
            "falta config.json junto a score.py. El zip del programa de puntuación "
            "tiene que llevar metadata, score.py y config.json en la raíz"
        )
    try:
        with open(str(ruta), encoding="utf-8-sig") as f:
            config = json.load(f)
    except ValueError as e:
        error("config.json no es un JSON válido: {}".format(e))
    if not isinstance(config, dict):
        error('config.json tiene que ser un objeto, por ejemplo {"columna": "clase", "tipo": "categoria"}')
    columna = config.get("columna")
    if not isinstance(columna, str) or not columna.strip():
        error('config.json no dice qué columna se compara: falta "columna"')
    tipo = config.get("tipo")
    if tipo not in TIPOS:
        error('en config.json, "tipo" tiene que ser "numero" o "categoria", y es {!r}'.format(tipo))
    id_col = config.get("id", "id")
    if not isinstance(id_col, str) or not id_col.strip():
        error('en config.json, "id" tiene que ser el nombre de una columna')
    return columna.strip(), tipo, id_col.strip()


def buscar_csv(carpeta, preferido, que):
    """El CSV de una carpeta. Si hay varios, el que lleve `preferido` en el nombre.

    Se busca también en subcarpetas para poder decir dónde está, pero se prefiere
    siempre el de la raíz: es donde Codabench espera los ficheros.
    """
    if not os.path.isdir(carpeta):
        error("no existe la carpeta {} ({}).".format(carpeta, que))
    hallados = []
    for raiz, dirs, ficheros in os.walk(carpeta):
        dirs[:] = [d for d in dirs if d != "__MACOSX" and not d.startswith(".")]
        for nombre in ficheros:
            if nombre.lower().endswith(".csv") and not nombre.startswith("."):
                ruta = os.path.join(raiz, nombre)
                profundidad = os.path.relpath(ruta, carpeta).count(os.sep)
                hallados.append((ruta, nombre.lower(), profundidad))
    if not hallados:
        error("no hay ningún fichero .csv en {}. Comprueba que el zip lleva el CSV en la raíz".format(que))
    hallados.sort(key=lambda h: (preferido not in h[1], h[2], h[1]))
    return hallados[0][0]


def leer_csv(ruta, id_col, columna, que):
    """Lee un CSV y devuelve la lista ordenada de (id, valor en texto)."""
    nombre = os.path.basename(ruta)
    with open(ruta, "rb") as f:
        crudo = f.read()
    try:
        texto = crudo.decode("utf-8-sig")
    except UnicodeDecodeError:
        error(
            "{} ({}) no está en UTF-8. Guárdalo como «CSV UTF-8 (delimitado por comas)»".format(nombre, que)
        )
    cabecera = texto.split("\n", 1)[0]
    if "," not in cabecera and ";" in cabecera:
        error(
            "{} ({}) separa las columnas con punto y coma. Tiene que ir con comas: en "
            "Excel, Guardar como → «CSV UTF-8 (delimitado por comas)»".format(nombre, que)
        )
    lector = csv.reader(io.StringIO(texto, newline=""))
    try:
        filas = list(lector)
    except csv.Error as e:
        error("{} ({}) no se puede leer como CSV: {}".format(nombre, que, e))
    if not filas:
        error("{} ({}) está vacío".format(nombre, que))
    columnas = [c.strip() for c in filas[0]]
    for falta in (id_col, columna):
        if falta not in columnas:
            error(
                "a {} ({}) le falta la columna '{}'. Sus columnas son: {}".format(
                    nombre, que, falta, ", ".join(columnas)
                )
            )
    i_id, i_valor = columnas.index(id_col), columnas.index(columna)
    salida = []
    vistos = set()
    for n_linea, fila in enumerate(filas[1:], start=2):
        if not any(c.strip() for c in fila):
            continue
        clave = fila[i_id].strip() if i_id < len(fila) else ""
        valor = fila[i_valor].strip() if i_valor < len(fila) else ""
        if not clave:
            error("{} ({}), línea {}: la fila no tiene id".format(nombre, que, n_linea))
        if clave in vistos:
            error("{} ({}): el id '{}' está repetido".format(nombre, que, clave))
        vistos.add(clave)
        salida.append((clave, valor, n_linea))
    if not salida:
        error("{} ({}) no tiene filas".format(nombre, que))
    return salida


def a_numero(valor, nombre, n_linea, clave):
    """Convierte a número o falla diciendo qué fila y por qué."""
    if not RE_NUMERO.match(valor):
        pista = " Usa el punto como separador decimal." if "," in valor else ""
        error(
            "{}, línea {} (id '{}'): '{}' no es un número.{}".format(nombre, n_linea, clave, valor, pista)
        )
    numero = float(valor)
    if math.isnan(numero) or math.isinf(numero):
        error("{}, línea {} (id '{}'): '{}' no es un número válido".format(nombre, n_linea, clave, valor))
    return numero


def cuadrar(solucion, envio):
    """Empareja por id. Falla si al envío le faltan ids de la solución o le sobran."""
    ids_solucion = [c for c, _, _ in solucion]
    del_envio = {c: (v, n) for c, v, n in envio}
    faltan = [c for c in ids_solucion if c not in del_envio]
    if faltan:
        error(
            "al envío le faltan {} de los {} ids (por ejemplo: {}). Tiene que haber una "
            "fila por cada id de test.csv".format(len(faltan), len(ids_solucion), ", ".join(faltan[:3]))
        )
    conjunto = set(ids_solucion)
    sobran = [c for c, _, _ in envio if c not in conjunto]
    if sobran:
        error(
            "el envío tiene {} ids que no están en test.csv (por ejemplo: {})".format(
                len(sobran), ", ".join(sobran[:3])
            )
        )
    return del_envio


def puntuar_numero(solucion, del_envio, nombre_sol, nombre_env):
    """MAE y RMSE, recorriendo la solución en su orden."""
    suma_abs = 0.0
    suma_cuad = 0.0
    for clave, valor, n_linea in solucion:
        real = a_numero(valor, nombre_sol, n_linea, clave)
        texto, n_env = del_envio[clave]
        if not texto:
            error("{}, línea {} (id '{}'): falta la predicción".format(nombre_env, n_env, clave))
        pred = a_numero(texto, nombre_env, n_env, clave)
        diferencia = pred - real
        suma_abs += abs(diferencia)
        suma_cuad += diferencia * diferencia
    n = len(solucion)
    return {
        "mae": round(suma_abs / n, 4),
        "rmse": round(math.sqrt(suma_cuad / n), 4),
        "n": n,
    }


def puntuar_categoria(solucion, del_envio, nombre_env):
    """Proporción de aciertos y F1 macro sobre las clases presentes en la solución.

    El F1 macro pesa igual todas las clases: si una domina, acertar siempre esa no
    basta para quedar arriba, que es lo que sí premiaría la proporción de aciertos.
    """
    pares = []
    for clave, real, _ in solucion:
        texto, n_env = del_envio[clave]
        if not texto:
            error("{}, línea {} (id '{}'): falta la predicción".format(nombre_env, n_env, clave))
        pares.append((real, texto))
    n = len(pares)
    aciertos = sum(1 for real, pred in pares if real == pred)
    suma_f1 = 0.0
    clases = sorted(set(real for real, _ in pares))
    for clase in clases:
        vp = sum(1 for real, pred in pares if real == clase and pred == clase)
        fp = sum(1 for real, pred in pares if real != clase and pred == clase)
        fn = sum(1 for real, pred in pares if real == clase and pred != clase)
        precision = vp / (vp + fp) if vp + fp else 0.0
        exhaustividad = vp / (vp + fn) if vp + fn else 0.0
        if precision + exhaustividad:
            suma_f1 += 2 * precision * exhaustividad / (precision + exhaustividad)
    return {
        "aciertos": round(aciertos / n, 4),
        "f1": round(suma_f1 / len(clases), 4),
        "n": n,
    }


def main():
    if len(sys.argv) >= 3:
        entrada, salida = sys.argv[1], sys.argv[2]
    else:
        entrada, salida = "/app/input", "/app/output"
    columna, tipo, id_col = leer_config()

    # `ref` y `res` se diferencian en una letra y cambiarlas no da error, sino una
    # nota calculada al revés: por eso cada una se nombra en todos los mensajes.
    ruta_sol = buscar_csv(os.path.join(entrada, "ref"), "solution", "la solución")
    ruta_env = buscar_csv(os.path.join(entrada, "res"), "submission", "el envío")
    solucion = leer_csv(ruta_sol, id_col, columna, "la solución")
    envio = leer_csv(ruta_env, id_col, columna, "el envío")
    del_envio = cuadrar(solucion, envio)

    nombre_sol, nombre_env = os.path.basename(ruta_sol), os.path.basename(ruta_env)
    if tipo == "numero":
        notas = puntuar_numero(solucion, del_envio, nombre_sol, nombre_env)
    else:
        notas = puntuar_categoria(solucion, del_envio, nombre_env)

    if not os.path.isdir(salida):
        os.makedirs(salida)
    with open(os.path.join(salida, "scores.json"), "w", encoding="utf-8") as f:
        json.dump(notas, f)
    print(json.dumps(notas))


if __name__ == "__main__":
    main()
