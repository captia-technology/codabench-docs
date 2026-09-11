---
title: "Requisitos previos"
description: "Llegar al editor de competiciones con la cuenta creada y con todos los ficheros ya comprimidos y nombrados de forma que se distingan en los desplegables de la UI."
sidebar_position: 3
---

# Requisitos previos

**Objetivo:** llegar al editor de competiciones con la cuenta creada y con todos los ficheros ya comprimidos y nombrados de forma que se distingan en los desplegables de la UI.

## La cuenta

Cuenta creada en la instancia de Codabench que se vaya a usar (p. ej. codabench.org o una instancia propia).

## Los ficheros comprimidos

Los ficheros ya preparados y comprimidos en `.zip` por separado:

- `input_data.zip`
- `reference_data.zip`
- `ingestion_program.zip` (opcional si la competición es de [predicciones directas](../submissions/formato.md))
- `scoring_program.zip`
- `starting_kit.zip` / `public_data.zip` (opcionales)

:::note[De dónde salen estos ficheros]
Generarlos queda fuera del alcance de esta guía, que empieza cuando los `.zip` ya existen. El repositorio que los produce está listado en [fuentes y documentación oficial](../referencia/fuentes.md).
:::

## El fichero `metadata` de cada programa

Cada programa (`ingestion_program`, `scoring_program`) debe incluir dentro un fichero `metadata` (sin extensión) que indique el comando a ejecutar, por ejemplo:

```yaml
command: python3 $program/scoring.py $input $output
```

## La convención de nombres

Conviene nombrar los zips de forma que se identifiquen sin ambigüedad al elegirlos en los desplegables de la UI, p. ej. `reference_data_<slug>_<version>.zip`, `scoring_program_<slug>_<version>.zip`, `<slug>_<version>_public_data.zip`, `<slug>_<version>_starting_kit.zip` — sobre todo si se van a crear varias versiones/fases de la misma competición y conviven varios recursos con nombres parecidos en [**Resources → Datasets/Programs**](../recursos/datasets-programs.md).

**Siguiente paso:** [Crear la competición](../competicion/index.md) — el editor web pestaña a pestaña, empezando por **Details**.
