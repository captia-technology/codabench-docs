---
title: "Preparar los ficheros"
description: "Elegir cómo preparar los cuatro zip que necesita una competición —con la herramienta de esta guía, a partir de un CSV, o a mano— y saber qué tiene que haber en ellos al final."
---

# Preparar los ficheros

**Objetivo:** elegir cómo preparar los cuatro zip que necesita una competición —con la herramienta de esta guía, a partir de un CSV, o a mano— y saber qué tiene que haber en ellos al final.

Una competición de predicciones directas, en la que el participante sube un CSV con sus predicciones, necesita cuatro zip. Después se suben como recursos en [Datasets y Programs](../recursos/datasets-programs.md):

| Zip | Qué lleva | Quién lo ve |
|---|---|---|
| `public_data` | `train.csv`, con la respuesta, y `test.csv`, sin ella | Todo el mundo |
| `starting_kit` | Lo necesario para hacer un primer envío válido | Todo el mundo |
| `reference_data` | La respuesta de cada fila de `test.csv` | **Solo el scoring program** |
| `scoring_program` | El programa que compara cada envío con la respuesta | Nadie lo descarga |

Hay dos caminos, y los dos acaban en los mismos cuatro zip:

1. [**Con la herramienta**](./herramienta.mdx) — subes un CSV con una fila por caso, eliges qué hay que predecir y dónde empieza la prueba, y descargas los zip. Es el camino corto y no hace falta programar. La descarga de un equipo desde captia.ai sirve tal cual. **Todo ocurre en tu navegador: el CSV no sale de tu ordenador.**
2. [**A mano**](./a-mano.mdx) — qué lleva cada zip, las reglas que más fallan y un programa de puntuación genérico listo para usar. Sirve cuando los datos no caben en la herramienta, y para entender o retocar lo que ha generado.

Hagas los zip como los hagas, la herramienta tiene un apartado para [comprobarlos](./herramienta.mdx#comprobar-mis-ficheros) antes de subirlos.
