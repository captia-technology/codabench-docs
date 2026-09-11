# «Codabench v1.23» — de dónde sale esa etiqueta

Este sitio se presenta como **contrastado con Codabench v1.23**. Aparece en el desplegable de
versión del navbar, en el pie de todas las páginas, en la portada y en `docs-map.json`.

Este documento dice de dónde sale exactamente esa afirmación, qué **no** significa y qué haría
falta para que significara lo que parece. Existe por una razón concreta: es la única afirmación del
sitio que puede volverse falsa sin que nada se rompa. Un enlace roto tumba el build; una tabla mal
formada la ve `check_docs.py`; una etiqueta de versión caducada **compila perfectamente**.

## De dónde sale, literalmente

De las URL de la documentación oficial que citaba la guía original. En su lista de Referencias hay
cuatro enlaces a `docs.codabench.org`, y **exactamente uno** lleva la versión en la ruta:

```
https://docs.codabench.org/v1.23/Organizers/Running_a_benchmark/Resource-Management/
```

Los otros tres —*Getting started with Codabench*, *Competition Creation Form* y *Competition
Creation Bundle*— apuntan a `/latest/`, que no identifica ninguna versión concreta.

Se puede comprobar en el original, que sigue en el historial de git:

```bash
git show 495599a:docs/crear-competicion.md | sed -n '229,236p'
```

Y hoy, en la página que heredó esas referencias: `docs/referencia/fuentes.md`.

Ese `v1.23` de una ruta es **todo el fundamento** de la etiqueta. Quien escribió la guía consultó
la documentación de Resource Management publicada bajo la versión 1.23, y de ahí se tomó el número.

## Qué NO significa

- **Nadie ha preguntado a una instancia qué versión ejecuta.** Ni a `codabench.org`, ni a la
  instancia donde se montó la competición que sirvió para contrastar los procedimientos.
- **No se ha comparado con las releases del producto.** La guía se escribió antes de que existiera
  `scripts/check_codabench.py`; es perfectamente posible que 1.23 no sea ni de lejos la última.
- **No cubre las tres cuartas partes de las fuentes.** Tres de los cuatro enlaces son a `/latest/`,
  así que describen lo que hubiera publicado ese día, no lo que publica la 1.23.
- **No dice nada sobre la interfaz observada.** Buena parte de esta guía no sale de la
  documentación, sino de montar una competición real y mirar la pantalla. Esa instancia ejecutaba
  la versión que ejecutara, y no se anotó.

En corto: **v1.23 es una versión de la documentación consultada, no una versión del producto
verificada.** Donde se afirme, hay que decirlo así. La portada, la página de fuentes y el
`README.md` ya lo dicen.

## Por qué se conserva la etiqueta, entonces

Porque la alternativa es peor. Una guía sin versión declarada es una guía que **implícitamente
afirma estar siempre al día**, y esa afirmación no se puede comprobar ni desmentir: no hay nada que
comparar. La etiqueta, aun con el origen limitado que tiene, hace tres cosas:

1. **Convierte una afirmación vaga en una comprobable.** «v1.23» se puede contrastar; «actualizado»
   no.
2. **Da un punto de partida a la comprobación de deriva.** `check_codabench.py` necesita una
   versión declarada para poder decir que se ha quedado atrás.
3. **Deja escrito el límite.** Este documento es parte de la etiqueta: quien la lea en el sitio
   encuentra en `docs/referencia/fuentes.md` de dónde sale, y quien trabaje en el repositorio lo
   encuentra aquí con todo el detalle.

Lo que **no** se hizo es fingir una comprobación que no existe. Esa es la única línea que no se
cruza: es preferible una etiqueta con el origen explicado a una etiqueta que aparenta más rigor del
que tiene.

## Qué haría falta para contrastarla de verdad

Un procedimiento, no un comando. Cuando alguien tenga acceso a una instancia de Codabench:

1. **Leer la versión que declara la instancia** donde se va a contrastar, y anotar cuál es, en qué
   instancia y en qué fecha. Si la instancia es interna, su URL **no se publica**: en `docs/` solo
   entra la versión, no dónde se miró.
2. **Compararla con la última release del producto** (`python scripts/check_codabench.py`, que
   consulta `codalab/codabench` en GitHub). Si la instancia va por detrás de la release, la guía
   describe la instancia, no la release, y hay que decir cuál de las dos rotula la etiqueta.
3. **Recorrer las pantallas que la guía describe** —el editor de competición pestaña a pestaña,
   Resources, Tasks, Phases, Leaderboards— y anotar por página qué se comprobó. Esa es la evidencia
   que la skill `code-documentation` llama «observación directa de la interfaz»: instancia, fecha y
   ruta de navegación.
4. **Declarar esa evidencia en `docs-map.json`**, junto a las URL de documentación que ya declara
   cada sección, para que la próxima vez la revisión sepa qué mirar y qué no.
5. **Anotar el resultado aquí, con fecha**, como nota posterior encima de este documento. Y solo
   entonces, si procede, subir la etiqueta.

Mientras eso no se haga, la etiqueta sigue significando lo que dice esta página, ni más ni menos.

## Qué hace `scripts/check_codabench.py`

Es el aviso automático, y **no** la comprobación. Lo que hace:

```bash
python scripts/check_codabench.py            # informe: ¿hay versión nueva? ¿qué revisar?
python scripts/check_codabench.py --fijar    # cierre mecánico: sube la etiqueta donde aparece
```

- **Consulta** `https://api.github.com/repos/codalab/codabench/releases/latest` y compara la
  versión que devuelve con la que declara este sitio. Ese es el sustituto de lo que en el manual de
  captia.ai es leer el `package.json` del repositorio hermano: aquí el producto es externo y no hay
  repositorio local que mirar.
- **Sale con 0** si está al día, **1** si hay algo que revisar y **2** si no pudo consultar la API
  —sin red falla con un mensaje, no con un traceback—.
- **Señala qué páginas dependen de qué fuentes**, leyéndolo de `docs-map.json`, para que la
  revisión sea acotada en vez de «revísalo todo».
- **Con `--fijar`, reescribe la etiqueta** allí donde el sitio la declara. Busca la frase entera
  `Codabench vX.Y` y no un `vX.Y` suelto, precisamente para **no** tocar las URL de la
  documentación oficial, que llevan la versión en la ruta (`docs.codabench.org/v1.23/…`) y no deben
  reescribirse a ciegas: cambiar ese enlace no lo actualiza, lo rompe o lo manda a una página que
  nadie ha leído.

Lo que **no** hace, a propósito: **no revisa contenido**. Que una versión nueva cambie o no las
pantallas descritas aquí solo se sabe abriendo Codabench y recorriéndolas. Por eso `--fijar` es un
cierre mecánico y va **siempre después** de la revisión, nunca antes. Subir la etiqueta sin haber
revisado no actualiza nada: convierte una afirmación **caducada** en una **falsa**, y esa es una
degradación real, no un tecnicismo. La caducada se detecta comparando versiones —con este mismo
script—; la falsa solo la descubre un lector siguiendo instrucciones que ya no encajan con lo que
tiene en pantalla, y para entonces ya ha perdido la tarde.

### Y el otro modo de podrirse en silencio

`scripts/check_fuentes.py` comprueba que las URL externas de la guía siguen vivas. Detecta que un
enlace a `/v1.23/…` **desaparezca**, pero no puede detectar lo contrario: un enlace a `/latest/…`
que sigue respondiendo 200 mientras describe otra pantalla. Los tres enlaces a `/latest/` de la
página de fuentes están exactamente en ese caso. Para eso está la revisión del apartado anterior;
ninguna herramienta la sustituye.

## Dónde vive la etiqueta

Para que nadie cambie una y se olvide del resto:

| Dónde | Qué hay | Lo sube `--fijar` |
|---|---|---|
| `docusaurus.config.js` | `versions.current.label` y el `copyright` del pie | Sí |
| `docs/**/*.md` y `.mdx` | La afirmación que lee el usuario: el atributo `version` de la portada y el apartado de `referencia/fuentes.md` | Sí, en todas |
| `scripts/build_nav.py` | El literal `revision_contrastada` del que se genera `docs-map.json` | Sí, solo el número |
| `README.md` · `CLAUDE.md` · `.claude/rules/documentacion.md` | La etiqueta citada al explicar el ciclo | Sí |
| `docs-map.json` | `revision_contrastada` ya generado | **No** — es un fichero generado; se rehace con `build_nav.py --apply` |
| `docs-meta/` | Este documento y los otros registros | **No, a propósito** |

`docs-meta/` queda fuera porque son **registros fechados**: reescribirlos para que cuadren con la
versión nueva falsearía lo que cuentan. Este documento es uno de ellos. Si algún día la etiqueta
sube, aquí se añade una nota fechada encima; no se cambia el número y ya está, porque entonces esta
página diría que «v1.30 sale de una URL» y eso no habría pasado nunca.

El script avisa al terminar de las apariciones de la versión antigua que ha dejado sin tocar, y
separa las que son deliberadas de las que hay que mirar. Casi todas las segundas serán URL de la
documentación oficial —las de `docs/referencia/fuentes.md` que llevan `/v1.23/` en la ruta—, y esas
**no se tocan nunca a ciegas**: son la fuente de la que salió la etiqueta, no una copia de ella.
