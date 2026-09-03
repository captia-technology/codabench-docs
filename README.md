# Codabench Docs

Guía de referencia para crear y mantener competiciones en [Codabench](https://www.codabench.org/), la plataforma open-source (sucesora de CodaLab) para benchmarks y competiciones de machine learning.

## Contenido

- [`docs/crear-competicion.md`](docs/crear-competicion.md) — guía completa del flujo vía UI: conceptos, `Management → Create`, Resources (Datasets/Programs/Tasks), Phases, Leaderboards, formato de submission, publicación y troubleshooting.
- El motor genérico de generación de datasets (`spec.yaml` + pipeline Python: descubrimiento de entidades, extracción InfluxDB/captia-connect, normalización, split train/test, QA, EDA, empaquetado de ZIPs) vive aparte, en el repo privado [`captia-technology/codabench-dataset-pipeline`](https://github.com/captia-technology/codabench-dataset-pipeline) (acceso restringido).

## Alcance

Esta documentación es general (no específica de un dataset o competición concreta). Sirve como referencia reutilizable para cualquier competición nueva en Codabench.
