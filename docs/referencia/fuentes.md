---
title: "Fuentes y documentación oficial"
description: "Saber a qué documentación oficial acudir cuando algo de esta guía no cuadre con lo que muestra la interfaz, y con qué versión de Codabench está contrastado lo que aquí se cuenta."
sidebar_label: "Fuentes"
sidebar_position: 2
---

# Fuentes y documentación oficial

**Objetivo:** saber a qué documentación oficial acudir cuando algo de esta guía no cuadre con lo que muestra la interfaz, y con qué versión de Codabench está contrastado lo que aquí se cuenta.

## Referencias

- [Getting started with Codabench](https://docs.codabench.org/latest/Organizers/Benchmark_Creation/Getting-started-with-Codabench/)
- [Competition Creation Form](https://docs.codabench.org/latest/Organizers/Benchmark_Creation/Competition-Creation-Form/)
- [Resource Management (Submissions, Datasets/Programs, Tasks)](https://docs.codabench.org/v1.31.2/Organizers/Running_a_benchmark/Resource-Management/)
- [How to Create your First Benchmark on Codabench (tutorial completo)](https://adrienpavao.com/blog/codabench-tuto/codabench-tuto.html)
- Método alternativo (bundle YAML + zip, versionable en repo): [Competition Creation Bundle](https://docs.codabench.org/latest/Organizers/Benchmark_Creation/Competition-Creation-Bundle/)
- Para generar los ficheros (`public_data`, `reference_data`, `scoring_program`, `starting_kit`) antes de llegar a esta guía: repo privado `captia-technology/codabench-dataset-pipeline` (motor genérico parametrizado por `spec.yaml`, acceso restringido).

## Con qué versión está contrastada esta guía

Este sitio se presenta como contrastado con **Codabench v1.31.2**, la última versión publicada en el momento de la última revisión (27 de agosto de 2026). Conviene ser preciso sobre qué significa eso aquí, porque no todas las afirmaciones de una guía se comprueban igual:

| De dónde sale | Qué cubre |
|---|---|
| **Una competición real montada de principio a fin** | El recorrido completo: subir recursos, crear la Task, abrir la fase, recibir submissions y verlas puntuar. Es el origen de esta guía. |
| **Las notas de publicación y el código de la etiqueta `v1.31.2`** | Los campos de cada formulario, los valores que admite cada desplegable y los valores por defecto. Es lo que se revisó al actualizar de v1.23 a v1.31.2. |
| **La documentación oficial** | Lo que la plataforma declara de sí misma, enlazada arriba. |

Lo que **no** se ha hecho: volver a montar una competición entera sobre una instancia con la v1.31.2 y comprobar pantalla por pantalla. Donde la interfaz no coincida con lo que aquí se lee, manda la interfaz — y agradeceremos el aviso.

:::note[Qué cambió entre v1.23 y v1.31.2]
Poco, en lo que afecta a esta guía: el desplegable **Computation** del leaderboard ganó la opción `Average Rank` (v1.29), los logs de una submission pasaron a agruparse en pestañas (v1.26), los desplegables de selección de la fase muestran ahora la descripción de cada recurso (v1.27), y aparecieron los grupos de participantes con cola propia (v1.28) y la validación **Human in the Loop** (v1.31).

La mayor parte de lo que se añadió en esta revisión no era desfase de versión, sino campos que existían desde el principio y que la guía no cubría. El detalle está en el registro del repositorio, fuera del sitio publicado.
:::
