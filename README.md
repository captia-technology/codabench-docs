# Codabench Docs

Guía de referencia para crear y mantener competiciones en [Codabench](https://www.codabench.org/), la plataforma open-source (sucesora de CodaLab) para benchmarks y competiciones de machine learning.

## Contenido

- [`docs/crear-competicion.md`](docs/crear-competicion.md) — guía completa del flujo vía UI: conceptos, `Management → Create`, Resources (Datasets/Programs/Tasks), Phases, Leaderboards, formato de submission, publicación y troubleshooting.
- [`templates/dataset-pipeline/`](templates/dataset-pipeline/) — motor genérico (Python, parametrizado por un `spec.yaml` declarativo) para generar la release de un dataset lista para subir a Codabench: descubrimiento de entidades, extracción desde InfluxDB/captia-connect, normalización, split train/test, QA con veredicto PASS/FAIL, EDA y empaquetado de los ZIPs (`public_data`, `reference_data`, `scoring_program`, `starting_kit`). Reutilizable entre proyectos — solo hay que reescribir `spec.yaml`.

## Alcance

Esta documentación es general (no específica de un dataset o competición concreta). Sirve como referencia reutilizable para cualquier competición nueva en Codabench.
