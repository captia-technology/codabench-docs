---
title: "Probar la competición"
description: "Comprobar de extremo a extremo, con una submission real, que la cadena ingestion → scoring → leaderboard funciona antes de abrir la competición a los participantes."
sidebar_position: 2
---

# Probar la competición

**Objetivo:** comprobar de extremo a extremo, con una submission real, que la cadena ingestion → scoring → leaderboard funciona antes de abrir la competición a los participantes.

## Recorrido de una submission de prueba

1. Publicar (o dejar en modo no listado) la competición y entrar a su página pública.
2. Pestaña **My Submissions**: subir una submission de prueba (`.zip`) — dummy o real.
3. Seguir los logs en tiempo real mientras se procesa (stdout/stderr disponibles por submission).
4. Verificar:
   - que el ingestion program (si existe) corre sin errores,
   - que el scoring program genera `scores.txt` con las claves esperadas,
   - que el leaderboard muestra el valor correctamente.
5. Si el leaderboard no se actualiza solo: ir a **Resources → Submissions**, localizar la submission procesada y usar el botón de acción **añadir a leaderboard** (según la [`submission_rule`](../evaluacion/submission-rule.md) configurada, puede requerirse esta acción manual la primera vez).

**Si algo no cuadra:** [troubleshooting](../referencia/troubleshooting.md) — el síntoma y su causa probable, antes de dar por mal montada la competición.
