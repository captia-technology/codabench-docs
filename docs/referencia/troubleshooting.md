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
| Participante no puede enviar submission | **Auto Approve Registration** desactivado y el registro no ha sido aprobado manualmente por un organizador en **Resources → Participants**. |
| Scoring program falla con `ModuleNotFoundError` | Dependencias no incluidas en el entorno de ejecución de la queue/worker usada; revisar qué imagen/entorno tiene asociada la queue. |
| Submission ya procesada no sale en el leaderboard | Falta pulsar la acción manual de "añadir a leaderboard" en **Resources → Submissions**, según la submission rule configurada. |
| Submission rechazada con `Only zip files are allowed` / `Missing submission.csv` / `Invalid columns` / `IDs mismatch` | Formato de entrega no válido — ver [formato de submission](../submissions/formato.md); reforzar la validación y el mensaje de error dentro del propio scoring program. |
| Sample submission da un resultado distinto al esperado (p. ej. `n` de filas no coincide) | La fase probablemente no está apuntando al `reference_data` correcto de esa versión del dataset. |
