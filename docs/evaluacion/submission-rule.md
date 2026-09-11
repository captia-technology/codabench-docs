---
title: "Submission rule"
description: "Elegir cuál de las submissions de cada participante es la que aparece en el leaderboard."
sidebar_position: 3
---

# Submission rule

**Objetivo:** elegir cuál de las submissions de cada participante es la que aparece en el leaderboard.

Se configura en el campo **Submission Rule** al crear o editar el [leaderboard](./leaderboards.md), y controla qué submission de cada participante se muestra. Son **seis**, y el desplegable las presenta con estos nombres:

| Regla | Qué hace | ¿Entra sola en el leaderboard? |
|---|---|---|
| **Add** | El participante puede añadir **una** submission. Una vez añadida, no la retira. | No |
| **Add And Delete** | Una submission, que el participante puede quitar y sustituir. | No |
| **Add And Delete Multiple** | Varias submissions a la vez, que el participante añade y quita a voluntad. | No |
| **Force Last** | Solo cuenta la última submission enviada. | **Sí** |
| **Force Latest Multiple** | Como la anterior, pero admitiendo varias entradas del mismo participante. | **Sí** |
| **Force Best** | Se muestra la mejor según la **Primary Column**. | **Sí** |

La columna de la derecha es la que decide el trabajo del participante, y es el detalle que más confusión causa al montar la primera competición:

- Con las tres reglas **Force**, Codabench añade la submission al leaderboard en cuanto termina de puntuarse. El participante no hace nada.
- Con **Add**, **Add And Delete** y **Add And Delete Multiple**, la submission se procesa y se puntúa igual, pero **se queda fuera de la tabla hasta que alguien la añade a mano**. No es un fallo de configuración ni un error: es la regla funcionando. El procedimiento está en [Probar la competición](../submissions/probar.md).

`Add` es el valor por defecto: una competición recién creada a la que nadie le ha tocado esta opción exige esa acción manual.

**Siguiente paso:** [Submissions](../submissions/index.md) — qué entrega el participante y cómo comprobar que la cadena entera puntúa.
