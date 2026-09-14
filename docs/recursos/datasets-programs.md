---
title: "Datasets y Programs"
description: "Subir a Codabench los datos y el código que después consumirá la Task, una sola vez y de forma reutilizable."
sidebar_position: 1
---

# Datasets y Programs

**Objetivo:** subir a Codabench los datos y el código que después consumirá la Task, una sola vez y de forma reutilizable.

Antes de crear una Task hacen falta los recursos que va a usar. Ir a **Resources → Datasets and programs** —«Resources» está en el menú de la cuenta, arriba a la derecha— (accesible también desde el botón **Manage Tasks/Datasets** dentro de la pestaña [Phases](../evaluacion/phases.md)).

Los cuatro tipos de recurso se ven mejor con el [ejemplo](../empezar/ejemplo.md) delante: `public_data` lleva el `train.csv` y el `test.csv` que descarga el participante, `reference_data` las etiquetas reales que nunca salen de aquí, y `scoring_program` el código que compara las dos cosas.

![Pestaña «Datasets and programs» de Resources, con cuatro recursos y las columnas Type, Size, In Use y Public](./resources-datasets-y-programas.jpg)

*La columna **Public** es la que hay que mirar dos veces: el starting kit y los datos públicos la tienen marcada, y **reference data y scoring program no**. Así es como tiene que quedar — si el ground truth aparece marcado como público, la competición está rota aunque todo lo demás funcione.*

*La columna **In Use** indica si algún Task lo referencia; los que no lo están se pueden borrar desde **Quota and Cleanup**, al final de la misma pantalla, que también muestra cuánto espacio queda de la cuota.*

## Subir los recursos

1. Click **Add Dataset/Program**.
2. Rellenar nombre, subir el `.zip` correspondiente y seleccionar el tipo de recurso.
3. Repetir para cada uno:
   - `input_data`
   - `reference_data`
   - `ingestion_program` (si aplica)
   - `scoring_program`
   - `starting_kit` / `public_data` (opcionales)

Los recursos se pueden marcar como públicos o privados, y son reutilizables entre Tasks y entre competiciones propias.

**Siguiente paso:** [El scoring program](./scoring-program.md) — qué lleva dentro ese zip, dónde encuentra los ficheros y dónde deja las métricas.
