---
title: "Fases y evaluación"
description: "Poner fechas y límites a la competición, publicar las métricas en una tabla de resultados y decidir qué submission de cada participante se muestra en ella."
---

# Fases y evaluación

**Objetivo:** poner fechas y límites a la competición, publicar las métricas en una tabla de resultados y decidir qué submission de cada participante se muestra en ella.

Con la Task ya creada en [recursos y tasks](../recursos/index.md), esta sección configura cuándo se compite y cómo se puntúa. Se recorre en este orden: primero cuándo se compite y con qué límites, después cómo se publican los resultados.

1. [**Phases**](./phases.md) — las etapas de la competición (`Development`, `Final`): fechas en UTC, Tasks asignadas y límites de submissions por participante.
2. [**Leaderboards**](./leaderboards.md) — la tabla de resultados: una columna por métrica, con su orden de ranking y su columna principal.
3. [**Submission rule**](./submission-rule.md) — cuál de las submissions de cada participante aparece en el leaderboard: la última, la mejor, o la que elija el propio participante.

El fallo más frecuente al montar esta parte es que la **Column Key** de una columna no coincida con la clave que el scoring program escribe en `scores.txt`: la columna queda vacía y no se emite ningún error. El síntoma, con el resto de los habituales, está en [troubleshooting](../referencia/troubleshooting.md).
