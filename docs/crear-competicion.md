# Cómo crear una competición en Codabench (vía UI)

Guía de referencia para publicar un benchmark/competición en [Codabench](https://www.codabench.org/) usando el **editor web** (formularios, sin escribir `competition.yaml` a mano ni subir un bundle `.zip` completo). Es el flujo recomendado para crear y mantener una competición directamente desde la interfaz.

> Codabench también admite crear la competición subiendo un bundle `.zip` con un `competition.yaml` (útil para versionar en un repo). Esta guía no cubre ese método — ver [Referencias](#referencias) si se necesita en el futuro.

---

## 1. Conceptos clave

Antes de tocar la UI, conviene tener claros los bloques con los que se construye una competición:

| Concepto | Qué es |
|---|---|
| **Competition** | La competición en sí: título, descripción, páginas, fases y leaderboards. |
| **Dataset** | Datos subidos como recurso: `input_data` (lo que ve el participante), `reference_data` (ground truth), `public_data` o `starting_kit`. |
| **Program** | Código ejecutable subido como recurso. Dos tipos: **Ingestion program** (transforma la submission del participante en predicciones) y **Scoring program** (compara predicciones contra `reference_data` y calcula métricas). |
| **Task** | Combina Datasets + Programs (input_data, reference_data, ingestion program, scoring program). Se crea una vez y se reutiliza en una o varias Phases. |
| **Phase** | Etapa temporal de la competición (ej. `Development`, `Final`). Referencia una o varias Tasks y tiene sus propias fechas y límites de submission. |
| **Leaderboard** | Tabla de resultados: columnas (métricas), orden de ranking y regla de qué submission de cada participante se muestra. |
| **Submission** | Lo que sube un participante: predicciones o código, según cómo esté configurada la Task. |

Los recursos (Datasets/Programs) y las Tasks se crean **una sola vez** y luego se reutilizan al vincularlos desde las Phases — no se suben de nuevo por cada fase.

---

## 2. Requisitos previos

- Cuenta creada en la instancia de Codabench que se vaya a usar (p. ej. codabench.org o una instancia propia).
- Los ficheros ya preparados y comprimidos en `.zip` por separado:
  - `input_data.zip`
  - `reference_data.zip`
  - `ingestion_program.zip` (opcional si la competición es de predicciones directas)
  - `scoring_program.zip`
  - `starting_kit.zip` / `public_data.zip` (opcionales)
- Cada programa (`ingestion_program`, `scoring_program`) debe incluir dentro un fichero `metadata` (sin extensión) que indique el comando a ejecutar, por ejemplo:

  ```yaml
  command: python3 $program/scoring.py $input $output
  ```
- Conviene nombrar los zips de forma que se identifiquen sin ambigüedad al elegirlos en los desplegables de la UI, p. ej. `reference_data_<slug>_<version>.zip`, `scoring_program_<slug>_<version>.zip`, `<slug>_<version>_public_data.zip`, `<slug>_<version>_starting_kit.zip` — sobre todo si se van a crear varias versiones/fases de la misma competición y conviven varios recursos con nombres parecidos en **Resources → Datasets/Programs**.

---

## 3. Crear la competición (Details)

1. En el menú superior: **Benchmarks → Management**.
2. Click en **Create** (botón arriba a la derecha de Competition Management).
3. Se abre el editor de la competición con varias pestañas. Rellenar **Details**:
   - **Title**: nombre de la competición.
   - **Logo**: imagen identificativa.
   - **Description**: resumen que aparece en el listado de competiciones.
   - **Queue**: cola de procesamiento de submissions (usar la que corresponda; por defecto la pública si no se tiene una propia configurada).

En este punto la competición ya existe (en borrador) y se puede seguir editando en cualquier momento.

> La cabecera pública de la competición muestra siempre un **Docker image** (p. ej. `codalab/codalab-legacy:py37`), aunque toda la competición se haya montado por UI sin tocar YAML — es el entorno de ejecución asociado a la Queue/Task usada, no algo que se escriba a mano en este flujo.

---

## 4. Participation

Pestaña **Participation**:

- **Terms**: términos y condiciones de la competición (texto/markdown). Se muestran en un modal antes de registrarse y también quedan disponibles como pestaña "Terms" dentro de la competición pública.
- **Auto Approve Registration**: si está marcado, cualquiera que se registre entra automáticamente; si no, la competición muestra "This competition requires approval from the competition organizers" y un organizador debe aprobar cada registro manualmente (**Resources → Participants**) antes de que el participante pueda enviar submissions.

---

## 5. Pages

Pestaña **Pages** — contenido informativo que verán los participantes como pestañas dentro de la competición pública (Overview, Data, Evaluation, etc.):

1. Click **Add page**.
2. Rellenar **Title** y **Content** (markdown).
3. Repetir por cada página necesaria.

Se puede enlazar entre páginas usando anchors del tipo `_tab_page0`, `_tab_page1`, `_tab_page_term` (para la pestaña de Terms).

Patrón habitual de páginas en una competición de tipo "predicciones directas": `Overview` (objetivo, flujo de trabajo resumido), `Data` (estructura del dataset, columnas públicas/excluidas, split train/test), `Evaluation` (métrica principal, formato exacto de submission, reglas de validación), `Submission` (paso a paso para generar y subir la entrega), `FAQ`, y opcionalmente `Files` (enlaces directos de descarga a los recursos públicos — Public Data, Starting Kit — dejando claro qué NO debe descargar el participante, p. ej. `reference_data`/`scoring_program`, aunque esos recursos ya son privados por configuración en Resources).

---

## 6. Recursos: Datasets/Programs

Antes de crear una Task hacen falta los recursos que va a usar. Ir a **Resources → Datasets/Programs** (accesible también desde el botón **Manage Tasks/Datasets** dentro de la pestaña Phases):

1. Click **Add Dataset/Program**.
2. Rellenar nombre, subir el `.zip` correspondiente y seleccionar el tipo de recurso.
3. Repetir para cada uno:
   - `input_data`
   - `reference_data`
   - `ingestion_program` (si aplica)
   - `scoring_program`
   - `starting_kit` / `public_data` (opcionales)

Los recursos se pueden marcar como públicos o privados, y son reutilizables entre Tasks y entre competiciones propias.

---

## 7. Crear la Task

Ir a **Resources → Tasks**:

1. Click **Create Task**.
2. Rellenar **nombre** y **descripción** de la task (qué debe predecir/resolver el participante).
3. Seleccionar de los recursos ya subidos en el paso anterior:
   - Input data
   - Reference data
   - Ingestion program (opcional)
   - Scoring program (obligatorio)

Codabench permite tener varias Tasks por competición y asignar más de una Task a la misma Phase — útil si la competición tiene varias subtareas evaluadas por separado.

---

## 8. Phases

Volver al editor de la competición, pestaña **Phases**:

1. Crear una fase (p. ej. `Development`) con:
   - **Name** y **Description**.
   - **Start** / **End** (en UTC).
   - **Tasks**: asignar la(s) Task(s) creada(s) en el paso 7.
   - **Execution Time Limit**: límite de tiempo (segundos) para que corran ingestion/scoring por submission.
   - **Max submissions per day**: límite diario por participante (medianoche a medianoche UTC).
   - **Max submissions per person**: tope total por participante.
2. Repetir para cada fase adicional (p. ej. `Final`), reutilizando la misma Task si el scoring program no cambia, o creando una Task nueva si cambia el dataset oculto.

La fase Development normalmente da feedback inmediato al participante; la fase Final suele ocultar resultados hasta el cierre de la competición para evitar overfitting al leaderboard público.

Si **End** se deja vacío, la fase queda abierta indefinidamente (la cabecera pública muestra "Current Phase Ends: Never") — es válido para competiciones internas de validación sin fecha de cierre fija.

---

## 9. Leaderboards

Pestaña **Leaderboards**:

1. Crear un leaderboard: **Title** y **Key** (identificador único, preferiblemente en minúsculas).
2. Añadir columnas, una por cada métrica que devuelva el scoring program:
   - **Title**: nombre visible de la columna.
   - **Column Key**: debe coincidir *exactamente* con la clave que el scoring program escribe en `scores.txt` (ver más abajo).
   - **Sorting**: ascendente o descendente (según si menor o mayor valor es mejor).
   - **Primary Column**: marca cuál es la columna principal de ranking.
   - **Computation**: `None` normalmente, o `Average` si la columna es la media calculada de otras columnas (en ese caso no recibe score directo del scoring program).

El scoring program debe escribir un `scores.txt` con líneas `clave: valor`, por ejemplo:

```
accuracy: 0.8721
f1_score: 0.8390
```

Si la `Column Key` no coincide con la clave de `scores.txt`, la columna aparece vacía en el leaderboard sin error explícito — es el fallo más frecuente al montar el leaderboard.

Mientras no haya ninguna submission añadida al leaderboard, la pestaña **Results** muestra "No visible leaderboard for this benchmark" — es el estado normal antes de la primera submission válida, no un error de configuración.

---

## 10. Collaborators (opcional)

Pestaña **Collaborators**: añadir otros organizadores buscando por usuario o email, para que puedan editar la competición sin compartir la cuenta principal.

---

## 11. Formato de submission en competiciones de predicciones directas

Cuando la Task no tiene ingestion program (participante sube ya las predicciones, no código), el propio **scoring program** es responsable de validar la entrega antes de puntuar. Conviene documentar el formato exacto en la página `Evaluation`/`Submission` y hacer que el scoring program falle con un mensaje claro si no se cumple. Patrón típico:

- El participante sube un `.zip` con un único CSV **en la raíz** (no dentro de una carpeta), p. ej. `submission.zip → submission.csv`.
- El CSV tiene columnas fijas y conocidas de antemano, p. ej. `id,prediccion_iaq_class`.
- El scoring program valida, antes de calcular métricas:

| Error típico | Causa |
|---|---|
| `Only zip files are allowed` | Se subió el CSV suelto en vez de un `.zip`. |
| `Missing submission.csv` | El zip no contiene el fichero con el nombre exacto esperado. |
| `submission.csv inside folder` | El CSV está dentro de una subcarpeta en vez de en la raíz del zip. |
| `Invalid columns` | Las columnas no coinciden exactamente (nombre u orden) con lo esperado. |
| `IDs mismatch` | Faltan o sobran IDs respecto a `test.csv`/`reference_data`. |
| `Duplicate IDs` | Hay una fila repetida para el mismo ID. |
| `Prediction out of range` | El valor predicho no pertenece al conjunto de clases/valores válidos. |

Publicar una **sample submission** de referencia (con un resultado esperado conocido, p. ej. "si subes la sample oficial deberías obtener `metric = X`") ayuda a que los participantes detecten pronto si algo en su entorno (fase, dataset, versión) no está bien apuntado, antes de perder tiempo con su propio modelo.

---

## 12. Probar la competición

1. Publicar (o dejar en modo no listado) la competición y entrar a su página pública.
2. Pestaña **My Submissions**: subir una submission de prueba (`.zip`) — dummy o real.
3. Seguir los logs en tiempo real mientras se procesa (stdout/stderr disponibles por submission).
4. Verificar:
   - que el ingestion program (si existe) corre sin errores,
   - que el scoring program genera `scores.txt` con las claves esperadas,
   - que el leaderboard muestra el valor correctamente.
5. Si el leaderboard no se actualiza sola: ir a **Resources → Submissions**, localizar la submission procesada y usar el botón de acción **añadir a leaderboard** (según la `submission_rule` configurada, puede requerirse esta acción manual la primera vez).

---

## 13. Submission rule del leaderboard

Se configura al crear/editar el leaderboard y controla qué submission de cada participante se muestra:

- **Force Last**: solo la última submission cuenta.
- **Force Best**: se muestra automáticamente la mejor según la columna principal.
- **Add and Delete (Multiple)**: el propio participante elige manualmente cuál mostrar entre sus submissions.

---

## 14. Troubleshooting común

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
| Submission rechazada con `Only zip files are allowed` / `Missing submission.csv` / `Invalid columns` / `IDs mismatch` | Formato de entrega no válido — ver [sección 11](#11-formato-de-submission-en-competiciones-de-predicciones-directas); reforzar la validación y el mensaje de error dentro del propio scoring program. |
| Sample submission da un resultado distinto al esperado (p. ej. `n` de filas no coincide) | La fase probablemente no está apuntando al `reference_data` correcto de esa versión del dataset. |

---

## Referencias

- [Getting started with Codabench](https://docs.codabench.org/latest/Organizers/Benchmark_Creation/Getting-started-with-Codabench/)
- [Competition Creation Form](https://docs.codabench.org/latest/Organizers/Benchmark_Creation/Competition-Creation-Form/)
- [Resource Management (Submissions, Datasets/Programs, Tasks)](https://docs.codabench.org/v1.23/Organizers/Running_a_benchmark/Resource-Management/)
- [How to Create your First Benchmark on Codabench (tutorial completo)](https://adrienpavao.com/blog/codabench-tuto/codabench-tuto.html)
- Método alternativo (bundle YAML + zip, versionable en repo): [Competition Creation Bundle](https://docs.codabench.org/latest/Organizers/Benchmark_Creation/Competition-Creation-Bundle/)
- Para generar los ficheros (`public_data`, `reference_data`, `scoring_program`, `starting_kit`) antes de llegar a esta guía: [`../templates/dataset-pipeline/`](../templates/dataset-pipeline/), motor genérico parametrizado por `spec.yaml`.
