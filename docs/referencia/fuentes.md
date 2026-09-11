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
- [Resource Management (Submissions, Datasets/Programs, Tasks)](https://docs.codabench.org/v1.23/Organizers/Running_a_benchmark/Resource-Management/)
- [How to Create your First Benchmark on Codabench (tutorial completo)](https://adrienpavao.com/blog/codabench-tuto/codabench-tuto.html)
- Método alternativo (bundle YAML + zip, versionable en repo): [Competition Creation Bundle](https://docs.codabench.org/latest/Organizers/Benchmark_Creation/Competition-Creation-Bundle/)
- Para generar los ficheros (`public_data`, `reference_data`, `scoring_program`, `starting_kit`) antes de llegar a esta guía: repo privado `captia-technology/codabench-dataset-pipeline` (motor genérico parametrizado por `spec.yaml`, acceso restringido).

## De dónde sale «Codabench v1.23»

Este sitio se presenta como contrastado con **Codabench v1.23**. Esa etiqueta sale de las URLs de la documentación oficial que cita esta guía —la de Resource Management está publicada bajo `v1.23`; las demás, bajo `latest`—, **no** de una comprobación contra la instancia de Codabench en la que se montó la competición. Nadie ha mirado qué versión declara esa instancia.

:::warning[Codabench va por delante de esta guía]
En el momento de publicar, la última versión publicada de Codabench es **v1.31.2** (27 de agosto de 2026), ocho versiones menores por delante de la que esta guía declara haber contrastado. El procedimiento que se describe aquí se montó sobre una competición real y funcionaba, pero **puede haber cambiado algún rótulo, alguna pestaña o algún campo** de los que se nombran. Donde la interfaz no coincida con lo que lees, manda la interfaz —y la [documentación oficial](https://docs.codabench.org/), que se publica por versión—.

La revisión de la guía contra la versión actual está pendiente; mientras tanto, la etiqueta se deja en v1.23 a propósito, porque es la versión contra la que el contenido se contrastó de verdad.
:::
