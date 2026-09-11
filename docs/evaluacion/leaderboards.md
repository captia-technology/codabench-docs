---
title: "Leaderboards"
description: "Montar la tabla de resultados de la competición y conseguir que sus columnas se rellenen con las métricas que devuelve el scoring program."
sidebar_position: 2
---

# Leaderboards

**Objetivo:** montar la tabla de resultados de la competición y conseguir que sus columnas se rellenen con las métricas que devuelve el scoring program.

## Crear el leaderboard y sus columnas

Pestaña **Leaderboards**:

1. Crear un leaderboard: **Title** y **Key** (identificador único, preferiblemente en minúsculas).
2. Añadir columnas, una por cada métrica que devuelva el scoring program:
   - **Title**: nombre visible de la columna.
   - **Column Key**: debe coincidir *exactamente* con la clave que el scoring program escribe en `scores.txt` (ver más abajo).
   - **Sorting**: ascendente o descendente (según si menor o mayor valor es mejor).
   - **Primary Column**: marca cuál es la columna principal de ranking.
   - **Computation**: `None` normalmente, o `Average` si la columna es la media calculada de otras columnas (en ese caso no recibe score directo del scoring program).

Qué submission de cada participante se muestra en esta tabla lo decide la [submission rule](./submission-rule.md), que se configura al crear o editar el leaderboard.

## El fichero `scores.txt`

El scoring program debe escribir un `scores.txt` con líneas `clave: valor`, por ejemplo:

```
accuracy: 0.8721
f1_score: 0.8390
```

:::warning[La Column Key tiene que ser literal]
Si la `Column Key` no coincide con la clave de `scores.txt`, la columna aparece vacía en el leaderboard sin error explícito — es el fallo más frecuente al montar el leaderboard.
:::

## Antes de la primera submission

Mientras no haya ninguna submission añadida al leaderboard, la pestaña **Results** muestra "No visible leaderboard for this benchmark" — es el estado normal antes de la primera submission válida, no un error de configuración.

**Siguiente paso:** [Submission rule](./submission-rule.md) — cuál de las submissions de cada participante ocupa su fila en esta tabla.
