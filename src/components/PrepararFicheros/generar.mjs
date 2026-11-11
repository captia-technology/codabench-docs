/**
 * De un CSV en formato largo a los ficheros de una competición de Codabench.
 *
 * Reparte por tiempo, nunca al azar (decisión P7 de docs-meta/07): con un reparto al azar, la
 * misma hora de la misma aula acaba a la vez en entrenamiento y en prueba, y el leaderboard
 * premia memorizar en vez de predecir. Genera los `id` si no los hay, calcula las notas de
 * referencia con las mismas cuentas que score.py y escribe el contenido de cada fichero.
 *
 * Es una función pura: recibe el CSV ya leído y el texto de las plantillas (score.py,
 * metadata…), y devuelve el contenido de los ficheros. Empaquetarlos en zip y descargarlos es
 * cosa de la interfaz.
 */

import { ErrorDatos, escribirCsv } from './csv.mjs';
import { detectarFormatoAncho, errorFormatoAncho, esNumero, normalizarNombre, parsearFecha } from './analisis.mjs';
import { puntuar, redondear4 } from './metricas.mjs';
import { crearZip } from './zip.mjs';
import { agrupacion, diccionarioDatos, instrucciones, paginas, readmeKit } from './textos.mjs';

/** Los scripts del kit de inicio, tal como están en `static/plantillas/kit/`. */
export const FICHEROS_KIT = ['solucion_referencia.py', 'validar_envio.py', 'hacer_envio_zip.py'];

/** Qué parte de las filas va a la prueba cuando el corte no es por fecha. */
export const PARTE_PRUEBA = 0.2;

/** Una plantilla que tiene que estar: un kit con un script vacío sería peor que un error. */
function plantilla(grupo, nombre) {
  const texto = grupo && grupo[nombre];
  if (!texto) throw new Error(`Falta la plantilla ${nombre}.`);
  return texto;
}

/** Nombre corto para los zip: minúsculas ASCII y guiones. */
export function nombreCorto(texto) {
  const limpio = String(texto || '')
    .replace(/\.csv$/i, '')
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 40)
    .replace(/-+$/, '');
  return limpio || 'competicion';
}

/** Los nombres de los cuatro zip, en el orden en que se suben. */
export function nombresZip(nombre) {
  const corto = nombreCorto(nombre);
  return {
    public_data: `public_data_${corto}.zip`,
    starting_kit: `starting_kit_${corto}.zip`,
    reference_data: `reference_data_${corto}.zip`,
    scoring_program: `scoring_program_${corto}.zip`,
    todo: `competicion_${corto}.zip`,
  };
}

/** La clase más frecuente; en un empate, la primera en orden alfabético, para que sea reproducible. */
function masFrecuente(cuentas) {
  let mejor = null;
  let maximo = -1;
  for (const [clase, n] of cuentas) {
    if (n > maximo || (n === maximo && clase < mejor)) {
      mejor = clase;
      maximo = n;
    }
  }
  return mejor;
}

/**
 * Las dos soluciones de referencia: la más simple (la media o la clase más frecuente de todo el
 * entrenamiento) y la que agrupa por lo que haya —grupo, hora del día o los dos—.
 *
 * La segunda es la misma que `solucion_referencia.py` del kit de inicio, cuenta por cuenta: se
 * recorre train.csv en su orden, se suma en ese orden y se redondea igual. Por eso las notas que
 * se anuncian en el kit se reproducen al ejecutarla.
 */
function referencias(entrenamiento, prueba, opciones) {
  const { tipo, grupo, tiempo } = opciones;
  const clave = (f) => [grupo ? f.grupo : null, tiempo ? f.hora : null].join('\u0000');

  let global;
  const porClave = new Map();
  if (tipo === 'numero') {
    let suma = 0;
    for (const f of entrenamiento) {
      const v = Number(f.objetivo);
      suma += v;
      const k = clave(f);
      const acumulado = porClave.get(k) || { suma: 0, n: 0 };
      acumulado.suma += v;
      acumulado.n += 1;
      porClave.set(k, acumulado);
    }
    global = redondear4(suma / entrenamiento.length);
  } else {
    const cuentas = new Map();
    for (const f of entrenamiento) {
      cuentas.set(f.objetivo, (cuentas.get(f.objetivo) || 0) + 1);
      const k = clave(f);
      if (!porClave.has(k)) porClave.set(k, new Map());
      const c = porClave.get(k);
      c.set(f.objetivo, (c.get(f.objetivo) || 0) + 1);
    }
    global = masFrecuente(cuentas);
  }
  const deClave = (k) => {
    const v = porClave.get(k);
    if (v === undefined) return global;
    return tipo === 'numero' ? redondear4(v.suma / v.n) : masFrecuente(v);
  };

  const solucion = prueba.map((f) => [f.id, f.objetivo]);
  const lista = [];
  const simple = new Map(prueba.map((f) => [f.id, global]));
  lista.push({
    nombre: tipo === 'numero' ? 'Predecir siempre la media' : 'Predecir siempre la clase más frecuente',
    predicciones: simple,
    metricas: puntuar(solucion, simple, tipo),
  });
  if (grupo || tiempo) {
    const que = tipo === 'numero' ? 'Media' : 'Clase más frecuente';
    const donde = agrupacion(grupo, tiempo);
    const agrupada = new Map(prueba.map((f) => [f.id, deClave(clave(f))]));
    lista.push({
      nombre: `${que} ${donde}`,
      predicciones: agrupada,
      metricas: puntuar(solucion, agrupada, tipo),
      kit: true,
    });
  } else {
    lista[0].kit = true;
  }
  return lista;
}

/** Valida las opciones contra el CSV y devuelve los índices de cada columna. */
function columnasElegidas(cabecera, opciones) {
  const indice = (nombre, que) => {
    if (!nombre) return -1;
    const i = cabecera.indexOf(nombre);
    if (i === -1) throw new ErrorDatos(`La columna ${que} «${nombre}» no está en el fichero.`);
    return i;
  };
  const iObjetivo = indice(opciones.objetivo, 'a predecir');
  if (iObjetivo === -1) throw new ErrorDatos('Falta elegir la columna a predecir.');
  const iTiempo = indice(opciones.tiempo, 'de tiempo');
  const iGrupo = indice(opciones.grupo, 'de grupo');
  const iId = cabecera.findIndex((c) => normalizarNombre(c) === 'id');
  for (const [i, que] of [
    [iTiempo, 'de tiempo'],
    [iGrupo, 'de grupo'],
    [iId, 'id'],
  ]) {
    if (i === iObjetivo) {
      throw new ErrorDatos(`La columna a predecir no puede ser también la columna ${que}.`);
    }
  }
  if (iTiempo !== -1 && iTiempo === iGrupo) {
    throw new ErrorDatos('La columna de tiempo y la de grupo tienen que ser distintas.');
  }
  if (opciones.tipo !== 'numero' && opciones.tipo !== 'categoria') {
    throw new ErrorDatos('El tipo tiene que ser «numero» o «categoria».');
  }
  return { iObjetivo, iTiempo, iGrupo, iId };
}

/** `id` de cada fila: el que trae el fichero o uno generado, siempre únicos. */
function ponerIds(filas, iId, tieneTiempo, tieneGrupo, avisos) {
  if (iId !== -1) {
    const vistos = new Set();
    for (const f of filas) {
      const id = f.valores[iId];
      if (id === '') throw new ErrorDatos(`La columna id está vacía en la línea ${f.linea}.`, 'Rellénala o quítala del CSV: la herramienta generará los id.');
      if (vistos.has(id)) throw new ErrorDatos(`El id «${id}» está repetido (línea ${f.linea}).`, 'Corrígelo o quita la columna id del CSV: la herramienta generará unos únicos.');
      vistos.add(id);
      f.id = id;
    }
    return;
  }
  const usados = new Map();
  let repetidos = 0;
  for (const f of filas) {
    let base;
    if (tieneTiempo) base = tieneGrupo ? `${f.grupo || 'sin-grupo'}_${f.clave}` : f.clave;
    else base = String(f.numero);
    const n = (usados.get(base) || 0) + 1;
    usados.set(base, n);
    if (n > 1) repetidos++;
    f.id = n > 1 ? `${base}_${n}` : base;
  }
  if (repetidos) {
    avisos.push(
      `${repetidos} filas coincidían con otra en ${tieneGrupo ? 'grupo y ' : ''}minuto; su id lleva un número ` +
        'al final (_2, _3…) para que no se repita. Si no lo esperabas, revisa si hay filas duplicadas.',
    );
  }
}

/** Reparte en entrenamiento y prueba. Devuelve `[entrenamiento, prueba]` en el orden del fichero. */
function repartir(filas, corte, tieneTiempo, avisos) {
  let enPrueba;
  if (!tieneTiempo) {
    const k = Math.floor(filas.length * (1 - PARTE_PRUEBA));
    enPrueba = (f, i) => i >= k;
    avisos.push(
      'Sin columna de tiempo, la prueba es el último 20 % de las filas en el orden del fichero. Si no ' +
        'está ordenado por fecha, la nota de la competición no será realista.',
    );
  } else if (corte && corte.modo === 'fecha') {
    if (!/^\d{4}-\d{2}-\d{2}$/.test(corte.fecha || '')) throw new ErrorDatos('Falta la fecha de corte.');
    enPrueba = (f) => f.fecha >= corte.fecha;
  } else {
    const ordenadas = filas.map((f, i) => [f.instante, i]).sort((a, b) => a[0] - b[0] || a[1] - b[1]);
    const limite = ordenadas[Math.floor(filas.length * (1 - PARTE_PRUEBA))][0];
    // Todo lo que ocurre en el instante del corte o después va a la prueba: así una misma
    // franja no queda partida entre las dos, aunque haya varios grupos en ella.
    enPrueba = (f) => f.instante >= limite;
  }
  const entrenamiento = [];
  const prueba = [];
  filas.forEach((f, i) => (enPrueba(f, i) ? prueba : entrenamiento).push(f));
  if (entrenamiento.length === 0 || prueba.length === 0) {
    const vacia = entrenamiento.length === 0 ? 'el entrenamiento' : 'la prueba';
    const rango = tieneTiempo ? ` Los datos van del ${rangoFechas(filas).desde} al ${rangoFechas(filas).hasta}.` : '';
    throw new ErrorDatos(`Con ese corte, ${vacia} se queda sin filas.${rango}`, 'Elige otra fecha de corte o el último 20 %.');
  }
  if (prueba.length < 30) {
    avisos.push(
      `La prueba tiene solo ${prueba.length} filas: la nota cambiará mucho de un envío a otro por azar.`,
    );
  }
  return [entrenamiento, prueba];
}

function rangoFechas(filas) {
  let desde = null;
  let hasta = null;
  for (const f of filas) {
    if (desde === null || f.local < desde) desde = f.local;
    if (hasta === null || f.local > hasta) hasta = f.local;
  }
  return { desde, hasta };
}

/**
 * Prepara la competición.
 *
 * - `datos`: lo que devuelve `leerCsv`.
 * - `opciones`: `{ objetivo, tipo: 'numero'|'categoria', tiempo, grupo, corte, nombre }`, con
 *   `corte` igual a `{ modo: 'porcentaje' }` o `{ modo: 'fecha', fecha: 'AAAA-MM-DD' }`.
 * - `plantillas`: el texto de `score.py`, `metadata` y los ficheros del kit, tal como se sirven
 *   desde `static/plantillas/`.
 *
 * Devuelve el resumen para la interfaz y `ficheros`: un objeto con el contenido de cada zip.
 */
export function prepararCompeticion(datos, opciones, plantillas) {
  const { cabecera } = datos;
  const ancho = detectarFormatoAncho(cabecera);
  if (ancho) throw errorFormatoAncho(ancho);
  const { iObjetivo, iTiempo, iGrupo, iId } = columnasElegidas(cabecera, opciones);
  const tieneTiempo = iTiempo !== -1;
  const tieneGrupo = iGrupo !== -1;
  const objetivo = cabecera[iObjetivo];
  const avisos = [];

  let filas = datos.filas.map((valores, i) => ({
    valores,
    numero: i + 1,
    linea: datos.lineas ? datos.lineas[i] : i + 2,
    objetivo: valores[iObjetivo],
    grupo: tieneGrupo ? valores[iGrupo] : null,
  }));

  const sinRespuesta = filas.filter((f) => f.objetivo === '').length;
  filas = filas.filter((f) => f.objetivo !== '');
  if (sinRespuesta) {
    avisos.push(`Se han quitado ${sinRespuesta} filas sin valor en «${objetivo}»: no hay nada con lo que puntuarlas.`);
  }

  if (tieneTiempo) {
    let sinFecha = 0;
    filas = filas.filter((f) => {
      const p = parsearFecha(f.valores[iTiempo]);
      if (!p) {
        sinFecha++;
        return false;
      }
      Object.assign(f, p);
      return true;
    });
    if (sinFecha) {
      avisos.push(`Se han quitado ${sinFecha} filas cuya fecha no se puede leer en «${cabecera[iTiempo]}».`);
    }
  }
  if (filas.length < 2) throw new ErrorDatos('Quedan menos de dos filas con respuesta: no hay con qué montar una competición.');

  if (opciones.tipo === 'numero') {
    const mala = filas.find((f) => !esNumero(f.objetivo));
    if (mala) {
      throw new ErrorDatos(
        `La columna «${objetivo}» tiene valores que no son números, como «${mala.objetivo}» (línea ${mala.linea}).`,
        'Elige «Categoría», o corrige esos valores. Los decimales van con punto.',
      );
    }
  }

  ponerIds(filas, iId, tieneTiempo, tieneGrupo, avisos);
  const [entrenamiento, prueba] = repartir(filas, opciones.corte, tieneTiempo, avisos);

  if (opciones.tipo === 'categoria') {
    const vistas = new Set(entrenamiento.map((f) => f.objetivo));
    const nuevas = [...new Set(prueba.map((f) => f.objetivo))].filter((c) => !vistas.has(c));
    if (nuevas.length) {
      avisos.push(
        `En la prueba hay clases que no aparecen en el entrenamiento (${nuevas.slice(0, 3).join(', ')}): ` +
          'nadie podrá aprender a predecirlas.',
      );
    }
  }

  const idCol = iId !== -1 ? cabecera[iId] : 'id';
  const conId = iId === -1;
  const columnasTrain = conId ? ['id', ...cabecera] : [...cabecera];
  const filaTrain = (f) => (conId ? [f.id, ...f.valores] : [...f.valores]);
  const quitar = conId ? iObjetivo + 1 : iObjetivo;
  const sinObjetivo = (fila) => fila.filter((_, i) => i !== quitar);

  const config = { columna: objetivo, tipo: opciones.tipo, id: idCol };
  const refs = referencias(entrenamiento, prueba, {
    tipo: opciones.tipo,
    grupo: tieneGrupo ? cabecera[iGrupo] : null,
    tiempo: tieneTiempo ? cabecera[iTiempo] : null,
  });
  const delKit = refs.find((r) => r.kit);
  const zips = nombresZip(opciones.nombre);

  const resumen = {
    objetivo,
    tipo: opciones.tipo,
    id: idCol,
    idGenerado: conId,
    tiempo: tieneTiempo ? cabecera[iTiempo] : null,
    grupo: tieneGrupo ? cabecera[iGrupo] : null,
    filasEntrenamiento: entrenamiento.length,
    filasPrueba: prueba.length,
    periodoEntrenamiento: tieneTiempo ? rangoFechas(entrenamiento) : null,
    periodoPrueba: tieneTiempo ? rangoFechas(prueba) : null,
    referencias: refs.map(({ nombre, metricas, kit }) => ({ nombre, metricas, kit: Boolean(kit) })),
    // Para los ejemplos de formato: un id real de la prueba y, como valor, la predicción de la
    // referencia más simple, no la respuesta de esa fila.
    ejemploId: prueba[0].id,
    ejemploClase: String(refs[0].predicciones.get(prueba[0].id)),
    avisos,
    zips,
    config,
    fecha: opciones.hoy || new Date().toISOString().slice(0, 10),
  };

  const columnas = cabecera.map((nombre, i) => ({
    nombre,
    vacios: filas.filter((f) => f.valores[i] === '').length / filas.length,
    clase:
      i === iTiempo
        ? 'fecha'
        : filas.every((f) => f.valores[i] === '' || esNumero(f.valores[i]))
          ? 'numero'
          : 'texto',
  }));

  const ficheros = {
    public_data: {
      'train.csv': escribirCsv([columnasTrain, ...entrenamiento.map(filaTrain)]),
      'test.csv': escribirCsv([sinObjetivo(columnasTrain), ...prueba.map((f) => sinObjetivo(filaTrain(f)))]),
      'sample_submission.csv': escribirCsv([[idCol, objetivo], ...prueba.map((f) => [f.id, delKit.predicciones.get(f.id)])]),
      'diccionario_datos.md': diccionarioDatos(resumen, columnas),
    },
    reference_data: {
      'solution.csv': escribirCsv([[idCol, objetivo], ...prueba.map((f) => [f.id, f.objetivo])]),
    },
    scoring_program: {
      metadata: plantilla(plantillas, 'metadata'),
      'score.py': plantilla(plantillas, 'scorePy'),
      'config.json': JSON.stringify(config, null, 2) + '\n',
    },
    // Los scripts del kit son genéricos: lo propio de esta competición va en su config.json,
    // que lleva además el grupo y el tiempo con los que agrupa la solución de referencia.
    starting_kit: {
      'README.md': readmeKit(resumen),
      'config.json': JSON.stringify({ ...config, grupo: resumen.grupo, tiempo: resumen.tiempo }, null, 2) + '\n',
      ...Object.fromEntries(FICHEROS_KIT.map((nombre) => [nombre, plantilla(plantillas.kit, nombre)])),
    },
    extras: {
      'INSTRUCCIONES.md': instrucciones(resumen),
      ...Object.fromEntries(Object.entries(paginas(resumen, columnas)).map(([n, t]) => [`paginas/${n}`, t])),
    },
  };

  return { resumen, ficheros, predicciones: refs.map((r) => r.predicciones) };
}

/** El orden en que se suben los zip, que es también el de los botones de descarga. */
export const ORDEN_ZIPS = ['public_data', 'starting_kit', 'reference_data', 'scoring_program'];

/**
 * Los cuatro zip, con todo en la raíz, y el de «Descargar todo»: los cuatro zip más las
 * instrucciones y las páginas base. Devuelve los bytes de cada uno, por papel y `todo`.
 */
export async function empaquetar(ficheros, zips, opciones = {}) {
  const salida = {};
  for (const papel of ORDEN_ZIPS) {
    salida[papel] = await crearZip(
      Object.entries(ficheros[papel]).map(([nombre, datos]) => ({ nombre, datos })),
      opciones,
    );
  }
  salida.todo = await crearZip(
    [
      ...ORDEN_ZIPS.map((papel) => ({ nombre: zips[papel], datos: salida[papel] })),
      ...Object.entries(ficheros.extras).map(([nombre, datos]) => ({ nombre, datos })),
    ],
    opciones,
  );
  return salida;
}
