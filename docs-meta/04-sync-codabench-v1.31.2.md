# Sincronización con Codabench v1.31.2 — 2026-09-11

La guía se publicó declarando estar contrastada con **v1.23**, la versión que aparecía en las URL
de la documentación oficial que citaba el documento original. `python scripts/check_codabench.py`
avisó de lo que tenía que avisar: Codabench iba ya por **v1.31.2** (27 de agosto de 2026), nueve
publicaciones por delante.

Este es el registro de esa revisión: qué se miró, qué se encontró y qué se cambió.

## Qué se miró, y con qué evidencia

No se ha vuelto a montar una competición sobre una instancia con la v1.31.2. La revisión se apoyó
en dos fuentes, las dos públicas y verificables:

1. **Las notas de publicación** de las nueve versiones entre v1.23 y v1.31.2, en
   `codalab/codabench`.
2. **El código de la etiqueta `v1.31.2`**, comparado con el de `v1.23`. En concreto los
   formularios del editor —`src/static/riot/competitions/editor/*.tag`— y los modelos
   —`src/apps/leaderboards/models.py`, `src/apps/competitions/models.py`—, que son donde viven
   los rótulos, los valores de cada desplegable y los valores por defecto.

El `diff` entre las dos etiquetas es la parte que más ahorra: dice qué cambió **de verdad**, en
vez de obligar a releer la guía entera contra la documentación y adivinar.

## Lo que cambió entre v1.23 y v1.31.2

Menos de lo que el salto de nueve versiones hacía temer. En todo el editor de competición:

| Cambio | Versión | Dónde se reflejó |
|---|---|---|
| El desplegable **Computation** gana la opción `Average Rank` | v1.29 | `evaluacion/leaderboards.md` |
| Los logs de una submission se agrupan en pestañas dinámicas, con aviso cuando no hay nada | v1.26 | `submissions/probar.md` |
| Los desplegables de la fase muestran la descripción de cada recurso bajo su nombre | v1.27 | `evaluacion/phases.md` |
| Se retira del rótulo de **Tasks** una nota que era falsa | v1.27 | — |
| Grupos de participantes con cola propia (encaminamiento por grupo) | v1.28 | `competicion/participation.md` |
| Validación **Human in the Loop** | v1.31 | pendiente, ver abajo |
| El panel de la submission muestra la columna primaria con su precisión | v1.26 | `submissions/probar.md` |

## Lo que no era desfase, sino hueco

El hallazgo de fondo de esta revisión, y el que más contenido añadió: **la mayoría de lo que
faltaba ya existía en la v1.23**. La guía original describía lo que su autor usó al montar una
competición concreta, no el formulario completo, y eso no se ve comparando versiones — solo
leyendo el formulario entero.

Campos que existían desde el principio y que la guía no contaba:

- **Details**: `Competition Docker Image` —con su valor por defecto `codalab/codalab-legacy:py37`,
  que explica el «Docker image que aparece sin haberlo escrito»—, `Competition Type`,
  `Competition Reward`, `Organizer Contact Email`, `Competition Report`, `Fact Sheet`.
- **Participation**: `Allow robot submissions`, `Whitelist Emails`.
- **Phases**: `Start Date`/`Start Time` y `End Date`/`End Time` como campos separados y en UTC+0,
  `Public data` y `Starting kit` asignables por fase, el valor por defecto de
  `Execution Time Limit` (600 s), `Hide Submission Output`, `Hide Prediction Output`,
  `Hide Score Output` y `Auto migrate to this phase`.
- **Leaderboards**: `Column Precision`, `Hidden` por columna, `Leaderboard is Hidden`, el
  desplegable `Apply to:` de las columnas calculadas, y que `Computation` admite `Sum`, `Min` y
  `Max` además de `Average`.
- **Submission rule**: son **seis**, no tres, y la guía citaba tres. Además `Add` —el valor por
  defecto— **no** añade la submission al leaderboard por su cuenta, lo que explica el síntoma
  «la submission se procesó pero no aparece» mejor que la redacción anterior.

## Una afirmación que era falsa

La guía decía del Docker image de la cabecera pública: «es el entorno de ejecución asociado a la
Queue/Task usada, **no algo que se escriba a mano en este flujo**». El síntoma observado era
correcto —aparece sin que nadie lo escriba— pero la explicación no: es el campo
**Competition Docker Image** de la pestaña Details, que el modelo `Competition` inicializa a
`codalab/codalab-legacy:py37`. La corrección importa porque cambia dónde se arregla un
`ModuleNotFoundError` del scoring program.

## Qué queda pendiente

- **Human in the Loop** (v1.31): la casilla existe en Details —«el compute worker pausa tras el
  scoring y espera una validación manual antes de enviar las puntuaciones»— y solo está activa en
  colas privadas. No se documenta todavía porque no se ha probado, y una función de validación
  manual descrita de oídas es peor que no descrita.
- Los campos de **Fact Sheet** y la gestión de **colas** propias siguen sin cubrirse: son otro
  tema, no el recorrido de montar una competición.
- **Contrastar contra una instancia real** con la v1.31.2. Mientras no se haga,
  `referencia/fuentes.md` dice exactamente eso, en el sitio publicado y no solo aquí.
