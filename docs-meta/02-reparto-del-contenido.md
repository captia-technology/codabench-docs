# El reparto del contenido — de un fichero a 23 páginas

De dónde sale cada página del sitio. Este documento es la **trazabilidad del contenido**: permite
comprobar, fila a fila, que el reparto no perdió nada y que ninguna página se escribió de la nada.

## Qué había y qué hay

Todo el contenido de este repositorio era **un solo fichero**: `docs/crear-competicion.md`, 236
líneas, con un preámbulo, 14 secciones numeradas y una lista de Referencias. Funcionaba leído de
arriba abajo en GitHub y tenía tres límites que un fichero suelto no resuelve:

- **No se puede enlazar a un paso.** Los enlaces internos eran anclas a títulos numerados
  (`#11-formato-de-submission-...`), que se rompen en cuanto se inserta una sección o se renumera.
- **No hay búsqueda.** Con 236 líneas se busca con `Ctrl+F`; el problema es que la guía crece.
- **No hay forma de decir contra qué versión está contrastado** lo que dice, ni de saber qué
  páginas revisar cuando Codabench cambie.

Hoy son **23 páginas repartidas en 6 secciones** —6 páginas índice y 17 de detalle—, más la
portada (`docs/index.mdx`) y el mapa generado (`docs/mapa-de-la-guia.md`): 25 ficheros en `docs/`.

## La regla del reparto

**No se reescribe la prosa, no se inventa material nuevo y no se pierde ni una fila de tabla ni un
enlace.** El contenido se mueve; no se reinterpreta.

Lo único que se añade son:

- **Las 6 páginas índice**, una por sección: texto puente corto que dice qué hay en la sección y en
  qué orden leerla. No reproducen el procedimiento de sus páginas —los pasos se leen una sola vez,
  donde tocan—, pero sí adelantan el aviso que hace que merezca la pena entrar: `evaluacion/index.md`
  anticipa que una `Column Key` que no coincide con `scores.txt` deja la columna vacía sin error, y
  `recursos/index.md` que una Task sin crear no aparece en el desplegable de la fase. Un índice que
  solo enumera títulos no ayuda a decidir por dónde entrar.
- **La portada** (`docs/index.mdx`), que es navegación: cuatro entradas por la pregunta que trae el
  lector, las seis secciones y cómo se lee una página.
- **El mapa** (`docs/mapa-de-la-guia.md`), **generado** por `scripts/build_nav.py`.
- **Los enlaces internos reescritos**, de anclas numeradas a enlaces relativos entre documentos.

La razón de la regla es simple: la guía original no es un borrador, es contenido contrastado contra
la interfaz y contra una competición real ya montada. Un reparto que además reescribe mezcla dos
trabajos —mover y revisar— y hace imposible saber, después, si una frase cambió porque se movió o
porque alguien decidió que decía otra cosa.

## La correspondencia, sección a sección

| Sección del original | Líneas | Destino |
|---|---|---|
| Preámbulo (qué cubre, flujo UI frente a bundle) | 1–8 | `empezar/index.md` — «Antes de empezar» |
| 1. Conceptos clave | 9–26 | `empezar/conceptos.md` — «Conceptos clave» |
| 2. Requisitos previos | 27–44 | `empezar/requisitos.md` — «Requisitos previos» |
| 3. Crear la competición (Details) | 45–60 | `competicion/details.md` — «Details» |
| 4. Participation | 61–69 | `competicion/participation.md` — «Participation» |
| 5. Pages | 70–83 | `competicion/pages.md` — «Pages» |
| 6. Recursos: Datasets/Programs | 84–100 | `recursos/datasets-programs.md` — «Datasets y Programs» |
| 7. Crear la Task | 101–116 | `recursos/tasks.md` — «Tasks» |
| 8. Phases | 117–135 | `evaluacion/phases.md` — «Phases» |
| 9. Leaderboards | 136–160 | `evaluacion/leaderboards.md` — «Leaderboards» |
| 10. Collaborators (opcional) | 161–166 | `competicion/collaborators.md` — «Collaborators» |
| 11. Formato de submission en competiciones de predicciones directas | 167–188 | `submissions/formato.md` — «Formato de submission» |
| 12. Probar la competición | 189–201 | `submissions/probar.md` — «Probar la competición» |
| 13. Submission rule del leaderboard | 202–211 | `evaluacion/submission-rule.md` — «Submission rule» |
| 14. Troubleshooting común | 212–228 | `referencia/troubleshooting.md` — «Troubleshooting» |
| Referencias | 229–236 | `referencia/fuentes.md` — «Fuentes y documentación oficial» |

Los rangos de línea son los del fichero tal como estaba en el commit `495599a`, que es el último
que lo tocó antes del reparto.

Las páginas que **no** salen de una sección del original son las 6 índices —`empezar/index.md`
comparte destino con el preámbulo, y `competicion/`, `recursos/`, `evaluacion/`, `submissions/` y
`referencia/` estrenan la suya—, la portada y el mapa.

## Tres secciones cambian de sitio, y por qué

El orden numérico del original es el orden en que se fue descubriendo la plataforma. El del árbol
es el orden en que se **monta** una competición. Tres secciones se mueven:

**10. Collaborators vuelve a Competición.** En la interfaz, **Collaborators** es una pestaña más
del editor, al lado de **Details**, **Participation** y **Pages**. En el original quedó la décima
porque se documentó al final, pero leerla ahí obliga a volver al editor cuando ya se estaba en
Phases. Dentro de la sección, el orden es el de las pestañas: Details → Participation → Pages →
Collaborators.

**13. Submission rule sube a Evaluación, junto a Leaderboards.** No es una sección aparte: es una
propiedad del leaderboard —qué submission de cada participante se muestra—. Estaba once secciones
más abajo que la pantalla que configura, y esa distancia es justamente lo que hace que se olvide.

**11 y 12 se agrupan en Submissions.** El formato de la entrega y la prueba de punta a punta son
dos caras de lo mismo: qué se sube y cómo se comprueba que puntúa. Comparten sección para que la
segunda se lea justo después de la primera.

## Los enlaces internos

El original enlazaba con anclas a sus propios títulos numerados
(«ver sección 11», `#11-formato-de-submission-en-competiciones-de-predicciones-directas`). Esas
anclas **ya no existen**: los títulos de las páginas nuevas no llevan número.

Pasan a ser enlaces relativos entre documentos, con la extensión `.md`, que es lo que Docusaurus
resuelve y lo que `scripts/check_docs.py` comprueba contra el sistema de ficheros con la caja
exacta:

```markdown
[formato de submission](../submissions/formato.md)
```

Cero anclas a secciones numeradas que ya no existen. Y como `onBrokenLinks` está en `'throw'`, un
enlace mal reescrito tumba el build en vez de publicarse roto.

## El original se retira

Una vez repartido, `docs/crear-competicion.md` se borra. Es deliberado, y no pierde nada:

- **Su contenido está en el sitio**, repartido en las 16 páginas de la tabla de arriba.
- **Su versión íntegra está en el historial de git**, en los commits `eecdb2a` (la guía inicial),
  `4c9a7b7` (el reenfoque al flujo por interfaz web), `c2942bb` (las observaciones de una
  competición real) y `495599a` (la referencia al repositorio que genera los ficheros). Se
  recupera entera con:

  ```bash
  git show 495599a:docs/crear-competicion.md
  ```

Dejarlo en `docs/` sería peor que borrarlo: se publicaría como una página vigente que dice lo mismo
que otras dieciséis, competiría con ellas en la búsqueda del sitio y en Google, y sería el sitio
donde alguien corregiría algo sin que la corrección llegara a las páginas de verdad. Dos copias del
mismo contenido divergen siempre; la única pregunta es cuándo.

Además, `scripts/build_nav.py` no lo permitiría: en la raíz de `docs/` solo pueden vivir la portada
y el mapa, y cualquier documento sin declarar en `SECCIONES` hace fallar el script y con él el CI.

## Las tres desviaciones del traslado, y por qué se aceptan

La regla del reparto es que la prosa no se reescribe. Se cumplió salvo en tres puntos, y quedan
aquí anotados porque una desviación sin registrar se lee después como deriva silenciosa:

**1. Una corrección de concordancia.** El original decía «si el leaderboard no se actualiza
**sola**»; en `submissions/probar.md` dice «no se actualiza **solo**». El sujeto es *el
leaderboard*. Revertirlo reintroduciría el error, así que se queda —pero es un cambio de texto y
no puede pasar por traslado literal.

**2. Tres frases de contexto que el original no tenía.** En `empezar/requisitos.md` (de dónde
salen los `.zip`), en `evaluacion/leaderboards.md` (que la submission rule decide qué fila se ve) y
en `evaluacion/submission-rule.md` (que una submission ya procesada puede necesitar la acción
manual). Ninguna inventa un hecho: las tres se derivan de material que sí está en el original —la
última entrada de «Referencias», la sección 13 y el paso 5 de la sección 12— y existen porque al
partir un documento en dieciséis, lo que antes se leía tres párrafos más abajo pasa a estar en otra
página. Sin ellas, el enlace queda sin explicar por qué se sigue.

**3. Los pies de recorrido.** Ninguna página del original terminaba con «Siguiente paso»: era un
único documento y el siguiente paso era la línea de abajo. Al repartirlo hay que reconstruir ese
hilo. La norma que siguen —y las dos excepciones— está en
[`.claude/rules/documentacion.md`](../.claude/rules/documentacion.md).

Lo que **no** ocurrió: ninguna fila de tabla, ningún enlace y ningún matiz del original se quedó
fuera. Comprobado línea a línea contra las 164 líneas no vacías del documento de partida —de sus
236, contadas con `git show 495599a:docs/crear-competicion.md | grep -c '[^[:space:]]'`—.

## Cómo comprobar que el reparto está completo

```bash
python scripts/check_docs.py          # enlaces, tablas, front matter, invariantes
python scripts/build_nav.py --check   # que las 23 páginas estén declaradas y colocadas
npm run build                         # onBrokenLinks: 'throw' — un enlace roto no pasa de aquí
```

Y para la parte que ninguna herramienta puede comprobar —que ninguna frase se quedó por el
camino—, la tabla de arriba con el original delante:

```bash
git show 495599a:docs/crear-competicion.md | sed -n '167,188p'   # p. ej., la sección 11
```
