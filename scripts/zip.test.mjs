/**
 * Pruebas del zip propio de «Preparar los ficheros» (`src/components/PrepararFicheros/zip.mjs`).
 *
 *     node --test scripts/zip.test.mjs
 *
 * Corren en CI. Un zip mal escrito no lo detecta nadie en el navegador: se descarga y se sube a
 * Codabench, que lo rechaza con un error genérico. Por eso, además de leer lo que se escribe, se
 * comprueba con el `zipfile` de Python —el mismo módulo que usan los scripts del kit de inicio—
 * que el zip es válido para otro programa, y al revés: que se leen los zips que hace Python.
 */
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

import { crc32, crearZip, leerZip, puedeComprimir } from '../src/components/PrepararFicheros/zip.mjs';

const texto = (bytes) => new TextDecoder().decode(bytes);
const CSV = 'id,personas\n' + Array.from({ length: 200 }, (_, i) => `AULA01_2026021008${String(i % 60).padStart(2, '0')},${i % 17}`).join('\n') + '\n';

function python(args) {
  for (const ejecutable of [process.env.PYTHON, 'python', 'python3'].filter(Boolean)) {
    const r = spawnSync(ejecutable, args, { encoding: 'utf8' });
    if (!r.error) return r;
  }
  throw new Error('No hay Python en el PATH: la comprobación cruzada lo necesita.');
}

function temporal(t) {
  const dir = mkdtempSync(join(tmpdir(), 'zip-'));
  t.after(() => rmSync(dir, { recursive: true, force: true }));
  return dir;
}

test('crc32: el valor de control del estándar', () => {
  assert.equal(crc32(new TextEncoder().encode('123456789')), 0xcbf43926);
  assert.equal(crc32(new Uint8Array(0)), 0);
});

test('crear y leer: comprimido con deflate, y lo pequeño sin comprimir', async () => {
  assert.ok(puedeComprimir(), 'Node 22 tiene CompressionStream con deflate-raw');
  const zip = await crearZip([
    { nombre: 'train.csv', datos: CSV },
    { nombre: 'metadata', datos: 'command: python3 $program/score.py $input $output\n' },
    { nombre: 'vacio.txt', datos: '' },
  ]);
  const leido = await leerZip(zip);
  assert.deepEqual(leido.map((e) => e.nombre), ['train.csv', 'metadata', 'vacio.txt']);
  assert.equal(texto(leido[0].datos), CSV);
  assert.equal(leido[0].metodo, 8);
  assert.equal(leido[1].metodo, 0, 'una línea comprimida crece: se guarda tal cual');
  assert.equal(texto(leido[2].datos), '');
});

test('sin CompressionStream, el zip se escribe sin comprimir y sigue siendo válido', async (t) => {
  const original = globalThis.CompressionStream;
  globalThis.CompressionStream = undefined;
  t.after(() => {
    globalThis.CompressionStream = original;
  });
  assert.equal(puedeComprimir(), false);
  const leido = await leerZip(await crearZip([{ nombre: 'train.csv', datos: CSV }]));
  assert.equal(leido[0].metodo, 0);
  assert.equal(texto(leido[0].datos), CSV);
});

test('un zip dentro de otro, como en «Descargar todo»', async () => {
  const dentro = await crearZip([{ nombre: 'solution.csv', datos: CSV }]);
  const fuera = await crearZip([
    { nombre: 'reference_data_aulas.zip', datos: dentro },
    { nombre: 'paginas/1_presentacion.md', datos: '# Título\n' },
  ]);
  const [zipInterior, pagina] = await leerZip(fuera);
  assert.equal(pagina.nombre, 'paginas/1_presentacion.md');
  const [solucion] = await leerZip(zipInterior.datos);
  assert.equal(texto(solucion.datos), CSV);
});

test('errores: no es un zip, o está dañado', async () => {
  await assert.rejects(leerZip(new TextEncoder().encode('id,personas\n1,2\n'), 'datos.zip'), /datos\.zip no es un zip/);
  const zip = await crearZip([{ nombre: 'a.txt', datos: 'x'.repeat(10) }], { comprimir: false });
  zip[30 + 'a.txt'.length] ^= 0xff; // un byte del contenido
  await assert.rejects(leerZip(zip), /no pasa la comprobación de integridad/);
});

test('Python (zipfile) abre lo que escribe la herramienta, nombres en UTF-8 incluidos', async (t) => {
  const dir = temporal(t);
  const ruta = join(dir, 'prueba.zip');
  writeFileSync(
    ruta,
    await crearZip([
      { nombre: 'train.csv', datos: CSV },
      { nombre: 'diccionario_año.md', datos: '# Diccionario\n' },
      { nombre: 'paginas/2_datos.md', datos: '# Datos\n' },
    ]),
  );
  const r = python([
    '-c',
    'import json, sys, zipfile\n' +
      'z = zipfile.ZipFile(sys.argv[1])\n' +
      'assert z.testzip() is None\n' +
      'print(json.dumps({i.filename: [i.compress_type, z.read(i).decode("utf-8")] for i in z.infolist()}))',
    ruta,
  ]);
  assert.equal(r.status, 0, r.stderr);
  const contenido = JSON.parse(r.stdout);
  assert.deepEqual(Object.keys(contenido), ['train.csv', 'diccionario_año.md', 'paginas/2_datos.md']);
  assert.deepEqual(contenido['train.csv'], [8, CSV]);
  assert.equal(contenido['diccionario_año.md'][1], '# Diccionario\n');
});

test('la herramienta lee lo que escribe Python (zipfile, deflate)', async (t) => {
  const dir = temporal(t);
  const ruta = join(dir, 'de-python.zip');
  const r = python([
    '-c',
    'import sys, zipfile\n' +
      'with zipfile.ZipFile(sys.argv[1], "w", zipfile.ZIP_DEFLATED) as z:\n' +
      '    z.writestr("submission.csv", "id,personas\\n" + "A,1\\n" * 300)\n' +
      '    z.writestr("carpeta/", "")\n',
    ruta,
  ]);
  assert.equal(r.status, 0, r.stderr);
  const leido = await leerZip(readFileSync(ruta));
  assert.equal(leido[0].nombre, 'submission.csv');
  assert.equal(leido[0].metodo, 8);
  assert.equal(texto(leido[0].datos), 'id,personas\n' + 'A,1\n'.repeat(300));
  assert.equal(leido[1].carpeta, true);
});
