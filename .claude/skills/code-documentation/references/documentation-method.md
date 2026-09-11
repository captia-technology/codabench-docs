# Método de documentación verificable

## Descubrir antes de narrar

Identificar en el alcance pedido quién es el lector, qué tiene delante, qué
decisiones tiene que tomar, qué depende de qué y dónde se puede equivocar sin
posibilidad de deshacer. Recorrer el procedimiento entero, de principio a fin,
antes de escribirlo: abrir la pantalla, leer los rótulos reales, comprobar qué
campos son obligatorios y qué pasa cuando falta uno. No convertir un índice de
menús en un procedimiento inventado.

Cuando lo documentado es una plataforma externa como Codabench, la disciplina
es la misma que con código, con otras fuentes. Distinguir siempre:

- Lo que **la documentación oficial declara**, con su URL y su versión. Puede ir
  por detrás de lo desplegado.
- Lo que **la interfaz muestra hoy**, con la instancia y la fecha. Puede diferir
  entre instancias y entre versiones.
- Lo que **una competición real hizo**, con lo que se montó y lo que se observó.
  Es la evidencia más fuerte y la más cara de obtener.

Relacionar cada afirmación material con una de las tres. Para un formulario,
distinguir el rótulo que se ve, el campo que se envía y el valor por defecto.
Para un fichero que la plataforma consume —un `metadata`, un `scores.txt`—, no
inferir su formato del nombre: comprobar qué acepta. Para límites, colas o
imágenes de ejecución, no deducir el entorno de producción de lo que muestra
una cabecera.

## Resolver contradicciones

Una fuente demuestra lo que demuestra, y ninguna invalida silenciosamente a las
otras. Registrar por separado:

| Estado | Uso |
| --- | --- |
| Verificado en la documentación oficial | URL y versión leídas, citadas en la página |
| Verificado en la interfaz | Pantalla, instancia y fecha de la observación |
| Verificado montando | Competición real: qué se montó y qué resultado se observó |
| Previsto | Lo que la plataforma anuncia o lo que decide el equipo, sin confirmar |
| Inferido | Hipótesis razonada que no se publicará como hecho |
| No verificado | Falta de acceso, de versión o de evidencia |

Cuando la documentación oficial y la interfaz discrepen, mostrar la
discrepancia y su impacto en la tarea del lector; suele ser lo más útil de la
página. No elegir la fuente más cómoda ni promediarlas. No probar en una
competición ajena, publicada o con participantes reales para salir de dudas.

## Elegir el tipo de página

Aplicar la distinción de Diátaxis: tutorial para aprender mediante un recorrido,
guía para resolver una tarea, referencia para consultar contratos y explicación
para comprender decisiones. No forzar una nueva jerarquía si la existente sirve.
Referencia: `https://diataxis.fr/`.

Cada guía debe declarar audiencia, requisitos, pasos, resultado verificable y
fallos frecuentes. Una referencia debe cubrir campos, valores admitidos,
obligatoriedad y errores observados; no inventar límites, cuotas ni
comportamientos de reintento. Una explicación debe separar lo que la plataforma
hace de lo que la organización ha decidido hacer con ella.

En este repositorio, además, la primera línea del cuerpo de toda página es el
rótulo `**Objetivo:**` con una frase que dice qué consigue el lector. No es
decoración: de ahí sale la `description` del front matter. Los rótulos de la
interfaz de Codabench van en negrita y en su idioma original —**Benchmarks →
Management**, **Add Dataset/Program**, **Force Best**—, porque son lo que el
lector tiene delante en la pantalla; traducirlos le obliga a adivinar.

## Documentación dentro del código

El código de este repositorio es su propia herramienta —los validadores y
generadores de `scripts/`, el hook de `.claude/hooks/` y la configuración de
Docusaurus— más el componente de portada de `src/components/Portada/`, que no es
herramienta sino copia del design system y no se adapta aquí. Respetar sus docstrings y convenciones. Priorizar la invariante que
comprueba cada función, el porqué de una decisión no obvia y el fallo concreto
que la motivó; no repetir tipos ya expresados por el lenguaje ni comentar cada
línea. Mantener firmas, comportamiento y salida intactos: un cambio en un
validador cambia lo que el repositorio acepta como válido, aunque el diff
parezca solo texto.

## Evidencia y publicación

Usar `assets/templates/evidence-ledger.json` como registro auxiliar y guardarlo
en `docs-meta/`, nunca en `docs/`. Preferir URL con versión, o pantalla con
fecha, a una referencia vaga a «la documentación». Los informes privados pueden
contener rutas internas y nombres de instancia; los públicos, no.

El repositorio es privado y el sitio es público. No publicar correos con dominio
real, direcciones IP, credenciales, URLs de instancias internas de Codabench ni
identificadores de cliente. `scripts/check_docs.py` bloquea lo que sabe
reconocer; no todo lo que no puede publicarse tiene una forma reconocible.

## Revisión de lector

Comprobar sin contexto previo: ¿qué resuelve?, ¿quién puede hacerlo?, ¿con qué
requisitos?, ¿cómo confirma que ha salido bien?, ¿qué hace si falla? Con una
guía de una plataforma externa hay una pregunta más: ¿podría seguirla alguien
que tiene Codabench delante y nunca ha montado una competición? La ausencia de
errores de build no demuestra que ninguna de esas preguntas esté resuelta.
