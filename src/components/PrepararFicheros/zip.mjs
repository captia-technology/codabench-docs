/**
 * Crear y leer ficheros zip en el navegador, sin dependencias (decisión P3 de docs-meta/07).
 *
 * El formato que hace falta es pequeño: cabecera local, datos, directorio central y registro
 * final, con un CRC32 por fichero. Comprimir y descomprimir lo hacen `CompressionStream` y
 * `DecompressionStream` con `deflate-raw`, que es exactamente el método 8 del zip. Si el
 * navegador no los tiene, el zip se escribe sin comprimir (método 0): ocupa más, pero Codabench
 * y cualquier descompresor lo abren igual.
 *
 * Sin zip64 y sin cifrado: una competición de aula no se acerca a los 4 GiB, y un zip cifrado
 * no lo puede abrir Codabench.
 */

import { ErrorDatos } from './csv.mjs';

const TABLA_CRC = (() => {
  const tabla = new Uint32Array(256);
  for (let n = 0; n < 256; n++) {
    let c = n;
    for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
    tabla[n] = c >>> 0;
  }
  return tabla;
})();

/** CRC-32 (IEEE 802.3), el que lleva cada fichero de un zip. */
export function crc32(bytes) {
  let c = 0xffffffff;
  for (let i = 0; i < bytes.length; i++) c = TABLA_CRC[(c ^ bytes[i]) & 0xff] ^ (c >>> 8);
  return (c ^ 0xffffffff) >>> 0;
}

const aBytes = (datos) => (typeof datos === 'string' ? new TextEncoder().encode(datos) : datos);

/** Pasa unos bytes por un flujo de transformación (compresión o descompresión). */
async function transformar(bytes, flujo) {
  const salida = new Blob([bytes]).stream().pipeThrough(flujo);
  return new Uint8Array(await new Response(salida).arrayBuffer());
}

/** ¿Puede este navegador comprimir con deflate? Si no, el zip va sin comprimir. */
export function puedeComprimir() {
  try {
    new CompressionStream('deflate-raw');
    return true;
  } catch {
    return false;
  }
}

/** Fecha y hora en el formato de MS-DOS, que es el que guarda un zip. */
function fechaDos(d) {
  return {
    hora: (d.getHours() << 11) | (d.getMinutes() << 5) | Math.floor(d.getSeconds() / 2),
    fecha: ((Math.max(d.getFullYear(), 1980) - 1980) << 9) | ((d.getMonth() + 1) << 5) | d.getDate(),
  };
}

/**
 * Crea un zip. `entradas` es una lista de `{ nombre, datos }`, con `datos` en texto (se guarda
 * en UTF-8) o en bytes. Todo va donde diga `nombre`: para que los ficheros queden en la raíz del
 * zip —lo que pide Codabench— basta con no poner carpeta en el nombre.
 */
export async function crearZip(entradas, { comprimir = true, fecha = new Date() } = {}) {
  const deflate = comprimir && puedeComprimir();
  const { hora, fecha: dia } = fechaDos(fecha);
  const partes = [];
  const central = [];
  let desplazamiento = 0;

  for (const { nombre, datos } of entradas) {
    const crudo = aBytes(datos);
    const nombreBytes = new TextEncoder().encode(nombre);
    let metodo = 0;
    let guardado = crudo;
    if (deflate) {
      const comprimido = await transformar(crudo, new CompressionStream('deflate-raw'));
      // Un fichero pequeño o ya comprimido (otro zip) puede crecer al comprimirlo.
      if (comprimido.length < crudo.length) {
        metodo = 8;
        guardado = comprimido;
      }
    }
    const crc = crc32(crudo);

    const local = new DataView(new ArrayBuffer(30));
    local.setUint32(0, 0x04034b50, true);
    local.setUint16(4, 20, true); // versión necesaria: 2.0
    local.setUint16(6, 0x0800, true); // bit 11: el nombre va en UTF-8
    local.setUint16(8, metodo, true);
    local.setUint16(10, hora, true);
    local.setUint16(12, dia, true);
    local.setUint32(14, crc, true);
    local.setUint32(18, guardado.length, true);
    local.setUint32(22, crudo.length, true);
    local.setUint16(26, nombreBytes.length, true);
    local.setUint16(28, 0, true);
    partes.push(new Uint8Array(local.buffer), nombreBytes, guardado);

    const cd = new DataView(new ArrayBuffer(46));
    cd.setUint32(0, 0x02014b50, true);
    cd.setUint16(4, 20, true); // hecho por: MS-DOS, 2.0
    cd.setUint16(6, 20, true);
    cd.setUint16(8, 0x0800, true);
    cd.setUint16(10, metodo, true);
    cd.setUint16(12, hora, true);
    cd.setUint16(14, dia, true);
    cd.setUint32(16, crc, true);
    cd.setUint32(20, guardado.length, true);
    cd.setUint32(24, crudo.length, true);
    cd.setUint16(28, nombreBytes.length, true);
    cd.setUint32(42, desplazamiento, true);
    central.push(new Uint8Array(cd.buffer), nombreBytes);

    desplazamiento += 30 + nombreBytes.length + guardado.length;
  }

  const tamCentral = central.reduce((n, p) => n + p.length, 0);
  const fin = new DataView(new ArrayBuffer(22));
  fin.setUint32(0, 0x06054b50, true);
  fin.setUint16(8, entradas.length, true);
  fin.setUint16(10, entradas.length, true);
  fin.setUint32(12, tamCentral, true);
  fin.setUint32(16, desplazamiento, true);

  const todo = [...partes, ...central, new Uint8Array(fin.buffer)];
  const salida = new Uint8Array(todo.reduce((n, p) => n + p.length, 0));
  let i = 0;
  for (const p of todo) {
    salida.set(p, i);
    i += p.length;
  }
  return salida;
}

/**
 * Lee un zip. Devuelve la lista de `{ nombre, datos, carpeta, metodo }`, con `datos` en bytes.
 *
 * Lee el directorio central, que es la lista fiable (las cabeceras locales pueden llevar los
 * tamaños a cero si el zip se escribió en flujo), y comprueba el CRC de cada fichero: un zip
 * dañado que se lee a medias daría un informe engañoso.
 */
export async function leerZip(bytes, nombreZip = 'El zip') {
  const datos = bytes instanceof Uint8Array ? bytes : new Uint8Array(bytes);
  const vista = new DataView(datos.buffer, datos.byteOffset, datos.byteLength);
  let fin = -1;
  for (let i = datos.length - 22; i >= Math.max(0, datos.length - 22 - 65535); i--) {
    if (vista.getUint32(i, true) === 0x06054b50) {
      fin = i;
      break;
    }
  }
  if (fin === -1) throw new ErrorDatos(`${nombreZip} no es un zip, o está incompleto.`);
  const total = vista.getUint16(fin + 10, true);
  let p = vista.getUint32(fin + 16, true);
  if (p === 0xffffffff || total === 0xffff) throw new ErrorDatos(`${nombreZip} es demasiado grande (zip64).`);

  const entradas = [];
  for (let n = 0; n < total; n++) {
    if (p + 46 > datos.length || vista.getUint32(p, true) !== 0x02014b50) {
      throw new ErrorDatos(`${nombreZip} está dañado: su índice no se puede leer.`);
    }
    const flags = vista.getUint16(p + 8, true);
    const metodo = vista.getUint16(p + 10, true);
    const crc = vista.getUint32(p + 16, true);
    const tamGuardado = vista.getUint32(p + 20, true);
    const largoNombre = vista.getUint16(p + 28, true);
    const largoExtra = vista.getUint16(p + 30, true);
    const largoComentario = vista.getUint16(p + 32, true);
    const local = vista.getUint32(p + 42, true);
    const nombreBytes = datos.subarray(p + 46, p + 46 + largoNombre);
    // Sin el bit 11, el nombre está en la página de códigos 437; para los nombres ASCII, que
    // son todos los que importan aquí, se lee igual.
    const nombre = new TextDecoder(flags & 0x0800 ? 'utf-8' : 'latin1').decode(nombreBytes);
    p += 46 + largoNombre + largoExtra + largoComentario;

    if (flags & 0x0001) throw new ErrorDatos(`${nombreZip}: «${nombre}» está cifrado, y Codabench no lo podrá abrir.`);
    const carpeta = nombre.endsWith('/');
    if (carpeta) {
      entradas.push({ nombre, datos: new Uint8Array(0), carpeta, metodo });
      continue;
    }
    const inicio = local + 30 + vista.getUint16(local + 26, true) + vista.getUint16(local + 28, true);
    const guardado = datos.subarray(inicio, inicio + tamGuardado);
    let contenido;
    if (metodo === 0) {
      contenido = guardado.slice();
    } else if (metodo === 8) {
      try {
        contenido = await transformar(guardado, new DecompressionStream('deflate-raw'));
      } catch {
        throw new ErrorDatos(`${nombreZip}: «${nombre}» no se puede descomprimir en este navegador, o está dañado.`);
      }
    } else {
      throw new ErrorDatos(`${nombreZip}: «${nombre}» usa un método de compresión (${metodo}) que no se puede leer aquí.`, 'Vuelve a comprimirlo con la opción normal (deflate) de tu sistema.');
    }
    if (crc32(contenido) !== crc) throw new ErrorDatos(`${nombreZip} está dañado: «${nombre}» no pasa la comprobación de integridad.`);
    entradas.push({ nombre, datos: contenido, carpeta, metodo });
  }
  return entradas;
}
