/**
 * Pruebas de la lógica de «Preparar los ficheros» (`src/components/PrepararFicheros/*.mjs`).
 *
 *     node --test scripts/preparar.test.mjs
 *
 * Corren en CI. El build de Docusaurus compila el componente pero no ejecuta nada de lo que hace
 * con un CSV, así que un reparto que mezclara fechas o una nota de referencia mal calculada
 * pasarían en verde. La prueba cruzada del final ejecuta el `score.py` real con Python sobre los
 * ficheros generados: es la que garantiza que la nota que la herramienta anuncia es la que dará
 * Codabench.
 *
 * Datos sintéticos (AULA01, AULA02…, fechas inventadas): el repositorio es público.
 */
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { mkdtempSync, mkdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

import { ErrorDatos, decodificarUtf8, escribirCsv, leerCsv } from '../src/components/PrepararFicheros/csv.mjs';
import {
  analizar,
  detectarFormatoAncho,
  parsearFecha,
  sugerirTipo,
} from '../src/components/PrepararFicheros/analisis.mjs';
import { puntuar, redondear4 } from '../src/components/PrepararFicheros/metricas.mjs';
import { nombreCorto, prepararCompeticion } from '../src/components/PrepararFicheros/generar.mjs';

const REPO = join(dirname(fileURLToPath(import.meta.url)), '..');
const PUNTUACION = join(REPO, 'static', 'plantillas', 'puntuacion');
const PLANTILLAS = {
  scorePy: readFileSync(join(PUNTUACION, 'score.py'), 'utf8'),
  metadata: readFileSync(join(PUNTUACION, 'metadata'), 'utf8'),
};

/** Generador pseudoaleatorio fijo: los datos salen iguales en cada ejecución. */
function aleatorio(semilla) {
  let s = semilla;
  return () => {
    s = (s * 1103515245 + 12345) % 2147483648;
    return s / 2147483648;
  };
}

/**
 * Tres aulas, diez días lectivos de febrero, de 8:00 a 19:00. Ordenado por aula y después por
 * hora, a propósito: el reparto tiene que cortar por fecha aunque el fichero no venga en ese orden.
 */
function csvAulas({ vacias = 0 } = {}) {
  const azar = aleatorio(7);
  const lineas = ['fecha_hora,aula,co2,temperatura,personas,calidad'];
  let vaciasPuestas = 0;
  for (const aula of ['AULA01', 'AULA02', 'AULA03']) {
    for (let dia = 2; dia <= 13; dia++) {
      if (dia === 7 || dia === 8) continue; // fin de semana
      for (let hora = 8; hora <= 19; hora++) {
        const base = hora >= 9 && hora <= 14 ? 22 : 6;
        const personas = Math.max(0, Math.round(base + (aula === 'AULA02' ? 4 : 0) + (azar() - 0.5) * 12));
        const co2 = Math.round(450 + personas * 30 + azar() * 80);
        const calidad = co2 < 800 ? 'buena' : co2 < 1200 ? 'aceptable' : 'deficiente';
        const temperatura = (19 + azar() * 4).toFixed(1);
        const fecha = `2026-02-${String(dia).padStart(2, '0')}T${String(hora).padStart(2, '0')}:00:00+01:00`;
        const sinRespuesta = vaciasPuestas < vacias && hora === 12;
        if (sinRespuesta) vaciasPuestas++;
        lineas.push([fecha, aula, co2, temperatura, sinRespuesta ? '' : personas, calidad].join(','));
      }
    }
  }
  return lineas.join('\n') + '\n';
}

const preparar = (texto, opciones) =>
  prepararCompeticion(leerCsv(texto), { nombre: 'aulas', hoy: '2026-11-11', ...opciones }, PLANTILLAS);

// ------------------------------------------------------------------------------------- CSV

test('leerCsv: comillas, comas y saltos de línea dentro de un valor', () => {
  const { cabecera, filas, lineas } = leerCsv('id,nota\n1,"hola, ""mundo"""\n2,"dos\nlineas"\n3,fin\n');
  assert.deepEqual(cabecera, ['id', 'nota']);
  assert.deepEqual(filas, [
    ['1', 'hola, "mundo"'],
    ['2', 'dos\nlineas'],
    ['3', 'fin'],
  ]);
  assert.deepEqual(lineas, [2, 3, 5]);
});

test('leerCsv: BOM, CRLF, líneas en blanco y comas sobrantes al final', () => {
  const { cabecera, filas } = leerCsv('﻿a,b\r\n1,2,\r\n\r\n3,4\r\n\r\n');
  assert.deepEqual(cabecera, ['a', 'b']);
  assert.deepEqual(filas, [
    ['1', '2'],
    ['3', '4'],
  ]);
});

test('leerCsv: el punto y coma de Excel en español se rechaza con una pista', () => {
  assert.throws(
    () => leerCsv('fecha;personas\n2026-02-10;3\n'),
    (e) => e instanceof ErrorDatos && /punto y coma/.test(e.message) && /CSV UTF-8/.test(e.pista),
  );
});

test('leerCsv: errores de forma', () => {
  assert.throws(() => leerCsv('a,b\n1,"sin cerrar\n'), /comillas sin cerrar desde la línea 2/);
  assert.throws(() => leerCsv('a,a\n1,2\n'), /aparece dos veces/);
  assert.throws(() => leerCsv('a,b\n1,2,3\n'), /línea 2: tiene 3 valores/);
  assert.throws(() => leerCsv('a,b\n'), /solo tiene la cabecera/);
});

test('decodificarUtf8: un fichero en Windows-1252 es un error, no un texto con interrogantes', () => {
  const latin1 = Uint8Array.from([0x61, 0x2c, 0x62, 0x0a, 0x61, 0xf1, 0x6f, 0x2c, 0x31, 0x0a]); // «año»
  assert.throws(() => decodificarUtf8(latin1, 'datos.csv'), /datos\.csv no está en UTF-8/);
  const conBom = new TextEncoder().encode('﻿a,b\n');
  assert.equal(decodificarUtf8(conBom), 'a,b\n');
});

test('escribirCsv: lo que escribe se vuelve a leer igual', () => {
  const filas = [
    ['id', 'texto'],
    ['A_1', 'con, coma'],
    ['A_2', 'con "comillas"'],
  ];
  const texto = escribirCsv(filas);
  assert.equal(texto, 'id,texto\nA_1,"con, coma"\nA_2,"con ""comillas"""\n');
  const leido = leerCsv(texto);
  assert.deepEqual([leido.cabecera, ...leido.filas], filas);
});

// ---------------------------------------------------------------------------------- análisis

test('parsearFecha: ISO con zona, con espacio, solo fecha y día/mes/año', () => {
  const a = parsearFecha('2026-02-10T08:15:00+01:00');
  assert.equal(a.hora, 8);
  assert.equal(a.clave, '202602100815');
  assert.equal(a.fecha, '2026-02-10');
  assert.equal(a.instante, Date.UTC(2026, 1, 10, 7, 15));
  assert.equal(parsearFecha('2026-02-10 08:15').clave, '202602100815');
  assert.equal(parsearFecha('2026-02-10').hora, 0);
  assert.equal(parsearFecha('10/02/2026 8:15').clave, '202602100815');
  assert.equal(parsearFecha('2026-02-31'), null);
  assert.equal(parsearFecha('2026-02-10 25:00'), null);
  assert.equal(parsearFecha('AULA01'), null);
  // El orden lo da el instante, no el texto: 01:30+02:00 es antes que 01:00+00:00.
  assert.ok(parsearFecha('2026-10-25T01:30:00+02:00').instante < parsearFecha('2026-10-25T01:00:00+00:00').instante);
});

test('detectarFormatoAncho: la descarga de varios equipos de captia.ai sí; la de uno, no', () => {
  assert.equal(detectarFormatoAncho(['fecha_hora', 'co2', 'temperatura', 'personas']), null);
  assert.ok(detectarFormatoAncho(['fecha_hora', 'co2__AULA01', 'temp__AULA01', 'co2__AULA02', 'temp__AULA02']));
  const una = detectarFormatoAncho(['fecha_hora', 'co2__AULA01', 'co2__AULA02']);
  assert.deepEqual(una.equipos, ['AULA01', 'AULA02']);
  assert.throws(() => preparar('fecha_hora,co2__AULA01,co2__AULA02\n2026-02-10,1,2\n', { objetivo: 'co2__AULA01', tipo: 'numero' }), /una fila por caso/);
});

test('sugerirTipo: texto, pocos números y muchos números', () => {
  assert.equal(sugerirTipo(['buena', 'aceptable', '']).tipo, 'categoria');
  assert.match(sugerirTipo(['buena', 'aceptable']).motivo, /«buena»/);
  assert.equal(sugerirTipo(['0', '1', '1', '0']).tipo, 'categoria');
  assert.match(sugerirTipo(['0', '1']).motivo, /cámbialo a «Número»/);
  assert.equal(sugerirTipo(['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11']).tipo, 'numero');
  assert.equal(sugerirTipo(['1', '2', '3', '4', '5', '6', '7', '8', '9', '10']).tipo, 'categoria');
});

test('analizar: propone tiempo, grupo e id por nombre y por contenido', () => {
  const { cabecera, filas } = leerCsv(csvAulas());
  const a = analizar(cabecera, filas);
  assert.equal(a.tiempo, 'fecha_hora');
  assert.equal(a.grupo, 'aula');
  assert.equal(a.id, null);
  assert.equal(a.ancho, null);
  assert.equal(a.columnas.find((c) => c.nombre === 'co2').clase, 'numero');
  const otro = leerCsv('ID,cuando,clase\n1,2026-01-01 10:00,x\n2,2026-01-01 11:00,y\n');
  const b = analizar(otro.cabecera, otro.filas);
  assert.equal(b.tiempo, 'cuando');
  assert.equal(b.id, 'ID');
});

// ----------------------------------------------------------------------------------- métricas

test('redondear4 se comporta como round(x, 4) de Python, empates incluidos', () => {
  assert.equal(redondear4(3.14159), 3.1416);
  assert.equal(redondear4(0.03125), 0.0312); // empate: al par
  assert.equal(redondear4(0.09375), 0.0938); // empate: al par
  assert.equal(redondear4(-0.03125), -0.0312);
  assert.equal(redondear4(2 / 3), 0.6667);
});

test('puntuar: los mismos números que las pruebas de score.py', () => {
  const sol = [
    ['a', '10'],
    ['b', '20'],
    ['c', '0'],
  ];
  assert.deepEqual(puntuar(sol, new Map([['a', 12], ['b', 16], ['c', 3]]), 'numero'), { mae: 3, rmse: 3.1091, n: 3 });
  const cat = [['1', 'buena'], ['2', 'buena'], ['3', 'aceptable'], ['4', 'deficiente'], ['5', 'buena'], ['6', 'aceptable']];
  const pred = new Map([['1', 'buena'], ['2', 'aceptable'], ['3', 'aceptable'], ['4', 'buena'], ['5', 'buena'], ['6', 'aceptable']]);
  assert.deepEqual(puntuar(cat, pred, 'categoria'), { aciertos: 0.6667, f1: 0.4889, n: 6 });
});

// --------------------------------------------------------------------------------- generación

const CSV_DE = (texto) => leerCsv(texto);

test('reparto por tiempo: el último 20 %, sin mezclar fechas entre entrenamiento y prueba', () => {
  const { resumen, ficheros } = preparar(csvAulas(), { objetivo: 'personas', tipo: 'numero', tiempo: 'fecha_hora', grupo: 'aula' });
  const train = CSV_DE(ficheros.public_data['train.csv']);
  const test_ = CSV_DE(ficheros.public_data['test.csv']);
  const total = train.filas.length + test_.filas.length;
  assert.equal(total, 3 * 10 * 12);
  assert.equal(test_.filas.length, resumen.filasPrueba);
  assert.ok(Math.abs(test_.filas.length / total - 0.2) < 0.05, `prueba: ${test_.filas.length} de ${total}`);
  const iFecha = train.cabecera.indexOf('fecha_hora');
  const ultimaTrain = train.filas.map((f) => parsearFecha(f[iFecha]).instante).reduce((a, b) => Math.max(a, b));
  const primeraTest = test_.filas.map((f) => parsearFecha(f[test_.cabecera.indexOf('fecha_hora')]).instante).reduce((a, b) => Math.min(a, b));
  assert.ok(ultimaTrain < primeraTest, 'ninguna fila de entrenamiento es posterior a una de prueba');
  assert.equal(resumen.periodoPrueba.hasta, '2026-02-13 19:00');
});

test('ficheros: test.csv sin la respuesta, solución con los mismos id y id generados únicos', () => {
  const { ficheros, resumen } = preparar(csvAulas(), { objetivo: 'personas', tipo: 'numero', tiempo: 'fecha_hora', grupo: 'aula' });
  const train = CSV_DE(ficheros.public_data['train.csv']);
  const test_ = CSV_DE(ficheros.public_data['test.csv']);
  const sol = CSV_DE(ficheros.reference_data['solution.csv']);
  const muestra = CSV_DE(ficheros.public_data['sample_submission.csv']);
  assert.deepEqual(train.cabecera, ['id', 'fecha_hora', 'aula', 'co2', 'temperatura', 'personas', 'calidad']);
  assert.deepEqual(test_.cabecera, ['id', 'fecha_hora', 'aula', 'co2', 'temperatura', 'calidad']);
  assert.deepEqual(sol.cabecera, ['id', 'personas']);
  assert.deepEqual(muestra.cabecera, ['id', 'personas']);
  assert.deepEqual(sol.filas.map((f) => f[0]), test_.filas.map((f) => f[0]));
  assert.deepEqual(muestra.filas.map((f) => f[0]), test_.filas.map((f) => f[0]));
  const ids = [...train.filas, ...test_.filas].map((f) => f[0]);
  assert.equal(new Set(ids).size, ids.length);
  assert.match(ids[0], /^AULA01_2026020208\d\d$/);
  assert.deepEqual(JSON.parse(ficheros.scoring_program['config.json']), { columna: 'personas', tipo: 'numero', id: 'id' });
  assert.equal(ficheros.scoring_program['score.py'], PLANTILLAS.scorePy);
  assert.equal(resumen.zips.public_data, 'public_data_aulas.zip');
  // Los textos no dejan marcadores sin rellenar de la plantilla.
  for (const texto of [...Object.values(ficheros.extras), ficheros.public_data['diccionario_datos.md']]) {
    assert.doesNotMatch(texto, /undefined|null|NaN|\[object/);
  }
  assert.match(ficheros.extras['INSTRUCCIONES.md'], /\| MAE \| `mae` \| `Ascending` \| Sí \| 4 \|/);
});

test('las filas sin respuesta se quitan, con aviso', () => {
  const { resumen } = preparar(csvAulas({ vacias: 4 }), { objetivo: 'personas', tipo: 'numero', tiempo: 'fecha_hora', grupo: 'aula' });
  assert.equal(resumen.filasEntrenamiento + resumen.filasPrueba, 360 - 4);
  assert.ok(resumen.avisos.some((a) => /4 filas sin valor/.test(a)));
});

test('corte por fecha', () => {
  const { resumen } = preparar(csvAulas(), {
    objetivo: 'calidad',
    tipo: 'categoria',
    tiempo: 'fecha_hora',
    grupo: 'aula',
    corte: { modo: 'fecha', fecha: '2026-02-12' },
  });
  assert.equal(resumen.filasPrueba, 3 * 2 * 12);
  assert.equal(resumen.periodoPrueba.desde, '2026-02-12 08:00');
  assert.equal(resumen.periodoEntrenamiento.hasta, '2026-02-11 19:00');
  assert.throws(
    () => preparar(csvAulas(), { objetivo: 'calidad', tipo: 'categoria', tiempo: 'fecha_hora', corte: { modo: 'fecha', fecha: '2027-01-01' } }),
    /la prueba se queda sin filas/,
  );
});

test('sin columna de tiempo: el último 20 % en el orden del fichero, con aviso, e id por número de fila', () => {
  const texto = 'x,y\n' + Array.from({ length: 50 }, (_, i) => `${i},${i % 3 === 0 ? 'si' : 'no'}`).join('\n') + '\n';
  const { resumen, ficheros } = preparar(texto, { objetivo: 'y', tipo: 'categoria' });
  assert.equal(resumen.filasPrueba, 10);
  assert.ok(resumen.avisos.some((a) => /Sin columna de tiempo/.test(a)));
  assert.equal(CSV_DE(ficheros.reference_data['solution.csv']).filas[0][0], '41');
});

test('errores que se explican en vez de generar algo inservible', () => {
  const base = { objetivo: 'calidad', tipo: 'numero', tiempo: 'fecha_hora', grupo: 'aula' };
  assert.throws(() => preparar(csvAulas(), base), /no son números, como «/);
  assert.throws(() => preparar(csvAulas(), { ...base, objetivo: 'aula', tipo: 'categoria' }), /no puede ser también la columna de grupo/);
  assert.throws(() => preparar('id,v\n1,2\n1,3\n2,4\n', { objetivo: 'v', tipo: 'numero' }), /El id «1» está repetido/);
  assert.equal(nombreCorto('Calidad del aire (Aula 1).csv'), 'calidad-del-aire-aula-1');
});

// --------------------------------------------------------------------- prueba cruzada con Python

/** Python del sistema: `python` en Windows y en el runner de CI, `python3` en otros sitios. */
function python(args) {
  for (const ejecutable of [process.env.PYTHON, 'python', 'python3'].filter(Boolean)) {
    const r = spawnSync(ejecutable, args, { encoding: 'utf8' });
    if (!r.error) return r;
  }
  throw new Error('No hay Python en el PATH: la prueba cruzada lo necesita.');
}

/** Puntúa con el score.py real, como Codabench: program/, input/ref, input/res y output/. */
function puntuarConPython(t, ficheros, envio) {
  const raiz = mkdtempSync(join(tmpdir(), 'preparar-'));
  t.after(() => rmSync(raiz, { recursive: true, force: true }));
  const escribir = (carpeta, contenido) => {
    mkdirSync(join(raiz, carpeta), { recursive: true });
    for (const [nombre, texto] of Object.entries(contenido)) writeFileSync(join(raiz, carpeta, nombre), texto);
  };
  escribir('program', ficheros.scoring_program);
  escribir('input/ref', ficheros.reference_data);
  escribir('input/res', { 'submission.csv': envio });
  const r = python([join(raiz, 'program', 'score.py'), join(raiz, 'input'), join(raiz, 'output')]);
  assert.equal(r.status, 0, r.stderr);
  return JSON.parse(readFileSync(join(raiz, 'output', 'scores.json'), 'utf8'));
}

for (const [objetivo, tipo] of [
  ['personas', 'numero'],
  ['calidad', 'categoria'],
]) {
  test(`prueba cruzada (${tipo}): score.py da las mismas notas que anuncia la herramienta`, (t) => {
    const { resumen, ficheros, predicciones } = preparar(csvAulas({ vacias: 3 }), { objetivo, tipo, tiempo: 'fecha_hora', grupo: 'aula' });
    assert.equal(resumen.referencias.length, 2);
    resumen.referencias.forEach((ref, i) => {
      const envio = escribirCsv([['id', objetivo], ...[...predicciones[i]].map(([id, v]) => [id, v])]);
      assert.deepEqual(puntuarConPython(t, ficheros, envio), ref.metricas, ref.nombre);
    });
    // El envío de ejemplo es la referencia del kit: lo que se promete en INSTRUCCIONES.md.
    const kit = resumen.referencias.find((r) => r.kit);
    assert.deepEqual(puntuarConPython(t, ficheros, ficheros.public_data['sample_submission.csv']), kit.metricas);
  });
}
