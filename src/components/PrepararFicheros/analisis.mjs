/**
 * Mirar un CSV antes de tocarlo: qué columnas hay, cuál parece el tiempo, cuál el grupo,
 * si es el formato ancho que no se admite y qué tipo de competición sale de la columna que
 * se quiere predecir.
 *
 * Todo lo que se deduce aquí es una PROPUESTA: la interfaz la enseña con su motivo y el
 * docente puede cambiarla. La herramienta no tiene por qué acertar siempre; tiene que explicar
 * siempre por qué propone lo que propone.
 */

import { ErrorDatos } from './csv.mjs';

/**
 * Lo que cuenta como número. Es el mismo patrón que usa `score.py`: si aquí se aceptara algo
 * que allí no (o al revés), la referencia que calcula la herramienta y la nota de Codabench
 * dejarían de coincidir.
 */
export const RE_NUMERO = /^[+-]?(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?$/;

export function esNumero(texto) {
  return RE_NUMERO.test(texto);
}

// Fechas: ISO 8601 (lo que descarga captia.ai, «2026-02-10T08:15:00+01:00») y el día/mes/año
// en que Excel en español reescribe esas fechas si se abre y se guarda el fichero. Los dos
// patrones están copiados en la solución de referencia del kit de inicio, que tiene que sacar
// la misma hora de la misma fecha.
const RE_ISO =
  /^(\d{4})-(\d{2})-(\d{2})(?:[T ](\d{2}):(\d{2})(?::(\d{2})(?:[.,]\d+)?)?)?\s*(Z|[+-]\d{2}:?\d{2})?$/;
const RE_DMA = /^(\d{1,2})\/(\d{1,2})\/(\d{4})(?:[ T](\d{1,2}):(\d{2})(?::(\d{2}))?)?$/;

const dos = (n) => String(n).padStart(2, '0');

/**
 * Una fecha en texto a sus partes, o `null` si no es una fecha.
 *
 * La hora, la clave del id y la fecha del corte son las que se leen escritas —la hora local
 * del centro—, no las convertidas a UTC: «las 8» tiene que ser las 8 para el docente que eligió
 * el corte y para el participante que agrupa por hora. El instante en UTC (`instante`) solo se
 * usa para ordenar, que es donde un cambio de hora sí importaría.
 */
export function parsearFecha(texto) {
  const t = String(texto).trim();
  let anio;
  let mes;
  let dia;
  let hora = 0;
  let minuto = 0;
  let segundo = 0;
  let zona = null;
  let m = RE_ISO.exec(t);
  if (m) {
    [anio, mes, dia] = [Number(m[1]), Number(m[2]), Number(m[3])];
    if (m[4] !== undefined) [hora, minuto] = [Number(m[4]), Number(m[5])];
    if (m[6] !== undefined) segundo = Number(m[6]);
    zona = m[7] ?? null;
  } else if ((m = RE_DMA.exec(t))) {
    [dia, mes, anio] = [Number(m[1]), Number(m[2]), Number(m[3])];
    if (m[4] !== undefined) [hora, minuto] = [Number(m[4]), Number(m[5])];
    if (m[6] !== undefined) segundo = Number(m[6]);
  } else {
    return null;
  }
  if (mes < 1 || mes > 12 || dia < 1 || hora > 23 || minuto > 59 || segundo > 59) return null;
  // El 31 de febrero no existe: Date lo convertiría en el 3 de marzo sin avisar.
  const base = new Date(Date.UTC(anio, mes - 1, dia));
  if (base.getUTCMonth() !== mes - 1) return null;
  let desfase = 0;
  if (zona && zona !== 'Z') {
    const signo = zona[0] === '-' ? -1 : 1;
    const cifras = zona.slice(1).replace(':', '');
    desfase = signo * (Number(cifras.slice(0, 2)) * 60 + Number(cifras.slice(2, 4)));
  }
  const fecha = `${anio}-${dos(mes)}-${dos(dia)}`;
  return {
    instante: Date.UTC(anio, mes - 1, dia, hora, minuto, segundo) - desfase * 60000,
    fecha,
    hora,
    local: `${fecha} ${dos(hora)}:${dos(minuto)}`,
    clave: `${anio}${dos(mes)}${dos(dia)}${dos(hora)}${dos(minuto)}`,
  };
}

/** Nombres que delatan una columna de tiempo, en minúscula y sin tildes. */
const NOMBRES_TIEMPO = ['fecha_hora', 'fecha', 'timestamp', 'time', 'date', 'datetime', 'fecha_y_hora', 'instante'];

/** Nombres que delatan una columna de grupo: lo que separa una serie de otra. */
const NOMBRES_GRUPO = [
  'equipo',
  'aula',
  'grupo',
  'asset',
  'asset_id',
  'device',
  'device_id',
  'dispositivo',
  'maquina',
  'sensor',
  'sala',
  'zona',
  'estacion',
  'site',
  'site_id',
];

/** Minúscula y sin tildes, para comparar nombres de columna. */
export function normalizarNombre(nombre) {
  return nombre
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .toLowerCase()
    .trim();
}

/**
 * ¿Es el formato ancho de captia.ai, con una columna por variable Y equipo (`co2__AULA01`)?
 *
 * Así sale hoy la descarga de varios equipos a la vez. La herramienta no lo convierte (decisión
 * P5 de docs-meta/07): lo detecta y explica qué hacer. Se considera ancho si un mismo sufijo
 * `__X` se repite en varias columnas (varias variables del mismo equipo) o si una misma variable
 * aparece con varios sufijos (la misma variable en varios equipos).
 */
export function detectarFormatoAncho(cabecera) {
  const partidas = cabecera
    .map((nombre) => {
      const i = nombre.lastIndexOf('__');
      return i > 0 && i < nombre.length - 2
        ? { nombre, base: nombre.slice(0, i), sufijo: nombre.slice(i + 2) }
        : null;
    })
    .filter(Boolean);
  if (partidas.length < 2) return null;
  const porSufijo = new Map();
  const sufijosPorBase = new Map();
  for (const p of partidas) {
    porSufijo.set(p.sufijo, (porSufijo.get(p.sufijo) || 0) + 1);
    if (!sufijosPorBase.has(p.base)) sufijosPorBase.set(p.base, new Set());
    sufijosPorBase.get(p.base).add(p.sufijo);
  }
  const ancho =
    [...porSufijo.values()].some((n) => n >= 2) || [...sufijosPorBase.values()].some((s) => s.size >= 2);
  if (!ancho) return null;
  return {
    equipos: [...new Set(partidas.map((p) => p.sufijo))],
    columnas: partidas.map((p) => p.nombre),
  };
}

/** El error que se enseña ante el formato ancho. Se construye aquí para que la prueba vea el mismo texto. */
export function errorFormatoAncho(ancho) {
  const ejemplo = ancho.columnas.slice(0, 3).join(', ');
  return new ErrorDatos(
    `Este fichero tiene los datos de ${ancho.equipos.length} equipos en la misma fila, una columna ` +
      `por variable y equipo (${ejemplo}…). La herramienta necesita una fila por caso.`,
    'Descarga de captia.ai un solo equipo cada vez y prepara una competición con cada uno, o espera ' +
      'a la descarga de varios equipos en una sola tabla, que llegará más adelante.',
  );
}

/**
 * Qué tipo de competición sale de los valores de la columna a predecir, y por qué.
 *
 * Números con más de 10 valores distintos son una cantidad que se estima (regresión); texto, o
 * números con 10 valores o menos (0/1, de 1 a 5…), son clases que se aciertan (clasificación).
 * El umbral es una convención, no una ley: por eso el motivo se enseña y el tipo se puede cambiar.
 */
export function sugerirTipo(valores) {
  const llenos = valores.map((v) => String(v).trim()).filter((v) => v !== '');
  if (llenos.length === 0) {
    return { tipo: 'categoria', motivo: 'La columna está vacía: no hay nada que predecir.' };
  }
  const textual = llenos.find((v) => !esNumero(v));
  if (textual !== undefined) {
    return {
      tipo: 'categoria',
      motivo:
        `Hay valores que no son números, como «${textual}»: es una clase que se acierta o no ` +
        '(clasificación). Se puntúa con el F1 macro y la proporción de aciertos: cuanto más alto, mejor.',
    };
  }
  const distintos = new Set(llenos.map(Number)).size;
  if (distintos > 10) {
    return {
      tipo: 'numero',
      motivo:
        `Todos los valores son números y hay ${distintos} distintos, más de 10: es una cantidad que se ` +
        'estima (regresión). Se puntúa con el error absoluto medio (MAE): cuanto más bajo, mejor.',
    };
  }
  return {
    tipo: 'categoria',
    motivo:
      `Son números, pero solo hay ${distintos} valores distintos, 10 o menos: se tratan como clases ` +
      '(clasificación), como 0 y 1. Si en realidad es una cantidad, cámbialo a «Número».',
  };
}

/**
 * Resumen de cada columna y propuesta de columnas de tiempo, grupo e id.
 *
 * Una columna es de fechas si al menos el 95 % de sus valores lo son: las pocas que no se puedan
 * leer se quitan al generar, con aviso, en vez de rechazar el fichero entero.
 */
export function analizar(cabecera, filas) {
  const columnas = cabecera.map((nombre, i) => {
    const llenos = [];
    for (const fila of filas) if (fila[i] !== '') llenos.push(fila[i]);
    const numerica = llenos.length > 0 && llenos.every(esNumero);
    const fechas = llenos.filter((v) => parsearFecha(v) !== null).length;
    const esFecha = llenos.length > 0 && !numerica && fechas >= 0.95 * llenos.length;
    let clase = 'texto';
    if (llenos.length === 0) clase = 'vacia';
    else if (esFecha) clase = 'fecha';
    else if (numerica) clase = 'numero';
    return {
      nombre,
      clase,
      vacios: filas.length - llenos.length,
      distintos: new Set(llenos).size,
      ejemplo: llenos[0] ?? '',
    };
  });

  const fechas = columnas.filter((c) => c.clase === 'fecha');
  const tiempo =
    fechas.find((c) => NOMBRES_TIEMPO.includes(normalizarNombre(c.nombre))) ?? fechas[0] ?? null;
  const grupo =
    columnas.find((c) => c !== tiempo && NOMBRES_GRUPO.includes(normalizarNombre(c.nombre))) ?? null;
  const id = columnas.find((c) => normalizarNombre(c.nombre) === 'id') ?? null;

  return {
    columnas,
    filas: filas.length,
    tiempo: tiempo ? tiempo.nombre : null,
    grupo: grupo ? grupo.nombre : null,
    id: id ? id.nombre : null,
    ancho: detectarFormatoAncho(cabecera),
  };
}
