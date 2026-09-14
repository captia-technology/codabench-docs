---
title: "Recursos y tasks"
description: "Subir los ficheros con los que se evalúa la competición y combinarlos en la Task que después asignarán las fases."
---

# Recursos y tasks

**Objetivo:** subir los ficheros con los que se evalúa la competición y combinarlos en la Task que después asignarán las fases.

Estas dos páginas son la parte de la competición que no vive en el editor de la competición, sino en **Resources**, y su orden es estricto: los recursos se suben primero, la Task los referencia después, y solo entonces una [Phase](../evaluacion/phases.md) puede asignarla. Una Task que aún no se ha creado no aparece en el desplegable de la fase.

1. [**Datasets y Programs**](./datasets-programs.md) — subir cada `.zip` como recurso y declarar de qué tipo es —`input_data`, `reference_data`, `ingestion_program`, `scoring_program`, `starting_kit` o `public_data`—, porque el tipo, y no el nombre, decide dónde se puede usar.
2. [**Tasks**](./tasks.md) — combinar esos recursos en una Task: qué datos ve el participante, contra qué se comparan sus predicciones y qué programa las puntúa.

Que vivan fuera del editor es justo lo que los hace reutilizables: la misma Task sirve para varias fases, y los mismos recursos para varias Tasks y para otras competiciones propias.
