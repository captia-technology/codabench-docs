---
title: "Datasets y Programs"
description: "Subir a Codabench los datos y el código que después consumirá la Task, una sola vez y de forma reutilizable."
sidebar_position: 1
---

# Datasets y Programs

**Objetivo:** subir a Codabench los datos y el código que después consumirá la Task, una sola vez y de forma reutilizable.

Antes de crear una Task hacen falta los recursos que va a usar. Ir a **Resources → Datasets/Programs** (accesible también desde el botón **Manage Tasks/Datasets** dentro de la pestaña [Phases](../evaluacion/phases.md)).

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

**Siguiente paso:** [Tasks](./tasks.md) — combinar estos recursos en la unidad que evalúa las submissions.
