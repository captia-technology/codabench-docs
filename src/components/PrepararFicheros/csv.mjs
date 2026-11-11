/**
 * Leer y escribir CSV (RFC 4180) sin dependencias.
 *
 * Es la puerta de entrada de la herramienta, y casi todo lo que puede salir mal con un CSV
 * hecho por una persona sale aquí: Excel en español guarda con punto y coma, y si no se elige
 * «CSV UTF-8» guarda en Windows-1252. Por eso los errores no se limitan a decir qué falla:
 * llevan una `pista` con cómo arreglarlo, que la interfaz enseña tal cual.
 *
 * Sin React y sin APIs del navegador más allá de `TextDecoder`, que también existe en Node:
 * así se prueba con `node --test` (scripts/preparar.test.mjs).
 */

/** Un error en los datos del usuario, con un mensaje y una pista pensados para leerse en pantalla. */
export class ErrorDatos extends Error {
  constructor(mensaje, pista = '') {
    super(mensaje);
    this.name = 'ErrorDatos';
    this.pista = pista;
  }
}

const PISTA_EXCEL =
  'En Excel: Archivo → Guardar como → «CSV UTF-8 (delimitado por comas)». ' +
  'En LibreOffice: Guardar como CSV, con «Unicode (UTF-8)» y la coma como separador.';

/**
 * Bytes a texto, exigiendo UTF-8. Quita el BOM que pone Excel (y la descarga de captia.ai).
 *
 * `fatal: true` es lo que convierte un fichero en Windows-1252 en un error en vez de en una
 * columna con «a�o» que nadie ve hasta que el participante abre los datos.
 */
export function decodificarUtf8(bytes, nombre = 'El fichero') {
  try {
    return new TextDecoder('utf-8', { fatal: true }).decode(bytes);
  } catch {
    throw new ErrorDatos(`${nombre} no está en UTF-8.`, PISTA_EXCEL);
  }
}

/** La primera línea física, para mirar el separador antes de interpretar nada. */
function primeraLinea(texto) {
  const fin = texto.search(/\r|\n/);
  return fin === -1 ? texto : texto.slice(0, fin);
}

/**
 * Lee un CSV separado por comas.
 *
 * Devuelve `{ cabecera, filas, lineas }`: los nombres de columna, las filas como listas de
 * textos (sin espacios a los lados) y, para cada fila, la línea del fichero en la que empieza,
 * que es lo que necesita un mensaje de error para que se pueda encontrar.
 */
export function leerCsv(texto, nombre = 'El fichero') {
  if (texto.charCodeAt(0) === 0xfeff) texto = texto.slice(1);
  const cabeceraCruda = primeraLinea(texto);
  if (!cabeceraCruda.includes(',')) {
    if (cabeceraCruda.includes(';')) {
      throw new ErrorDatos(
        `${nombre} separa las columnas con punto y coma (;). Tiene que ir con comas.`,
        'Es lo que hace Excel en español al guardar como «CSV (delimitado por comas)». ' +
          PISTA_EXCEL,
      );
    }
    if (cabeceraCruda.includes('\t')) {
      throw new ErrorDatos(`${nombre} separa las columnas con tabuladores. Tiene que ir con comas.`, PISTA_EXCEL);
    }
  }

  const registros = [];
  const lineas = [];
  let fila = [];
  let campo = '';
  let entreComillas = false;
  let linea = 1;
  let lineaFila = 1;
  let lineaComillas = 1;

  const cerrarFila = () => {
    fila.push(campo);
    // Una línea en blanco no es una fila: Excel y muchos editores dejan una al final.
    if (!(fila.length === 1 && fila[0].trim() === '')) {
      registros.push(fila);
      lineas.push(lineaFila);
    }
    fila = [];
    campo = '';
  };

  for (let i = 0; i < texto.length; i++) {
    const c = texto[i];
    if (entreComillas) {
      if (c === '"') {
        if (texto[i + 1] === '"') {
          campo += '"';
          i++;
        } else {
          entreComillas = false;
        }
      } else {
        if (c === '\n') linea++;
        campo += c;
      }
      continue;
    }
    if (c === '"' && campo.trim() === '') {
      entreComillas = true;
      lineaComillas = linea;
      campo = '';
    } else if (c === ',') {
      fila.push(campo);
      campo = '';
    } else if (c === '\r' || c === '\n') {
      if (c === '\r' && texto[i + 1] === '\n') i++;
      cerrarFila();
      linea++;
      lineaFila = linea;
    } else {
      campo += c;
    }
  }
  if (entreComillas) {
    throw new ErrorDatos(`${nombre}: hay unas comillas sin cerrar desde la línea ${lineaComillas}.`);
  }
  if (campo !== '' || fila.length > 0) cerrarFila();

  if (registros.length === 0) throw new ErrorDatos(`${nombre} está vacío.`);

  const cabecera = registros[0].map((c) => c.trim());
  cabecera.forEach((col, i) => {
    if (col === '') {
      throw new ErrorDatos(`${nombre}: la columna ${i + 1} de la cabecera no tiene nombre.`);
    }
    if (cabecera.indexOf(col) !== i) {
      throw new ErrorDatos(`${nombre}: la columna «${col}» aparece dos veces en la cabecera.`);
    }
  });

  const filas = [];
  for (let r = 1; r < registros.length; r++) {
    let valores = registros[r].map((v) => v.trim());
    if (valores.length > cabecera.length) {
      // Comas de sobra al final de la línea (lo deja así algún editor): no son datos.
      const sobrantes = valores.slice(cabecera.length);
      if (sobrantes.some((v) => v !== '')) {
        throw new ErrorDatos(
          `${nombre}, línea ${lineas[r]}: tiene ${valores.length} valores y la cabecera ${cabecera.length} columnas.`,
          '¿Hay comas dentro de un valor sin comillas, o números con coma decimal?',
        );
      }
      valores = valores.slice(0, cabecera.length);
    }
    while (valores.length < cabecera.length) valores.push('');
    filas.push(valores);
  }
  if (filas.length === 0) throw new ErrorDatos(`${nombre} solo tiene la cabecera: no hay filas de datos.`);
  return { cabecera, filas, lineas: lineas.slice(1) };
}

/** Un valor con las comillas que pide RFC 4180, y solo cuando hacen falta. */
function campoCsv(valor) {
  const s = valor === null || valor === undefined ? '' : String(valor);
  return /[",\r\n]|^\s|\s$/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
}

/** Lista de filas a CSV: comas, `\n` al final de cada línea. La codificación la pone quien escriba los bytes. */
export function escribirCsv(filas) {
  return filas.map((fila) => fila.map(campoCsv).join(',')).join('\n') + '\n';
}
