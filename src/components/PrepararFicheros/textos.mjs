/**
 * Los textos que acompañan a los zip: el diccionario de datos, las instrucciones de montaje y
 * las páginas base de la competición.
 *
 * Se generan con los datos reales de la competición (columnas, fechas, notas de referencia),
 * así que no pueden ser ficheros estáticos. Lo que la herramienta no puede saber —de dónde
 * salen los datos, quién organiza— va entre corchetes con «Completa:», para que se vea al
 * repasar el texto y no se publique por descuido.
 *
 * Los rótulos de Codabench van en inglés y en negrita, como en la guía: son lo que el docente
 * tiene delante en la pantalla.
 */

import { COLUMNAS, formatoDecimal } from './metricas.mjs';

/** Un nombre de columna como código, sin que un `|` rompa la tabla. */
const cod = (texto) => '`' + String(texto).replace(/\|/g, '\\|').replace(/`/g, "'") + '`';

function tabla(cabecera, filas) {
  const linea = (celdas) => '| ' + celdas.join(' | ') + ' |';
  return [linea(cabecera), linea(cabecera.map(() => '---')), ...filas.map(linea)].join('\n');
}

const porcentaje = (x) => {
  const p = Math.round(x * 1000) / 10;
  return `${String(p).replace('.', ',')} %`;
};

const CLASE = { fecha: 'fecha y hora', numero: 'número', texto: 'texto' };

function periodo(p) {
  return p ? `, del ${p.desde} al ${p.hasta}` : '';
}

/** Las notas de referencia como tabla, con las columnas del leaderboard de ese tipo. */
function tablaReferencias(resumen) {
  const columnas = COLUMNAS[resumen.tipo];
  return tabla(
    ['Solución', ...columnas.map((c) => c.titulo)],
    resumen.referencias.map((r) => [r.nombre, ...columnas.map((c) => formatoDecimal(r.metricas[c.clave]))]),
  );
}

function descripcionId(resumen) {
  if (!resumen.idGenerado) return 'Identifica la fila.';
  if (resumen.tiempo && resumen.grupo) return `Identifica la fila: ${resumen.grupo}, fecha y hora (${cod(resumen.ejemploId)}).`;
  if (resumen.tiempo) return `Identifica la fila: fecha y hora (${cod(resumen.ejemploId)}).`;
  return 'Identifica la fila: su número en el fichero original.';
}

/** `diccionario_datos.md`, dentro de los datos públicos. */
export function diccionarioDatos(resumen, columnas) {
  const filas = [];
  if (resumen.idGenerado) filas.push([cod('id'), 'texto', '0 %', descripcionId(resumen)]);
  for (const c of columnas) {
    let descripcion = '[Completa: qué es y en qué unidad.]';
    if (c.nombre === resumen.objetivo) descripcion = '**Lo que hay que predecir.** Solo está en `train.csv`.';
    else if (c.nombre === resumen.id) descripcion = descripcionId(resumen);
    else if (c.nombre === resumen.tiempo) descripcion = 'Fecha y hora de la fila, en hora local. [Completa: qué intervalo cubre cada fila.]';
    else if (c.nombre === resumen.grupo) descripcion = '[Completa: qué es cada grupo.] Cada valor es una serie distinta.';
    filas.push([cod(c.nombre), CLASE[c.clase], porcentaje(c.vacios), descripcion]);
  }
  return `# Diccionario de datos

[Completa: qué es cada fila y de dónde salen los datos.]

## Ficheros

${tabla(
    ['Fichero', 'Qué lleva'],
    [
      [cod('train.csv'), `${resumen.filasEntrenamiento} filas${periodo(resumen.periodoEntrenamiento)}, **con** la columna ${cod(resumen.objetivo)}. Sirve para aprender.`],
      [cod('test.csv'), `${resumen.filasPrueba} filas${periodo(resumen.periodoPrueba)}, **sin** la columna ${cod(resumen.objetivo)}. Es lo que hay que predecir.`],
      [cod('sample_submission.csv'), `Un envío de ejemplo, con una fila por cada ${cod(resumen.id)} de ${cod('test.csv')}.`],
    ],
  )}

## Columnas

${tabla(['Columna', 'Tipo', 'Vacíos', 'Descripción'], filas)}
`;
}

/** La métrica principal en una frase, para el participante. */
function explicacionMetrica(resumen) {
  if (resumen.tipo === 'numero') {
    return (
      `**Error absoluto medio (MAE)**: la diferencia media entre lo que predices y el valor real, en las ` +
      `unidades de ${cod(resumen.objetivo)}. **Cuanto más bajo, mejor.** La tabla de resultados muestra ` +
      'también el **RMSE**, que castiga más los errores grandes.'
    );
  }
  return (
    '**F1 macro**: calcula el F1 de cada clase y hace la media, de modo que todas las clases pesan igual. ' +
    '**Cuanto más alto, mejor**, y el máximo es 1. La tabla de resultados muestra también la proporción ' +
    'de **aciertos**, de 0 a 1: si una clase domina, acertar siempre esa da muchos aciertos y un F1 macro bajo.'
  );
}

function ejemploEnvio(resumen) {
  const ejemplo = resumen.tipo === 'numero' ? '12.5' : resumen.ejemploClase ?? 'clase';
  return '```\n' + `${resumen.id},${resumen.objetivo}\n${resumen.ejemploId},${ejemplo}\n...\n` + '```';
}

/** `INSTRUCCIONES.md`: qué se sube, dónde y cómo se configura el leaderboard. */
export function instrucciones(resumen) {
  const z = resumen.zips;
  const columnas = COLUMNAS[resumen.tipo];
  const principal = columnas.find((c) => c.principal);
  const delKit = resumen.referencias.find((r) => r.kit);
  const tipoTexto = resumen.tipo === 'numero' ? 'número (regresión)' : 'categoría (clasificación)';
  return `# Cómo montar la competición en Codabench

Ficheros generados el ${resumen.fecha} con la herramienta «Preparar los ficheros» de la guía de
Codabench. Se han generado en tu navegador: los datos no han salido de tu ordenador.

- **Columna a predecir:** ${cod(resumen.objetivo)}, ${tipoTexto}.
- **Entrenamiento:** ${resumen.filasEntrenamiento} filas${periodo(resumen.periodoEntrenamiento)}.
- **Prueba:** ${resumen.filasPrueba} filas${periodo(resumen.periodoPrueba)}.

## 1. Subir los cuatro zip

En **Resources → Datasets and programs**, pulsa **Add Dataset/Program** una vez por cada zip y
elige su tipo:

${tabla(
    ['Zip', 'Tipo', 'Público', 'Dónde se usa después'],
    [
      [cod(z.public_data), cod('public_data'), 'Sí', 'En la fase, campo **Public Data**'],
      [cod(z.starting_kit), cod('starting_kit'), 'Sí', 'En la fase, campo **Starting Kit**'],
      [cod(z.reference_data), cod('reference_data'), '**No**', 'En la Task, campo **Reference data**'],
      [cod(z.scoring_program), cod('scoring_program'), '**No**', 'En la Task, campo **Scoring program**'],
    ],
  )}

${cod(z.reference_data)} lleva las respuestas de la prueba: si se marca como público, cualquiera
puede descargarlas.

## 2. Crear la Task

En **Resources → Tasks**, pulsa **Create Task** y elige ${cod(z.reference_data)} en
**Reference data** y ${cod(z.scoring_program)} en **Scoring program**. Deja vacíos
**Input data** e **Ingestion program**: el participante sube directamente sus predicciones.

El programa de puntuación solo usa la biblioteca estándar de Python, así que funciona con la
imagen por defecto de **Details → Competition Docker Image**.

## 3. La fase

En la pestaña **Phases** del editor, al crear o editar la fase: la Task del paso anterior en
**Tasks**, ${cod(z.public_data)} en **Public Data** y ${cod(z.starting_kit)} en **Starting Kit**.

## 4. El leaderboard

En la pestaña **Leaderboard**, una columna por métrica:

${tabla(
    ['Title', 'Column Key', 'Sorting', 'Primary Column', 'Column Precision'],
    columnas.map((c) => [c.titulo, cod(c.clave), cod(c.orden), c.principal ? 'Sí' : 'No', '4']),
  )}

La **Column Key** tiene que ser exactamente la de la tabla: es la clave que escribe el programa
de puntuación en \`scores.json\`. ${principal.orden === 'Ascending' ? '`Ascending` quiere decir que menor es mejor' : '`Descending` quiere decir que mayor es mejor'}.
El programa escribe también \`n\`, el número de filas evaluadas; no necesita columna.

## 5. Las páginas

${tabla(
    ['Fichero', 'Dónde va'],
    [
      [cod('paginas/1_presentacion.md'), 'Pestaña **Pages**, página «Presentación»'],
      [cod('paginas/2_datos.md'), 'Pestaña **Pages**, página «Datos»'],
      [cod('paginas/3_evaluacion.md'), 'Pestaña **Pages**, página «Evaluación»'],
      [cod('paginas/4_condiciones.md'), 'Pestaña **Participation**, campo **Terms**'],
    ],
  )}

Son un punto de partida: completa lo que va entre corchetes antes de publicar.

## 6. Probar antes de abrir

Comprime ${cod('sample_submission.csv')} en un zip, con el CSV en la raíz, y súbelo en
**My Submissions**. La columna ${principal.titulo} tiene que dar
**${formatoDecimal(delKit.metricas[principal.clave])}** (Codabench lo enseña con punto decimal).
Si falla o da otra cosa, revisa la Task y las **Column Key** del leaderboard.

## Notas de referencia

${
    resumen.referencias.length > 1
      ? 'Lo que sacan dos soluciones sencillas sobre la prueba. Un modelo que no las mejore no aporta\nnada frente a una regla que cabe en una línea.'
      : 'Lo que saca la solución más sencilla sobre la prueba. Un modelo que no la mejore no aporta\nnada frente a una regla que cabe en una línea.'
  }

${tablaReferencias(resumen)}
`;
}

/** Las cuatro páginas base de la competición. */
export function paginas(resumen, columnas) {
  const presentacion = `# [Completa: título de la competición]

[Completa: de dónde salen los datos y por qué merece la pena predecir esto.]

**El reto:** predecir ${cod(resumen.objetivo)} en cada fila de ${cod('test.csv')} a partir del resto de columnas.

## Cómo participar

1. Lee las páginas **Datos** y **Evaluación**.
2. Descarga los datos y el kit de inicio en la pestaña **Get Started**.
3. Entrena tu modelo y escribe \`submission.csv\`, con una predicción para cada fila de \`test.csv\`.
4. Comprímelo en un \`.zip\`, con el CSV en la raíz, y súbelo en **My Submissions**.
5. Mira tu posición en **Results**.

El kit de inicio trae una solución de referencia que no necesita instalar nada.
`;

  const datos = `# Datos

[Completa: qué es cada fila, por ejemplo «un aula en una hora».]

${tabla(
    ['Fichero', 'Qué lleva'],
    [
      [cod('train.csv'), `${resumen.filasEntrenamiento} filas${periodo(resumen.periodoEntrenamiento)}, **con** ${cod(resumen.objetivo)}.`],
      [cod('test.csv'), `${resumen.filasPrueba} filas${periodo(resumen.periodoPrueba)}, **sin** ${cod(resumen.objetivo)}: es lo que hay que predecir.`],
      [cod('sample_submission.csv'), 'Un envío de ejemplo con el formato correcto.'],
      [cod('diccionario_datos.md'), 'Qué es cada columna.'],
    ],
  )}

Columnas: ${[...(resumen.idGenerado ? ['id'] : []), ...columnas.map((c) => c.nombre)].map(cod).join(', ')}.

${
  resumen.tiempo
    ? 'El reparto es por fechas: la prueba empieza donde acaba el entrenamiento. Así la competición mide ' +
      'si se sabe predecir lo que viene, no si se recuerda lo que ya pasó.'
    : 'El reparto sigue el orden del fichero: la prueba son las últimas filas.'
}
`;

  const evaluacion = `# Evaluación

## Métrica

${explicacionMetrica(resumen)}

## Formato del envío

Un \`.zip\` con un único CSV **en la raíz** (no dentro de una carpeta), con dos columnas:

${ejemploEnvio(resumen)}

- Una fila por cada ${cod(resumen.id)} de \`test.csv\`, ni más ni menos.
- ${resumen.tipo === 'numero' ? 'Los decimales, con punto.' : `Las clases, escritas exactamente igual que en \`train.csv\`.`}
- Separado por comas y guardado en UTF-8.

## Referencias

${tablaReferencias(resumen)}
`;

  const condiciones = `# Condiciones

- Competición con fines educativos, organizada por [Completa: centro u organización].
- Los datos proceden de [Completa: de dónde]. [Completa: si contienen o no datos personales.]
- Los datos solo se pueden usar dentro de esta competición.
- Cada participante envía sus propias predicciones. No vale usar fuentes externas con los valores reales.
- La organización puede revisar los envíos y retirar los que no cumplan estas condiciones.
`;

  return {
    '1_presentacion.md': presentacion,
    '2_datos.md': datos,
    '3_evaluacion.md': evaluacion,
    '4_condiciones.md': condiciones,
  };
}
