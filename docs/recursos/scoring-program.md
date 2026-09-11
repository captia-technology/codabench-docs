---
title: "El scoring program por dentro"
description: "Escribir un scoring program que se ejecute donde Codabench espera, lea los ficheros donde están de verdad y deje las métricas donde la plataforma las busca."
sidebar_label: "El scoring program"
sidebar_position: 2
---

# El scoring program por dentro

**Objetivo:** escribir un scoring program que se ejecute donde Codabench espera, lea los ficheros donde están de verdad y deje las métricas donde la plataforma las busca.

Es la pieza que más tiempo hace perder al montar la primera competición, y casi nunca por el cálculo de la métrica: se pierde en las rutas. Esta página recoge el contrato exacto.

## Qué contiene el `.zip`

```
scoring_program.zip
├── metadata          ← sin extensión, y es obligatorio
└── scoring.py        ← el nombre da igual; el que manda es el de `metadata`
```

El fichero `metadata` declara qué se ejecuta:

```yaml
command: python3 $program/scoring.py $input $output
```

## Las rutas: qué es cada variable

Codabench sustituye esas variables antes de lanzar el contenedor, y **`$input` no significa lo mismo en los dos programas**. Es el detalle que rompe más scoring programs escritos copiando un ejemplo de ingestion:

| Variable | En el ingestion program | En el scoring program |
|---|---|---|
| `$input` | `/app/input_data` | `/app/input` |
| `$output` | `/app/output` | `/app/output` |
| `$program` | `/app/program` | `/app/program` |
| `$predictions` | `/app/output` | `/app/input/res` |
| `$hidden` | — | `/app/input/ref` |
| `$shared` | `/app/shared` | `/app/shared` |

Dentro del contenedor de scoring, el árbol queda así:

```
/app/
├── input/
│   ├── ref/        ← reference_data: la verdad. NUNCA llega al participante
│   └── res/        ← lo que entregó el participante, o la salida del ingestion
├── output/         ← aquí se escribe scores.txt
└── program/        ← el propio scoring program
```

:::warning[`ref` y `res` se confunden, y el fallo es silencioso]
Las dos carpetas cuelgan de `$input` y sus nombres se diferencian en una letra. Intercambiarlas no da un error de fichero no encontrado —las dos existen y las dos tienen CSV dentro—: da una métrica calculada al revés, que se publica en el leaderboard con toda naturalidad. Vale la pena una línea que compruebe que la columna de la etiqueta está en `ref` y no en `res`.
:::

## Dónde se escriben las métricas

En `$output`, y Codabench busca **dos** ficheros, por este orden:

1. `scores.json` — un objeto JSON con `clave: valor`.
2. `scores.txt` — si no hay JSON. **Se lee con un parser YAML**, y de ahí viene que el formato `clave: valor` funcione.

Si no encuentra ninguno, la submission falla con `Could not find scores file, did the scoring program output it?`.

Que `scores.txt` se lea como YAML tiene una consecuencia práctica: un `NaN`, una cadena sin comillas con dos puntos dentro o una tabulación traicionera lo convierten en otra cosa —o lo rompen— sin que el mensaje mencione el fichero. Escribir números, y ya está.

```
f1_macro: 0.8114
accuracy: 0.9032
```

Cada clave tiene que coincidir **letra por letra** con la `Column Key` de su columna del [leaderboard](../evaluacion/leaderboards.md). Una clave que no corresponde a ninguna columna no da error: simplemente no se ve.

## Un scoring program completo

Este es el del [ejemplo de la guía](../empezar/ejemplo.md): valida la entrega, calcula F1 macro y exactitud, y escribe las dos.

```python
#!/usr/bin/env python3
"""Scoring del ejemplo: clase de calidad del aire por aula y franja."""
import sys
from pathlib import Path

import pandas as pd
from sklearn.metrics import accuracy_score, f1_score

CLASES = {"buena", "aceptable", "deficiente"}
COLUMNAS = ["id", "prediccion_iaq_class"]


def error(mensaje):
    """Sale con un mensaje que el participante pueda entender y accionar.

    Va a stderr y con codigo 1: es lo que Codabench muestra en el log de la
    submission. Un traceback de pandas ahi no le dice nada a quien entrega.
    """
    print(f"ERROR: {mensaje}", file=sys.stderr)
    sys.exit(1)


def main():
    entrada, salida = Path(sys.argv[1]), Path(sys.argv[2])
    ref, res = entrada / "ref", entrada / "res"

    # 1 - la entrega existe y tiene el nombre exacto
    csv = res / "submission.csv"
    if not csv.is_file():
        sueltos = [p.name for p in res.rglob("*.csv")]
        if sueltos:
            error(
                f"no encuentro submission.csv en la raiz del zip; he visto {sueltos}. "
                "El CSV va en la raiz, no dentro de una carpeta"
            )
        error("el zip no contiene ningun CSV")

    entrega = pd.read_csv(csv)
    verdad = pd.read_csv(ref / "test_labels.csv")

    # 2 - columnas exactas, en nombre y en orden
    if list(entrega.columns) != COLUMNAS:
        error(f"columnas {list(entrega.columns)}; esperaba exactamente {COLUMNAS}")

    # 3 - un id por fila, ni repetidos ni ausentes
    if entrega["id"].duplicated().any():
        repetidos = entrega.loc[entrega["id"].duplicated(), "id"].head(3).tolist()
        error(f"ids repetidos, por ejemplo {repetidos}")
    faltan = set(verdad["id"]) - set(entrega["id"])
    sobran = set(entrega["id"]) - set(verdad["id"])
    if faltan or sobran:
        error(f"los ids no cuadran con test.csv: faltan {len(faltan)}, sobran {len(sobran)}")

    # 4 - solo clases validas
    invalidas = set(entrega["prediccion_iaq_class"]) - CLASES
    if invalidas:
        error(f"clases no validas: {sorted(invalidas)}; las validas son {sorted(CLASES)}")

    # 5 - alinear por id ANTES de comparar. Sin esto, una entrega correcta pero
    #     ordenada de otra forma puntua como si fuera aleatoria.
    juntos = verdad.merge(entrega, on="id", validate="one_to_one")

    y_real = juntos["iaq_class"]
    y_pred = juntos["prediccion_iaq_class"]

    metricas = {
        "f1_macro": f1_score(y_real, y_pred, average="macro", labels=sorted(CLASES)),
        "accuracy": accuracy_score(y_real, y_pred),
    }

    salida.mkdir(parents=True, exist_ok=True)
    with open(salida / "scores.txt", "w", encoding="utf-8") as f:
        for clave, valor in metricas.items():
            f.write(f"{clave}: {valor:.4f}\n")


if __name__ == "__main__":
    main()
```

Las cinco validaciones no son celo excesivo: cada una corresponde a una fila de la [tabla de errores](../submissions/formato.md) y a un mensaje que el participante puede arreglar solo, sin escribir al foro.

El paso 5 es el que se olvida y el más caro. Comparar dos CSV fila a fila da por supuesto que los dos llegan en el mismo orden, y nada se lo garantiza al participante. Sin el `merge`, una entrega perfecta puede puntuar como el azar y nadie entiende por qué.

## Las dependencias van en la imagen, no en el zip

El contenedor no instala nada: ejecuta el `command` y ya está. Si el scoring program importa `pandas` o `scikit-learn`, la imagen tiene que traerlos. La de por defecto, `codalab/codalab-legacy:py37`, se queda corta enseguida — y el síntoma es un `ModuleNotFoundError` en el log de la submission. Se resuelve en **Details → Competition Docker Image** con una imagen propia que los incluya; está explicado en [Details](../competicion/details.md).

**Siguiente paso:** [Tasks](./tasks.md) — combinar estos recursos en la unidad que evalúa las submissions.
