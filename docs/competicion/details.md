---
title: "Details"
description: "Crear la competición en Codabench y rellenar la pestaña Details, que es la que le da título, logo, descripción y cola de procesamiento."
sidebar_position: 1
---

# Details

**Objetivo:** crear la competición en Codabench y rellenar la pestaña Details, que es la que le da título, logo, descripción y cola de procesamiento.

## Crear la competición

1. En el menú superior: **Benchmarks → Management**.
2. Click en **Create** (botón arriba a la derecha de Competition Management).
3. Se abre el editor de la competición con varias pestañas. Rellenar **Details**:
   - **Title**: nombre de la competición.
   - **Logo**: imagen identificativa.
   - **Description**: resumen que aparece en el listado de competiciones.
   - **Queue**: cola de procesamiento de submissions (usar la que corresponda; por defecto la pública si no se tiene una propia configurada).

En este punto la competición ya existe (en borrador) y se puede seguir editando en cualquier momento.

:::note[El Docker image que aparece sin haberlo escrito]

La cabecera pública de la competición muestra siempre un **Docker image** (p. ej. `codalab/codalab-legacy:py37`), aunque toda la competición se haya montado por UI sin tocar YAML — es el entorno de ejecución asociado a la Queue/Task usada, no algo que se escriba a mano en este flujo.

:::

**Siguiente paso:** [Participation](./participation.md) — quién puede registrarse y bajo qué términos.
