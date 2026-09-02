# Cómo crear una competición en Codabench

Guía de referencia general para publicar un benchmark/competición en [Codabench](https://www.codabench.org/) (o una instancia self-hosted del mismo). Cubre conceptos, estructura del bundle, configuración YAML, programas de ingestion/scoring, fases, leaderboards y errores comunes.

---

## 1. Conceptos clave

Codabench organiza una competición en piezas reutilizables y componibles:

| Concepto | Qué es |
|---|---|
| **Competition** | La competición en sí: metadata, páginas, fases y leaderboards. |
| **Task** | Une un dataset con un programa de scoring (y opcionalmente de ingestion). Una Task es reutilizable entre varias Phases o competiciones. |
| **Phase** | Una etapa temporal de la competición (ej. `Development`, `Final`). Cada fase referencia una o más Tasks y tiene sus propias fechas de inicio/fin. |
| **Program** | Código ejecutable subido como `.zip`. Hay dos tipos: **Ingestion program** (transforma input del participante en predicciones) y **Scoring program** (compara predicciones contra ground truth y calcula métricas). |
| **Dataset** | Datos de entrada (`input_data`), datos de referencia/ground truth (`reference_data`) y, opcionalmente, un starting kit (`starting_kit`) o datos públicos (`public_data`). |
| **Leaderboard** | Tabla de resultados. Define qué columnas (métricas) mostrar y cómo rankear (asc/desc, selección de mejor submission). |
| **Submission** | Lo que sube un participante: normalmente predicciones (`.zip`) o código (si la competición es *code submission*). |

A diferencia de CodaLab, en Codabench **Task** es una entidad independiente y reusable — no se define inline dentro de cada fase.

---

## 2. Dos formas de crear una competición

1. **Vía UI** (recomendado para empezar): `My Competitions → Create Competition` en la web de Codabench, subiendo un bundle `.zip`.
2. **Vía bundle YAML + zip**: se define todo en `competition.yaml` y se sube el zip completo. Es el método reproducible y versionable — recomendado si vas a mantener la competición en un repo de código.

Esta guía se centra en el método 2, porque es el que permite trazabilidad y control de versiones.

---

## 3. Estructura del bundle

Un bundle de competición es un `.zip` con esta forma típica:

```
mi-competicion/
├── competition.yaml          # Config principal (obligatorio)
├── pages/
│   ├── overview.md
│   ├── data.md
│   ├── evaluation.md
│   └── terms.md
├── logo.png                  # Imagen de la competición (opcional)
├── ingestion_program/
│   ├── ingestion.py
│   └── metadata              # opcional, describe el ejecutable
├── scoring_program/
│   ├── scoring.py
│   └── metadata
├── input_data/                # Datos que ve el participante (dev/test según fase)
├── reference_data/            # Ground truth, usado por el scoring program
├── starting_kit/               # Notebook/ejemplo para el participante (opcional)
└── public_data/                 # Datos públicos descargables (opcional)
```

Al hacer zip, el `competition.yaml` debe quedar en la **raíz** del zip (no dentro de una subcarpeta).

---

## 4. `competition.yaml` comentado

```yaml
version: 2                       # Versión del formato de bundle (usar 2 para Codabench)
title: "Mi Competición de Ejemplo"
description: "Descripción corta, aparece en el listado de competiciones."
image: logo.png                  # Ruta relativa dentro del bundle
registration_auto_approve: true  # false = un admin debe aprobar cada registro
docker_image: codalab/codalab-legacy:py39   # Imagen usada para ejecutar ingestion/scoring

terms: pages/terms.md

pages:
  - title: Overview
    file: pages/overview.md
  - title: Data
    file: pages/data.md
  - title: Evaluation
    file: pages/evaluation.md

tasks:
  - index: 0
    name: "Tarea principal"
    description: "Qué debe predecir el participante."
    ingestion_program: ingestion_program
    scoring_program: scoring_program
    input_data: input_data
    reference_data: reference_data
    starting_kit: starting_kit    # opcional

solutions: []                    # opcional, soluciones de referencia publicables tras cierre

phases:
  - index: 0
    name: "Development"
    description: "Fase de desarrollo, feedback inmediato."
    start: 2026-09-02
    end: 2026-10-15
    tasks:
      - 0                         # índice de la task definida arriba
    is_public: true
    hidden: false

  - index: 1
    name: "Final"
    description: "Fase final, sin feedback hasta el cierre."
    start: 2026-10-15
    end: 2026-10-30
    tasks:
      - 0
    is_public: false

leaderboards:
  - index: 0
    title: "Resultados"
    key: main
    submission_rule: "Force_Last"   # o Add_And_Delete, Force_Best...
    columns:
      - title: "Accuracy"
        key: accuracy
        index: 0
        sorting: desc               # desc = mayor es mejor
        computation: null           # o "avg", "std" si combina varias columnas
```

Puntos que suelen dar problemas:

- **`index` en tasks/phases/leaderboards** debe ser consistente y sin huecos empezando en 0.
- **`docker_image`**: si el scoring program necesita librerías concretas (numpy, sklearn, pandas...), usar una imagen que ya las tenga o construir una propia y publicarla en Docker Hub.
- **Fechas** en UTC. Si `start`/`end` no están bien puestas, la fase puede aparecer cerrada o no visible.
- **`columns.key`** en el leaderboard debe coincidir *exactamente* con la clave que el scoring program escribe en `scores.txt` (ver sección 6).

---

## 5. Ingestion program

El ingestion program traduce la entrada del participante en predicciones evaluables. Es opcional si el participante sube directamente las predicciones (submission de resultados, no de código).

Estructura mínima:

```
ingestion_program/
├── ingestion.py
└── metadata
```

`metadata` (sin extensión) describe cómo ejecutarlo:

```yaml
command: python3 $program/ingestion.py $input $output $program
```

Variables disponibles: `$input` (submission del participante + input_data), `$output` (dónde escribir resultados), `$program` (carpeta del propio ingestion program), `$hidden` (reference_data, si aplica).

Si la competición es de tipo *predicciones directas* (el participante sube ya el `.zip` de predicciones), se puede omitir el ingestion program por completo y el scoring program consume directamente la submission.

---

## 6. Scoring program

Compara la salida del ingestion program (o la submission directa) contra `reference_data` y escribe las métricas.

```
scoring_program/
├── scoring.py
└── metadata
```

`metadata`:

```yaml
command: python3 $program/scoring.py $input $output
```

El scoring program debe escribir un fichero `scores.txt` en `$output` con formato `clave: valor`:

```
accuracy: 0.8721
f1_score: 0.8390
```

Estas claves son las que se referencian en `leaderboards[].columns[].key` del `competition.yaml`. Si no coinciden, la columna aparece vacía en el leaderboard sin error explícito — es el fallo más común al montar una competición nueva.

---

## 7. Fases (Phases)

- Cada fase referencia una o varias `tasks` por índice.
- `is_public: true` en Development permite feedback inmediato al participante tras cada submission.
- La fase Final suele tener `is_public: false` para evitar overfitting al leaderboard público (los resultados solo se revelan al cerrar la competición).
- El paso de una fase a otra es automático según fechas (`start`/`end`), no requiere intervención manual salvo que se reconfigure.
- Se pueden reutilizar las mismas `tasks` entre fases (útil cuando dev y final comparten scoring program pero cambian el dataset oculto).

---

## 8. Leaderboards

- `submission_rule` controla qué submission de un participante cuenta:
  - `Force_Last`: solo la última cuenta.
  - `Force_Best`: se queda con la mejor según la métrica principal.
  - `Add_And_Delete`: el participante puede elegir manualmente cuál mostrar.
- Se pueden definir varias columnas y marcar cuál ordena el ranking (normalmente la primera, o la que tenga `sorting` definido y sea la métrica principal).
- `computation` permite combinar múltiples runs (ej. media de varias fases) si la task se ejecuta más de una vez.

---

## 9. Publicar y probar

1. Empaquetar la carpeta en `.zip` (competition.yaml en la raíz).
2. En Codabench: `My Competitions → Create Competition → Upload` y seleccionar el zip.
3. Codabench valida el YAML; si hay errores de sintaxis o de referencias (índices, ficheros no encontrados) los reporta en la propia UI.
4. Hacer una submission de prueba (dummy) en Development antes de anunciar la competición, para verificar que:
   - el ingestion program corre sin errores,
   - el scoring program produce `scores.txt` con las claves esperadas,
   - el leaderboard muestra los valores correctamente.
5. Iterar: se puede volver a subir un bundle actualizado ("Edit Competition → Upload new bundle") sin perder registros de participantes, aunque **sí** puede resetear submissions según qué se cambie (tasks/phases). Revisar el changelog de submissions tras cada actualización de bundle en producción.

---

## 10. Troubleshooting común

| Síntoma | Causa probable |
|---|---|
| Leaderboard vacío o con `-` | La `key` en `columns` no coincide con la clave escrita en `scores.txt`. |
| Submission se queda en "Running" indefinidamente | Timeout del docker_image, o excepción no capturada en ingestion/scoring (revisar logs de la submission, botón "stderr"/"stdout"). |
| Error al subir el bundle: "Invalid YAML" | Indentación incorrecta o `competition.yaml` no está en la raíz del zip. |
| Fase no aparece / sigue en la anterior | Fechas `start`/`end` mal puestas o en huso horario distinto al esperado (usar UTC). |
| Participante no puede subir submission | `registration_auto_approve: false` y el registro no ha sido aprobado manualmente por un admin. |
| Scoring program falla con `ModuleNotFoundError` | La `docker_image` no incluye la librería usada; usar una imagen con más dependencias o construir una custom. |
| Columnas de leaderboard en orden incorrecto | El `index` de cada columna no refleja el orden deseado. |

---

## Referencias

- Documentación oficial: https://www.codabench.org/docs/
- Repo del proyecto (Codalab-competitions / Codabench en GitHub): buscar `codalab/codabench` en GitHub para ver bundles de ejemplo (`competition_examples/`) que sirven como plantilla real.
