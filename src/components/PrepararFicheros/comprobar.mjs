/**
 * «Comprobar mis ficheros»: revisa cuatro zip hechos a mano antes de subirlos a Codabench.
 *
 * Mira los fallos que en Codabench solo se ven como un envío que falla, a veces con un mensaje
 * que no dice nada (decisión P12 de docs-meta/07): ficheros dentro de una carpeta, `metadata`
 * sin `command`, `config.json` roto, `test.csv` con la respuesta dentro, ids que no casan entre
 * la solución y la prueba, punto y coma y texto que no es UTF-8.
 *
 * Cada resultado dice qué pasa y, si es un fallo, cómo arreglarlo. Un zip que no se sube se
 * marca como «sin comprobar», no como correcto.
 */

import { ErrorDatos, decodificarUtf8, leerCsv } from './csv.mjs';
import { leerZip } from './zip.mjs';

export const PAPELES = [
  { clave: 'public_data', titulo: 'Datos públicos', tipo: 'public_data' },
  { clave: 'starting_kit', titulo: 'Kit de inicio', tipo: 'starting_kit' },
  { clave: 'reference_data', titulo: 'Datos de referencia', tipo: 'reference_data' },
  { clave: 'scoring_program', titulo: 'Programa de puntuación', tipo: 'scoring_program' },
];

/** Lo que el sistema operativo mete en un zip sin que nadie lo pida. */
const esBasura = (nombre) => nombre.startsWith('__MACOSX/') || /(^|\/)(\.DS_Store|Thumbs\.db|desktop\.ini)$/i.test(nombre);
const EXT_TEXTO = /\.(csv|md|txt|py|json|r|ya?ml)$/i;

/** Marca del programa genérico de la guía: si está, el zip necesita su config.json. */
const MARCA_GENERICO = 'Programa de puntuación genérico';

function nuevoInforme() {
  const lista = [];
  const poner = (zip, estado, mensaje, arreglo = '') => lista.push({ zip, estado, mensaje, arreglo });
  return {
    lista,
    ok: (zip, m) => poner(zip, 'ok', m),
    error: (zip, m, a) => poner(zip, 'error', m, a),
    aviso: (zip, m, a) => poner(zip, 'aviso', m, a),
    sinComprobar: (zip, m) => poner(zip, 'sin-comprobar', m),
  };
}

/** Lee el CSV de un zip, avisando del separador y de la codificación. `null` si no se puede. */
function csvDe(entrada, zip, informe) {
  let texto;
  try {
    texto = decodificarUtf8(entrada.datos, entrada.nombre);
    return leerCsv(texto, entrada.nombre);
  } catch (e) {
    if (!(e instanceof ErrorDatos)) throw e;
    informe.error(zip, e.message, e.pista);
    return null;
  }
}

/** Ids de un CSV en la columna indicada, con los repetidos y los vacíos aparte. */
function idsDe(csv, columna) {
  const i = csv.cabecera.indexOf(columna);
  const ids = new Set();
  const repetidos = [];
  let vacios = 0;
  for (const fila of csv.filas) {
    const id = fila[i];
    if (id === '') vacios++;
    else if (ids.has(id)) repetidos.push(id);
    else ids.add(id);
  }
  return { ids, repetidos, vacios };
}

const ejemplos = (lista) => lista.slice(0, 3).map((x) => `«${x}»`).join(', ');

/**
 * Abre un zip y comprueba lo que vale para todos: que se lea, que los ficheros estén en la raíz
 * y que el texto esté en UTF-8. Devuelve un mapa nombre → entrada, o `null` si no se pudo abrir.
 */
async function abrir(papel, archivo, informe) {
  const zip = papel.clave;
  let entradas;
  try {
    entradas = await leerZip(archivo.bytes, archivo.nombre);
  } catch (e) {
    if (!(e instanceof ErrorDatos)) throw e;
    informe.error(zip, e.message, e.pista || 'Vuelve a crear el zip con la opción de comprimir de tu sistema.');
    return null;
  }
  const ficheros = entradas.filter((e) => !e.carpeta && !esBasura(e.nombre));
  if (ficheros.length === 0) {
    informe.error(zip, `${archivo.nombre} está vacío.`);
    return null;
  }
  const enCarpeta = ficheros.filter((e) => e.nombre.includes('/'));
  if (enCarpeta.length === ficheros.length) {
    const carpeta = ficheros[0].nombre.split('/')[0];
    informe.error(
      zip,
      `Todos los ficheros están dentro de la carpeta «${carpeta}/», no en la raíz del zip. Codabench no los encontrará.`,
      'Comprime los ficheros, no la carpeta: entra en ella, selecciónalos todos y comprímelos.',
    );
  } else if (enCarpeta.length) {
    informe.aviso(
      zip,
      `Hay ficheros dentro de carpetas: ${ejemplos(enCarpeta.map((e) => e.nombre))}.`,
      'Si alguno es de los que Codabench tiene que encontrar, sácalo a la raíz del zip.',
    );
  } else {
    informe.ok(zip, `${ficheros.length} ficheros, todos en la raíz del zip.`);
  }
  // Los CSV se comprueban después, al leerlos, junto con el separador.
  for (const e of ficheros) {
    if ((EXT_TEXTO.test(e.nombre) && !/\.csv$/i.test(e.nombre)) || e.nombre.split('/').pop() === 'metadata') {
      try {
        decodificarUtf8(e.datos, e.nombre);
      } catch (err) {
        informe.error(zip, err.message, err.pista);
      }
    }
  }
  // En la raíz, por su nombre; lo que esté en carpetas no cuenta para las comprobaciones de abajo.
  return new Map(ficheros.filter((e) => !e.nombre.includes('/')).map((e) => [e.nombre, e]));
}

/** `metadata` con `command` y, si es el programa genérico, un `config.json` válido. */
function comprobarPrograma(ficheros, informe) {
  const zip = 'scoring_program';
  const metadata = ficheros.get('metadata');
  if (!metadata) {
    const parecido = [...ficheros.keys()].find((n) => /^metadata\./i.test(n));
    informe.error(
      zip,
      'Falta el fichero `metadata` en la raíz del zip.',
      parecido
        ? `Hay un «${parecido}»: tiene que llamarse metadata, sin extensión.`
        : 'Crea un fichero llamado metadata, sin extensión, con una línea como: command: python3 $program/score.py $input $output',
    );
  } else {
    const texto = new TextDecoder().decode(metadata.datos);
    const m = /^\s*command\s*:\s*(.+)$/m.exec(texto);
    if (!m) {
      informe.error(zip, '`metadata` no tiene la línea `command:`.', 'Añade, por ejemplo: command: python3 $program/score.py $input $output');
    } else {
      const llamado = /\$program\/(\S+)/.exec(m[1]);
      if (llamado && !ficheros.has(llamado[1])) {
        informe.error(zip, `\`metadata\` ejecuta «${llamado[1]}», pero ese fichero no está en la raíz del zip.`, 'Corrige el nombre en metadata o añade el fichero.');
      } else {
        informe.ok(zip, `\`metadata\` ejecuta: ${m[1].trim()}`);
      }
    }
  }

  const score = ficheros.get('score.py');
  const generico = score && new TextDecoder().decode(score.datos).includes(MARCA_GENERICO);
  const crudo = ficheros.get('config.json');
  if (!crudo) {
    if (generico) {
      informe.error(zip, 'Es el programa de puntuación genérico de la guía, pero falta `config.json`.', 'Añade config.json en la raíz, con la columna a comparar y el tipo.');
    }
    return null;
  }
  let config;
  try {
    config = JSON.parse(new TextDecoder().decode(crudo.datos).replace(/^﻿/, ''));
  } catch (e) {
    informe.error(zip, `\`config.json\` no es un JSON válido: ${e.message}`, 'Revisa las comillas y las comas. Debe parecerse a {"columna": "personas", "tipo": "numero"}.');
    return null;
  }
  const problemas = [];
  if (!config || typeof config !== 'object' || Array.isArray(config)) problemas.push('no es un objeto');
  else {
    if (typeof config.columna !== 'string' || !config.columna.trim()) problemas.push('falta "columna"');
    if (config.tipo !== 'numero' && config.tipo !== 'categoria') problemas.push('"tipo" tiene que ser "numero" o "categoria"');
    if (config.id !== undefined && (typeof config.id !== 'string' || !config.id.trim())) problemas.push('"id" tiene que ser el nombre de una columna');
  }
  if (problemas.length) {
    informe.error(zip, `\`config.json\`: ${problemas.join('; ')}.`, 'Debe parecerse a {"columna": "personas", "tipo": "numero"}.');
    return null;
  }
  informe.ok(zip, `\`config.json\`: compara la columna «${config.columna}» como ${config.tipo === 'numero' ? 'número' : 'categoría'}.`);
  return { columna: config.columna.trim(), tipo: config.tipo, id: (config.id || 'id').trim() };
}

/**
 * Comprueba los zip. `archivos` es un objeto con una entrada por papel (`public_data`,
 * `starting_kit`, `reference_data`, `scoring_program`), cada una `{ nombre, bytes }` o ausente.
 * Devuelve la lista de resultados: `{ zip, estado, mensaje, arreglo }`.
 */
export async function comprobarZips(archivos) {
  const informe = nuevoInforme();
  const abiertos = {};
  for (const papel of PAPELES) {
    const archivo = archivos[papel.clave];
    if (!archivo) {
      informe.sinComprobar(papel.clave, 'No has elegido este zip.');
      continue;
    }
    abiertos[papel.clave] = await abrir(papel, archivo, informe);
  }

  // Los CSV de todos los zip: separador y codificación, una sola vez.
  const csv = {};
  for (const [zip, ficheros] of Object.entries(abiertos)) {
    if (!ficheros) continue;
    for (const [nombre, entrada] of ficheros) {
      if (/\.csv$/i.test(nombre)) csv[`${zip}/${nombre}`] = csvDe(entrada, zip, informe);
    }
  }

  const config = abiertos.scoring_program ? comprobarPrograma(abiertos.scoring_program, informe) : null;
  const idCol = config ? config.id : 'id';

  let train = null;
  let test = null;
  if (abiertos.public_data) {
    const pub = abiertos.public_data;
    for (const nombre of ['train.csv', 'test.csv']) {
      if (!pub.has(nombre)) {
        const parecido = [...pub.keys()].find((n) => n.toLowerCase() === nombre);
        informe.error(
          'public_data',
          `Falta \`${nombre}\` en la raíz del zip.`,
          parecido ? `Hay un «${parecido}»: renómbralo a ${nombre}, en minúsculas.` : `Añade ${nombre} en la raíz.`,
        );
      }
    }
    train = csv['public_data/train.csv'] ?? null;
    test = csv['public_data/test.csv'] ?? null;
    if (pub.has('solution.csv')) {
      informe.error('public_data', 'Los datos públicos llevan `solution.csv`: las respuestas de la prueba quedarían a la vista de todos.', 'Quítalo de este zip: va solo en los datos de referencia.');
    }
  }

  // La columna a predecir: la de config.json o, sin él, la que está en train y no en test.
  let objetivo = config ? config.columna : null;
  if (train && test) {
    if (objetivo) {
      if (test.cabecera.includes(objetivo)) {
        informe.error('public_data', `\`test.csv\` lleva la columna «${objetivo}», que es la respuesta.`, 'Quita esa columna de test.csv: es lo que tienen que predecir.');
      } else {
        informe.ok('public_data', `\`test.csv\` no lleva la columna «${objetivo}».`);
      }
      if (!train.cabecera.includes(objetivo)) {
        informe.error('public_data', `\`train.csv\` no tiene la columna «${objetivo}» que dice config.json.`, 'Sin ella no hay con qué aprender: revisa el nombre en config.json o en train.csv.');
      }
    } else {
      const soloTrain = train.cabecera.filter((c) => !test.cabecera.includes(c));
      if (soloTrain.length === 0) {
        informe.error('public_data', '`test.csv` tiene todas las columnas de `train.csv`: ¿falta quitar la columna a predecir?', 'Quita de test.csv la columna con la respuesta.');
      } else {
        objetivo = soloTrain.length === 1 ? soloTrain[0] : null;
        informe.ok('public_data', `\`test.csv\` no lleva ${soloTrain.length === 1 ? 'la columna' : 'las columnas'} ${ejemplos(soloTrain)} de \`train.csv\`.`);
      }
    }
    for (const [nombre, datos] of [['train.csv', train], ['test.csv', test]]) {
      if (!datos.cabecera.includes(idCol)) {
        informe.error('public_data', `\`${nombre}\` no tiene la columna «${idCol}».`, 'Cada fila necesita un id: es lo que empareja la predicción con la respuesta.');
      }
    }
  }

  if (abiertos.reference_data) {
    const ref = abiertos.reference_data;
    const csvs = [...ref.keys()].filter((n) => /\.csv$/i.test(n));
    const nombre = csvs.find((n) => n.toLowerCase().includes('solution')) ?? csvs[0];
    const solucion = nombre ? csv[`reference_data/${nombre}`] : null;
    if (!nombre) {
      informe.error('reference_data', 'No hay ningún CSV en la raíz de los datos de referencia.', 'Añade solution.csv, con el id y la respuesta de cada fila de test.csv.');
    } else if (solucion) {
      const faltan = [idCol, objetivo].filter((c) => c && !solucion.cabecera.includes(c));
      if (faltan.length) {
        informe.error('reference_data', `\`${nombre}\` no tiene ${faltan.length === 1 ? 'la columna' : 'las columnas'} ${ejemplos(faltan)}.`, 'Tiene que llevar el id y la respuesta, con los mismos nombres que usa el programa de puntuación.');
      } else if (test && test.cabecera.includes(idCol)) {
        const s = idsDe(solucion, idCol);
        const t = idsDe(test, idCol);
        const faltanIds = [...t.ids].filter((id) => !s.ids.has(id));
        const sobranIds = [...s.ids].filter((id) => !t.ids.has(id));
        if (s.repetidos.length || t.repetidos.length) {
          informe.error('reference_data', `Hay ids repetidos: ${ejemplos([...s.repetidos, ...t.repetidos])}.`, 'Cada id tiene que aparecer una sola vez en test.csv y en la solución.');
        }
        if (s.vacios || t.vacios) {
          informe.error('reference_data', 'Hay filas sin id en la solución o en test.csv.', 'Rellena el id de esas filas.');
        }
        if (faltanIds.length || sobranIds.length) {
          informe.error(
            'reference_data',
            `Los ids de \`${nombre}\` y de \`test.csv\` no coinciden: a la solución le faltan ${faltanIds.length} y le sobran ${sobranIds.length}${faltanIds.length ? ` (faltan, por ejemplo, ${ejemplos(faltanIds)})` : ''}.`,
            'Genera los dos ficheros a la vez, del mismo reparto: la solución es test.csv con su respuesta.',
          );
        } else if (!s.repetidos.length && !t.repetidos.length) {
          informe.ok('reference_data', `Los ${s.ids.size} ids de \`${nombre}\` son los mismos que los de \`test.csv\`.`);
        }
      }
    }
  }

  if (abiertos.starting_kit && abiertos.starting_kit.size === 0) {
    informe.aviso('starting_kit', 'El kit de inicio no tiene ningún fichero en la raíz.', 'El participante lo descarga tal cual: pon en la raíz lo que necesita para empezar.');
  }

  return informe.lista;
}
