---
title: "Troubleshooting"
description: "Identificar rápido la causa probable de los fallos que más aparecen al montar y probar una competición."
sidebar_position: 1
---

# Troubleshooting

**Objetivo:** identificar rápido la causa probable de los fallos que más aparecen al montar y probar una competición.

## Síntomas y causas probables

| Síntoma | Causa probable |
|---|---|
| Leaderboard vacío o con `-` | El **Column Key** no coincide con la clave escrita en `scores.txt` por el scoring program. |
| "No visible leaderboard for this benchmark" | Normal si aún no hay ninguna submission válida añadida al leaderboard; no indica un fallo de configuración. |
| Submission se queda en "Running" indefinidamente | Se supera el **Execution Time Limit** de la fase, o hay una excepción no capturada en ingestion/scoring (revisar logs stdout/stderr de la submission). |
| No aparece la Task al configurar una Phase | La Task no se creó antes en **Resources → Tasks**, o el Dataset/Program referenciado sigue sin subirse. |
| Fase no aparece / sigue en la anterior | Fechas **Start/End** mal puestas o interpretadas en huso horario distinto (Codabench usa UTC); recordar que **End** vacío significa fase sin cierre ("Never"). |
| Participante no puede enviar submission | **Auto approve registration requests** sin marcar y el registro todavía sin aprobar. Se aprueba desde el botón **Participants** de la cabecera de la competición. |
| Scoring program falla con `ModuleNotFoundError` | La imagen en la que se ejecuta no trae esa dependencia. Se cambia en **Details → Competition Docker Image**, que por defecto vale `codalab/codalab-legacy:py37`; ver [Details](../competicion/details.md). |
| Submission ya procesada no sale en el leaderboard | La **submission rule** del leaderboard es `Add`, `Add And Delete` o `Add And Delete Multiple` —`Add` es la de por defecto— y esas tres no añaden nada solas: falta pulsar la acción de "añadir a leaderboard" desde el botón **Submissions** de la cabecera de la competición, que lista las entregas de todo el mundo. Con `Force Last`, `Force Latest Multiple` o `Force Best` entra sola. |
| Submission rechazada con `Only zip files are allowed` / `Missing submission.csv` / `Invalid columns` / `IDs mismatch` | Formato de entrega no válido — ver [formato de submission](../submissions/formato.md); reforzar la validación y el mensaje de error dentro del propio scoring program. |
| Sample submission da un resultado distinto al esperado (p. ej. `n` de filas no coincide) | La fase probablemente no está apuntando al `reference_data` correcto de esa versión del dataset. |
