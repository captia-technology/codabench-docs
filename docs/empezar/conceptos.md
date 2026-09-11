---
title: "Conceptos clave"
description: "Reconocer los bloques con los que se construye una competición en Codabench y saber en qué parte de la guía se configura cada uno."
sidebar_position: 1
---

# Conceptos clave

**Objetivo:** reconocer los bloques con los que se construye una competición en Codabench y saber en qué parte de la guía se configura cada uno.

Antes de tocar la UI, conviene tener claros los bloques con los que se construye una competición.

## Los bloques de una competición

| Concepto | Qué es |
|---|---|
| [**Competition**](../competicion/index.md) | La competición en sí: título, descripción, páginas, fases y leaderboards. |
| [**Dataset**](../recursos/datasets-programs.md) | Datos subidos como recurso: `input_data` (lo que ve el participante), `reference_data` (ground truth), `public_data` o `starting_kit`. |
| [**Program**](../recursos/datasets-programs.md) | Código ejecutable subido como recurso. Dos tipos: **Ingestion program** (transforma la submission del participante en predicciones) y **Scoring program** (compara predicciones contra `reference_data` y calcula métricas). |
| [**Task**](../recursos/tasks.md) | Combina Datasets + Programs (input_data, reference_data, ingestion program, scoring program). Se crea una vez y se reutiliza en una o varias Phases. |
| [**Phase**](../evaluacion/phases.md) | Etapa temporal de la competición (ej. `Development`, `Final`). Referencia una o varias Tasks y tiene sus propias fechas y límites de submission. |
| [**Leaderboard**](../evaluacion/leaderboards.md) | Tabla de resultados: columnas (métricas), orden de ranking y regla de qué submission de cada participante se muestra. |
| [**Submission**](../submissions/formato.md) | Lo que sube un participante: predicciones o código, según cómo esté configurada la Task. |

## Los recursos se crean una vez, no una por fase

Los recursos (Datasets/Programs) y las Tasks se crean **una sola vez** y luego se reutilizan al vincularlos desde las Phases — no se suben de nuevo por cada fase.

**Siguiente paso:** [Requisitos previos](./requisitos.md) — los ficheros y la cuenta que hay que tener listos antes de abrir el editor.
