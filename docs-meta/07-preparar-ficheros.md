# 07 — Preparar los ficheros de una competición

**Fecha:** 2026-11-11. **Estado:** plan aprobado el 2026-11-11 (P1 y P3 sí, P5 no; ver notas). **Issue:** #7. **Rama:** `preparar-ficheros`.

## Qué se pide y por qué

Hoy la guía empieza cuando los cuatro zip ya existen. La portada y «Requisitos previos» lo dicen
así, y para generarlos remiten a un repositorio privado al que el lector no tiene acceso y que,
además, solo prepara competiciones de clasificación. Un docente que quiera montar su propia
competición se queda atascado en el primer paso.

La issue #7 pide cubrir ese hueco con dos caminos que acaban en los mismos cuatro zip, más una
comprobación antes de subirlos:

1. **Automático:** el docente sube el CSV que descarga de captia.ai (Variables → Dataset) a una
   herramienta de la guía, elige qué hay que predecir y dónde se corta la prueba, y descarga los
   zip.
2. **A mano:** una página explica qué lleva cada zip y las reglas que más fallan, y ofrece un
   programa de puntuación genérico listo para usar.
3. **Comprobar mis ficheros:** la herramienta revisa unos zip hechos a mano y dice qué corregir.

**Regla de la issue:** en captia.ai no aparece nada de Codabench. Solo se usa su descarga genérica
de datos.

## Lo que hay hoy

| Dónde | Qué dice |
|---|---|
| `docs/index.mdx`, bloque «Antes de llegar aquí» | Los cuatro zip se generan con un repositorio privado |
| `docs/empezar/requisitos.md`, aviso «De dónde salen estos ficheros» | Generarlos queda fuera del alcance de la guía |
| `docs/recursos/scoring-program.md` | El contrato del programa de puntuación: `metadata`, rutas `$input/ref` y `$input/res`, `scores.json` |
| `docs/submissions/formato.md` | El formato del envío y sus errores habituales |
| `src/` | Solo el tema y la portada, copia exacta del design system |
| CI (`docs-ci.yml`) | `check_docs.py`, `build_nav.py --check`, pruebas del middleware con `node --test` y build |

Lo que la guía ya explica (los cuatro tipos de recurso, el programa de puntuación por dentro y el
formato del envío) no se repite: las páginas nuevas enlazan a esas.

## Decisiones propuestas

Aprobadas el 2026-11-11: P1 y P3 sí; P5 cambia (no se convierte el formato ancho). La verificación en una competición real (T10) queda pendiente y **no bloquea la publicación**: la herramienta se publica antes y no se presenta como verificada en Codabench hasta que T10 se haga.

| # | Decisión | Por qué |
|---|---|---|
| P1 | Sección nueva **«Preparar los ficheros»** (`docs/preparar/`) entre «Antes de empezar» y «Crear la competición», con tres páginas: `index.md` (los dos caminos), `herramienta.mdx` (generar y comprobar) y `a-mano.mdx` (qué lleva cada zip y el programa genérico) | Es el orden real: los ficheros se preparan antes de abrir el editor |
| P2 | La herramienta es un componente React en `src/components/PrepararFicheros/`, usado desde los `.mdx`. La lógica va aparte, en módulos `.mjs` sin React | Los módulos sin React se prueban con `node --test` en CI, igual que el middleware |
| P3 | **Sin dependencias nuevas.** CSV con un lector propio (RFC 4180), zip con las API nativas `CompressionStream` y `DecompressionStream` (`deflate-raw`) y un CRC32 propio. Si el navegador no tiene `CompressionStream`, el zip se guarda sin comprimir | Evita añadir y mantener un paquete. Las API están en Chrome y Edge 80+, Firefox 113+ y Safari 16.4+ |
| P4 | Todo ocurre en el navegador: el CSV y los zip no se envían a ningún sitio, y la página lo dice | Los datos son del centro y no deben salir de su ordenador |
| P5 | **Solo el formato largo:** una fila por caso, con columna de tiempo y, si hay varios grupos, columna de grupo. La descarga actual de captia.ai de **un solo equipo** ya sale así. El formato ancho de varios equipos (`variable__equipo`) se rechaza con un mensaje que explica qué hacer | Decidido el 2026-11-11: no se convierte el formato ancho. La descarga de varios equipos en formato largo llega con captia-technology/captia.ai#850 |
| P6 | **Tipo de competición detectado por la columna a predecir:** números con más de 10 valores distintos → regresión (MAE principal y RMSE, mejor cuanto más bajo); texto o 10 valores o menos → clasificación (aciertos y F1 macro sobre las clases presentes en la solución, mejor cuanto más alto). El docente puede cambiarlo | El docente no tiene por qué saber qué métrica usar; la herramienta propone y explica |
| P7 | **Reparto por tiempo, nunca al azar:** por defecto, el último 20 % cronológico va a la prueba; también se puede elegir una fecha de corte. Sin columna de tiempo, el último 20 % en el orden del fichero, con aviso. Las filas sin respuesta se quitan | Un reparto al azar mete la misma hora en entrenamiento y en prueba y da notas irreales |
| P8 | `id` generado si no existe: `<grupo>_<AAAAMMDDHHMM>`, o el número de fila | La solución y el envío se emparejan por `id` |
| P9 | **Programa de puntuación genérico:** un único `score.py`, solo biblioteca estándar y compatible con Python 3.7 (la imagen por defecto), configurado con `config.json` (`{"columna": "...", "tipo": "numero"}` o `"categoria"`). Claves fijas: `mae`, `rmse` y `n`, o `aciertos`, `f1` y `n`. Errores en español. Fuente única en `static/plantillas/puntuacion/`, que la herramienta lee para empaquetarlo | Un solo programa para todas las competiciones; un docente que lo use a mano solo toca el `config.json` |
| P10 | **Kit de inicio básico:** README, solución de referencia sin dependencias (regresión: media por grupo y hora, o media global; clasificación: clase más frecuente), `validar_envio.py` y `hacer_envio_zip.py` | Lo mínimo para que un participante envíe algo válido en minutos |
| P11 | **Lo que se descarga:** los cuatro zip por separado y un «Descargar todo» con los cuatro, unas `INSTRUCCIONES.md` (columnas del leaderboard con su `Sorting`) y textos base para las páginas (`paginas/*.md`) | El orden de las columnas es el fallo que más se repite; mejor dárselo escrito |
| P12 | **Comprobar mis ficheros** revisa: ficheros en la raíz de cada zip, `metadata` con `command`, `config.json` válido, `train.csv` y `test.csv` presentes, que `test.csv` no lleve la columna de la respuesta, que los `id` de solución y prueba coincidan, separador `;` y codificación que no sea UTF-8 | Son los fallos que en Codabench solo aparecen como envío fallido |
| P13 | Ningún dato real en el repositorio: las pruebas y los ejemplos usan datos sintéticos (`AULA01`, `AULA02`…) | El repositorio es público |

## Tareas

| Tarea | Qué | Commit |
|---|---|---|
| T1 | Este plan | `docs(preparar-ficheros): plan …` |
| T2 | `score.py` genérico y `config.json` de ejemplo, con pruebas `unittest` y su paso en CI | `feat(preparar-ficheros): programa de puntuación genérico …` |
| T3 | Módulo de lógica: leer CSV, detectar formato y convertir el ancho, detectar el tipo, repartir, generar `id`, referencias y contenido de cada fichero. Pruebas `node --test` con datos sintéticos y paso en CI | `feat(preparar-ficheros): lógica …` |
| T4 | Módulo zip: crear (deflate nativo, sin comprimir si no hay) y leer, con CRC32. Pruebas `node --test` | `feat(preparar-ficheros): zip …` |
| T5 | Plantillas del kit de inicio, de las instrucciones y de los textos base | `feat(preparar-ficheros): kit …` |
| T6 | Componente `PrepararFicheros` (generar y comprobar) con los tokens del tema, leyendo antes el contrato de diseño | `feat(preparar-ficheros): componente …` |
| T7 | Páginas de `docs/preparar/`, declaradas en `SECCIONES`, con `build_nav.py --apply` y `check_docs.py` | `docs(preparar-ficheros): páginas …` |
| T8 | Retoques: portada, `requisitos.md`, `CLAUDE.md`, el perfil del repositorio de la skill y `docs-meta/README.md` | `docs(preparar-ficheros): …` |
| T9 | Verificación local: validadores, pruebas, build y QA visual en los dos temas y en móvil | sin commit si no cambia nada |
| T10 | **Evidencia real (pendiente, sin fecha; no bloquea la publicación):** montar en codabench.org dos competiciones privadas con zips generados por la herramienta a partir de datos sintéticos, una de regresión y otra de clasificación, enviar el envío de ejemplo y anotar aquí lo observado | `docs(preparar-ficheros): evidencia …` |
| T11 | Revisión de lector, separando exactitud y comprensión | correcciones, si las hay |
| T12 | PR contra `master`, solo con autorización, y comprobación de la preview de Vercel | — |

## Verificación

- `python scripts/check_docs.py` y `python scripts/build_nav.py --check`.
- Pruebas: las del programa de puntuación (`unittest`), las de la lógica y del zip (`node --test`) y las del middleware.
- `npm run build`, sin `--locale`.
- QA visual de la herramienta: los dos temas, teclado y anchura de móvil.
- T10: que una competición generada se puntúe en Codabench de verdad. Un build en verde no lo demuestra.

## Riesgos

| Riesgo | Mitigación |
|---|---|
| La descarga de varios equipos de captia.ai sale en formato ancho hasta la #850 | La herramienta lo detecta y explica que hay que descargar un equipo o esperar a la descarga nueva |
| Un navegador sin `CompressionStream` | Zip sin comprimir; los ficheros son algo más grandes pero válidos |
| La imagen de Codabench no tiene una librería | `score.py` solo usa la biblioteca estándar |
| Detección del tipo equivocada | El docente puede cambiarla, y la herramienta explica por qué eligió |

## Nota sobre el perfil del repositorio

`.claude/skills/code-documentation/references/perfil-repositorio.md` dice todavía que el sitio es
público y sin autenticación. Desde el 2026-10-28 pide credencial (`06-control-de-acceso.md`). Se
corrige en T8.
