---
title: "Phases"
description: "Definir las etapas temporales de la competición, con sus fechas y sus límites de submission, y enganchar a cada una la Task que la evalúa."
sidebar_position: 1
---

# Phases

**Objetivo:** definir las etapas temporales de la competición, con sus fechas y sus límites de submission, y enganchar a cada una la Task que la evalúa.

## Crear una fase

Volver al editor de la competición, pestaña **Phases**:

1. Crear una fase (p. ej. `Development`) con:
   - **Name** y **Description**.
   - **Start** / **End** (en UTC).
   - **Tasks**: asignar la(s) Task(s) creada(s) en [Tasks](../recursos/tasks.md).
   - **Execution Time Limit**: límite de tiempo (segundos) para que corran ingestion/scoring por submission.
   - **Max submissions per day**: límite diario por participante (medianoche a medianoche UTC).
   - **Max submissions per person**: tope total por participante.
2. Repetir para cada fase adicional (p. ej. `Final`), reutilizando la misma Task si el scoring program no cambia, o creando una Task nueva si cambia el dataset oculto.

## Development y Final

La fase Development normalmente da feedback inmediato al participante; la fase Final suele ocultar resultados hasta el cierre de la competición para evitar overfitting al leaderboard público.

## Fases sin fecha de cierre

:::note[End vacío]
Si **End** se deja vacío, la fase queda abierta indefinidamente (la cabecera pública muestra "Current Phase Ends: Never") — es válido para competiciones internas de validación sin fecha de cierre fija.
:::

**Siguiente paso:** [Leaderboards](./leaderboards.md) — la tabla donde se publican las métricas que devuelve el scoring program.
