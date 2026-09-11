---
title: "Submissions"
description: "Fijar qué entrega exactamente el participante y comprobar con una submission real que la cadena completa funciona antes de abrir la competición."
---

# Submissions

**Objetivo:** fijar qué entrega exactamente el participante y comprobar con una submission real que la cadena completa funciona antes de abrir la competición.

Las dos páginas de esta sección cierran el montaje: una define el contrato de entrega y en la otra lo recorre uno mismo, en el papel del participante.

1. [**Formato de submission**](./formato.md) — qué sube el participante cuando la Task no tiene ingestion program, y qué debe validar el scoring program antes de puntuar nada.
2. [**Probar la competición**](./probar.md) — subir una submission de prueba, seguir sus logs y verificar que el valor llega al leaderboard.

## Qué le pasa a una submission

De arriba abajo, con el punto en el que se rompe cada cosa señalado a la derecha:

```mermaid
flowchart TB
  A["El participante sube<br/><b>submission.zip</b>"]
  B["Cola de ejecución<br/><i>espera un worker libre</i>"]
  C["<b>Ingestion program</b><br/><i>solo si la Task lo tiene</i>"]
  D["<b>Scoring program</b><br/>valida la entrega<br/>y compara con reference_data"]
  E["<b>scores.txt</b><br/><code>f1_macro: 0.8114</code>"]
  F["Columna del leaderboard<br/>con la misma <b>Column Key</b>"]
  G["La fila aparece en <b>Results</b>"]

  A --> B --> C --> D --> E --> F --> G

  B -. "se queda en Running:<br/>Execution Time Limit<br/>o worker parado" .-> X1[" "]
  D -. "formato inválido:<br/>la entrega se rechaza<br/>con su mensaje" .-> X2[" "]
  E -. "la clave no coincide:<br/>columna vacía,<br/>y sin error" .-> X3[" "]
  F -. "submission rule Add:<br/>espera a que<br/>alguien la añada" .-> X4[" "]

  classDef vacio fill:none,stroke:none
  class X1,X2,X3,X4 vacio
```

Las cuatro ramas de puntos son, por orden de frecuencia, los cuatro motivos por los que un organizador cree que su competición está mal montada. Ninguno de los cuatro produce un error visible en la pantalla de la competición: hay que ir a buscarlos. El [troubleshooting](../referencia/troubleshooting.md) los recoge con su síntoma exacto.

Probar forma parte del montaje, no es un extra: hasta que una submission recorre ingestion, scoring y leaderboard, no hay ninguna evidencia de que la [Task](../recursos/tasks.md) y el [leaderboard](../evaluacion/leaderboards.md) estén apuntando a lo que se cree.
