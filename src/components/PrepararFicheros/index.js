/**
 * La herramienta «Preparar los ficheros»: generar los zip de una competición a partir de un CSV,
 * comprobar unos zip hechos a mano y descargar el programa de puntuación genérico.
 *
 * Todo ocurre en el navegador (decisión P4 de docs-meta/07): el CSV y los zip no se envían a
 * ningún sitio. Las únicas peticiones de red son las de las plantillas de `static/plantillas/`,
 * que se leen para meterlas en los zip y no llevan datos.
 *
 * La lógica vive en los módulos `.mjs` de esta carpeta, sin React, y se prueba con `node --test`
 * (scripts/preparar.test.mjs y scripts/zip.test.mjs). Aquí solo hay interfaz.
 *
 * Docusaurus renderiza también en servidor. Lo que usa APIs del navegador (ficheros, Blob,
 * CompressionStream) va dentro de `BrowserOnly` y de manejadores de eventos, nunca al evaluar el
 * módulo. Los estilos salen de los tokens del tema (`--ifm-*` y `--captia-*` de custom.css) y los
 * botones y avisos son las primitivas del propio tema: aquí no se define ningún color.
 */

import React, { useEffect, useId, useMemo, useRef, useState } from 'react';
import clsx from 'clsx';
import BrowserOnly from '@docusaurus/BrowserOnly';
import useBaseUrl from '@docusaurus/useBaseUrl';
import Admonition from '@theme/Admonition';

import { ErrorDatos, decodificarUtf8, leerCsv } from './csv.mjs';
import { analizar, errorFormatoAncho, parsearFecha, sugerirTipo } from './analisis.mjs';
import { FICHEROS_KIT, ORDEN_ZIPS, PARTE_PRUEBA, empaquetar, nombreCorto, prepararCompeticion } from './generar.mjs';
import { COLUMNAS, formatoDecimal } from './metricas.mjs';
import { PAPELES, comprobarZips } from './comprobar.mjs';
import { crearZip, puedeComprimir } from './zip.mjs';
import styles from './styles.module.css';

// ------------------------------------------------------------------------------- utilidades

/** Lee las plantillas de `static/plantillas/` una sola vez por página. */
function usePlantillas() {
  const base = useBaseUrl('/plantillas/');
  const cache = useRef(null);
  return () => {
    if (!cache.current) {
      const leer = async (ruta) => {
        const respuesta = await fetch(base + ruta, { credentials: 'same-origin' });
        if (!respuesta.ok) throw new Error(`no se ha podido cargar ${ruta} (${respuesta.status})`);
        return respuesta.text();
      };
      cache.current = Promise.all([
        leer('puntuacion/score.py'),
        leer('puntuacion/metadata'),
        ...FICHEROS_KIT.map((n) => leer(`kit/${n}`)),
      ]).then(
        ([scorePy, metadata, ...kit]) => ({
          scorePy,
          metadata,
          kit: Object.fromEntries(FICHEROS_KIT.map((n, i) => [n, kit[i]])),
        }),
        (e) => {
          cache.current = null; // que el siguiente intento vuelva a pedirlas
          throw e;
        },
      );
    }
    return cache.current;
  };
}

/** Descarga unos bytes como fichero, sin salir de la página. */
function descargar(nombre, bytes) {
  const url = URL.createObjectURL(new Blob([bytes], { type: 'application/zip' }));
  const enlace = document.createElement('a');
  enlace.href = url;
  enlace.download = nombre;
  document.body.appendChild(enlace);
  enlace.click();
  enlace.remove();
  setTimeout(() => URL.revokeObjectURL(url), 10000);
}

const tamano = (bytes) =>
  bytes < 1024 * 1024
    ? `${Math.max(1, Math.round(bytes / 1024))} KB`
    : `${(bytes / 1024 / 1024).toFixed(1).replace('.', ',')} MB`;

/** El mensaje de un error para la pantalla: el de la herramienta tal cual, el resto con contexto. */
const comoError = (e, contexto) =>
  e instanceof ErrorDatos ? { mensaje: e.message, pista: e.pista } : { mensaje: `${contexto}: ${e.message}` };

/** Texto con `código` entre comillas invertidas, como lo escriben los mensajes de comprobar.mjs. */
function ConCodigo({ texto }) {
  return texto.split('`').map((trozo, i) => (i % 2 ? <code key={i}>{trozo}</code> : trozo));
}

function Fallo({ error }) {
  if (!error) return null;
  return (
    <div role="alert">
      <Admonition type="danger" title="No se puede seguir">
        <p>{error.mensaje}</p>
        {error.pista && <p>{error.pista}</p>}
      </Admonition>
    </div>
  );
}

/** Zona de arrastrar y soltar alrededor de un `<input type="file">`, que es lo que maneja el teclado. */
function ZonaFichero({ etiqueta, ayuda, accept, elegido, onArchivo }) {
  const id = useId();
  const [encima, setEncima] = useState(false);
  return (
    <div
      className={clsx(styles.zona, encima && styles.zonaActiva)}
      onDragOver={(e) => {
        e.preventDefault();
        setEncima(true);
      }}
      onDragLeave={() => setEncima(false)}
      onDrop={(e) => {
        e.preventDefault();
        setEncima(false);
        if (e.dataTransfer.files[0]) onArchivo(e.dataTransfer.files[0]);
      }}
    >
      <label htmlFor={id} className={styles.etiqueta}>
        {etiqueta}
      </label>
      {ayuda && (
        <p id={`${id}-ayuda`} className={styles.ayuda}>
          {ayuda}
        </p>
      )}
      <input
        id={id}
        type="file"
        accept={accept}
        className={styles.fichero}
        aria-describedby={ayuda ? `${id}-ayuda` : undefined}
        onChange={(e) => {
          const archivo = e.target.files[0];
          // Vaciar el campo permite volver a elegir el mismo fichero después de corregirlo.
          e.target.value = '';
          if (archivo) onArchivo(archivo);
        }}
      />
      {elegido && (
        <p className={styles.elegido}>
          Elegido: <code>{elegido}</code>
        </p>
      )}
    </div>
  );
}

const CONTENIDO = { fecha: 'fechas', numero: 'números', texto: 'texto', vacia: 'vacía' };

function ResumenColumnas({ csv }) {
  const { analisis, nombre } = csv;
  const n = analisis.filas;
  return (
    <>
      <p>
        <code>{nombre}</code>: {n} filas y {analisis.columnas.length} columnas. Columna de tiempo propuesta:{' '}
        {analisis.tiempo ? <code>{analisis.tiempo}</code> : 'ninguna'}. De grupo:{' '}
        {analisis.grupo ? <code>{analisis.grupo}</code> : 'ninguna'}. Columna id:{' '}
        {analisis.id ? <code>{analisis.id}</code> : 'no hay, se generará'}.
      </p>
      <table className={styles.tabla}>
        <thead>
          <tr>
            <th scope="col">Columna</th>
            <th scope="col">Contenido</th>
            <th scope="col">Vacíos</th>
            <th scope="col">Valores distintos</th>
            <th scope="col">Ejemplo</th>
          </tr>
        </thead>
        <tbody>
          {analisis.columnas.map((c) => (
            <tr key={c.nombre}>
              <td>
                <code>{c.nombre}</code>
              </td>
              <td>{CONTENIDO[c.clase]}</td>
              <td>{c.vacios ? `${c.vacios} (${Math.round((c.vacios / n) * 100)} %)` : '0'}</td>
              <td>{c.distintos}</td>
              <td>{c.ejemplo}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </>
  );
}

function TablaReferencias({ resumen }) {
  const columnas = COLUMNAS[resumen.tipo];
  return (
    <table className={styles.tabla}>
      <thead>
        <tr>
          <th scope="col">Solución de referencia</th>
          {columnas.map((c) => (
            <th scope="col" key={c.clave}>
              {c.titulo}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {resumen.referencias.map((r) => (
          <tr key={r.nombre}>
            <td>
              {r.nombre}
              {r.kit && ' (la del kit de inicio)'}
            </td>
            {columnas.map((c) => (
              <td key={c.clave}>{formatoDecimal(r.metricas[c.clave])}</td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}

// ---------------------------------------------------------------------------------- generar

function Generar() {
  const id = useId();
  const cargarPlantillas = usePlantillas();
  const [csv, setCsv] = useState(null);
  const [error, setError] = useState(null);
  const [objetivo, setObjetivo] = useState('');
  const [tiempo, setTiempo] = useState('');
  const [grupo, setGrupo] = useState('');
  const [tipo, setTipo] = useState('numero');
  const [corte, setCorte] = useState('porcentaje');
  const [fecha, setFecha] = useState('');
  const [nombre, setNombre] = useState('');
  const [resultado, setResultado] = useState(null);
  const [ocupado, setOcupado] = useState(false);
  const refResultado = useRef(null);

  // Un cambio en cualquier opción deja viejos los zip ya generados: se retiran para que nadie
  // descargue unos ficheros que no corresponden a lo que tiene en pantalla.
  useEffect(() => setResultado(null), [csv, objetivo, tiempo, grupo, tipo, corte, fecha, nombre]);

  useEffect(() => {
    if (resultado && refResultado.current) refResultado.current.focus();
  }, [resultado]);

  const columna = (nombreColumna) => {
    const i = csv.datos.cabecera.indexOf(nombreColumna);
    return csv.datos.filas.map((f) => f[i]);
  };

  const sugerencia = useMemo(() => (csv && objetivo ? sugerirTipo(columna(objetivo)) : null), [csv, objetivo]);

  // Fechas que caben en el selector del corte, y el día en el que caería el 20 %, como propuesta.
  const rango = useMemo(() => {
    if (!csv || !tiempo) return null;
    const fechas = columna(tiempo)
      .map((v) => parsearFecha(v))
      .filter(Boolean)
      .map((p) => p.fecha)
      .sort();
    if (!fechas.length) return null;
    return {
      min: fechas[0],
      max: fechas[fechas.length - 1],
      propuesta: fechas[Math.floor(fechas.length * (1 - PARTE_PRUEBA))],
    };
  }, [csv, tiempo]);

  async function abrirCsv(archivo) {
    setError(null);
    setCsv(null);
    setObjetivo('');
    try {
      const texto = decodificarUtf8(new Uint8Array(await archivo.arrayBuffer()), archivo.name);
      const datos = leerCsv(texto, archivo.name);
      const analisis = analizar(datos.cabecera, datos.filas);
      if (analisis.ancho) throw errorFormatoAncho(analisis.ancho);
      setCsv({ nombre: archivo.name, datos, analisis });
      setTiempo(analisis.tiempo || '');
      setGrupo(analisis.grupo || '');
      setCorte('porcentaje');
      setFecha('');
      setNombre(nombreCorto(archivo.name));
    } catch (e) {
      setError(comoError(e, `No se ha podido leer ${archivo.name}`));
    }
  }

  function elegirObjetivo(valor) {
    setObjetivo(valor);
    if (valor) setTipo(sugerirTipo(columna(valor)).tipo);
  }

  function elegirCorte(valor) {
    setCorte(valor);
    if (valor === 'fecha' && !fecha && rango) setFecha(rango.propuesta);
  }

  async function generar(e) {
    e.preventDefault();
    setError(null);
    setOcupado(true);
    try {
      const plantillas = await cargarPlantillas();
      const { resumen, ficheros } = prepararCompeticion(
        csv.datos,
        {
          objetivo,
          tipo,
          tiempo: tiempo || null,
          grupo: grupo || null,
          corte: tiempo && corte === 'fecha' ? { modo: 'fecha', fecha } : { modo: 'porcentaje' },
          nombre,
        },
        plantillas,
      );
      setResultado({ resumen, zips: await empaquetar(ficheros, resumen.zips) });
    } catch (err) {
      setError(comoError(err, 'No se han podido generar los ficheros'));
    } finally {
      setOcupado(false);
    }
  }

  const fechas = csv ? csv.analisis.columnas.filter((c) => c.clase === 'fecha') : [];
  const otras = csv ? csv.datos.cabecera.filter((c) => c !== objetivo && c !== tiempo) : [];

  return (
    <div className={styles.herramienta}>
      <section className={styles.paso} aria-labelledby={`${id}-csv`}>
        <h3 id={`${id}-csv`} className={styles.titulo}>
          1. El CSV
        </h3>
        <ZonaFichero
          etiqueta="Arrastra aquí el CSV o elígelo"
          ayuda="Una fila por caso, separado por comas y en UTF-8. La descarga de un equipo desde captia.ai ya sale así."
          accept=".csv,text/csv"
          elegido={csv && csv.nombre}
          onArchivo={abrirCsv}
        />
        {!csv && <Fallo error={error} />}
        {csv && <ResumenColumnas csv={csv} />}
      </section>

      {csv && (
        <form className={styles.paso} onSubmit={generar} aria-labelledby={`${id}-opciones`}>
          <h3 id={`${id}-opciones`} className={styles.titulo}>
            2. Qué se predice y dónde empieza la prueba
          </h3>
          <div className={styles.campos}>
            <div className={styles.campo}>
              <label htmlFor={`${id}-objetivo`} className={styles.etiqueta}>
                Columna a predecir
              </label>
              <select id={`${id}-objetivo`} required value={objetivo} onChange={(e) => elegirObjetivo(e.target.value)}>
                <option value="">Elige una columna</option>
                {csv.datos.cabecera
                  .filter((c) => c !== tiempo && c !== grupo && c !== csv.analisis.id)
                  .map((c) => (
                    <option key={c} value={c}>
                      {c}
                    </option>
                  ))}
              </select>
            </div>
            <div className={styles.campo}>
              <label htmlFor={`${id}-tiempo`} className={styles.etiqueta}>
                Columna de tiempo
              </label>
              <select id={`${id}-tiempo`} value={tiempo} aria-describedby={`${id}-tiempo-ayuda`} onChange={(e) => setTiempo(e.target.value)}>
                <option value="">Ninguna</option>
                {fechas.map((c) => (
                  <option key={c.nombre} value={c.nombre}>
                    {c.nombre}
                  </option>
                ))}
              </select>
              <p id={`${id}-tiempo-ayuda`} className={styles.ayuda}>
                {fechas.length ? 'Ordena las filas y marca dónde empieza la prueba.' : 'No hay ninguna columna con fechas.'}
              </p>
            </div>
            <div className={styles.campo}>
              <label htmlFor={`${id}-grupo`} className={styles.etiqueta}>
                Columna de grupo (opcional)
              </label>
              <select id={`${id}-grupo`} value={grupo} aria-describedby={`${id}-grupo-ayuda`} onChange={(e) => setGrupo(e.target.value)}>
                <option value="">Ninguna</option>
                {otras.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
              <p id={`${id}-grupo-ayuda`} className={styles.ayuda}>
                Lo que separa una serie de otra: el aula, el equipo…
              </p>
            </div>
          </div>

          <fieldset className={styles.opciones}>
            <legend className={styles.etiqueta}>Tipo de competición</legend>
            <label className={styles.opcion}>
              <input type="radio" name={`${id}-tipo`} value="numero" checked={tipo === 'numero'} onChange={() => setTipo('numero')} />
              Número: estimar una cantidad (regresión, se puntúa con MAE)
            </label>
            <label className={styles.opcion}>
              <input type="radio" name={`${id}-tipo`} value="categoria" checked={tipo === 'categoria'} onChange={() => setTipo('categoria')} />
              Categoría: acertar una clase (clasificación, se puntúa con F1 macro)
            </label>
            {sugerencia && (
              <p className={styles.ayuda}>
                {sugerencia.motivo}
                {sugerencia.tipo !== tipo && ' Has elegido el otro tipo: se usará el tuyo.'}
              </p>
            )}
          </fieldset>

          <fieldset className={styles.opciones}>
            <legend className={styles.etiqueta}>Dónde empieza la prueba</legend>
            {tiempo ? (
              <>
                <label className={styles.opcion}>
                  <input type="radio" name={`${id}-corte`} value="porcentaje" checked={corte === 'porcentaje'} onChange={() => elegirCorte('porcentaje')} />
                  En el último 20 % del tiempo
                </label>
                <label className={styles.opcion}>
                  <input type="radio" name={`${id}-corte`} value="fecha" checked={corte === 'fecha'} onChange={() => elegirCorte('fecha')} />
                  Desde una fecha
                </label>
                {corte === 'fecha' && (
                  <div className={styles.campo}>
                    <label htmlFor={`${id}-fecha`} className={styles.etiqueta}>
                      Primer día de la prueba
                    </label>
                    <input
                      id={`${id}-fecha`}
                      type="date"
                      required
                      value={fecha}
                      min={rango ? rango.min : undefined}
                      max={rango ? rango.max : undefined}
                      onChange={(e) => setFecha(e.target.value)}
                    />
                  </div>
                )}
                <p className={styles.ayuda}>
                  El reparto es por fecha, nunca al azar: con un reparto al azar la misma hora acaba en los dos lados
                  y la nota no dice nada.
                </p>
              </>
            ) : (
              <p className={styles.ayuda}>
                Sin columna de tiempo, la prueba es el último 20 % de las filas, en el orden del fichero.
              </p>
            )}
          </fieldset>

          <div className={styles.campo}>
            <label htmlFor={`${id}-nombre`} className={styles.etiqueta}>
              Nombre corto de la competición
            </label>
            <input
              id={`${id}-nombre`}
              type="text"
              value={nombre}
              aria-describedby={`${id}-nombre-ayuda`}
              onChange={(e) => setNombre(e.target.value)}
            />
            <p id={`${id}-nombre-ayuda`} className={styles.ayuda}>
              Va en el nombre de los zip: <code>public_data_{nombreCorto(nombre)}.zip</code>. Ayuda a distinguirlos en los
              desplegables de Codabench.
            </p>
          </div>

          <div className={styles.acciones}>
            <button type="submit" className="button button--primary" disabled={ocupado}>
              Generar los ficheros
            </button>
            <span role="status" className={styles.ayuda}>
              {ocupado ? 'Generando…' : ''}
            </span>
          </div>
          <Fallo error={error} />
        </form>
      )}

      {resultado && <Resultado resultado={resultado} refTitulo={refResultado} />}
    </div>
  );
}

function Resultado({ resultado, refTitulo }) {
  const id = useId();
  const { resumen, zips } = resultado;
  const periodo = (p) => (p ? `, del ${p.desde} al ${p.hasta}` : '');
  return (
    <section className={styles.paso} aria-labelledby={`${id}-titulo`}>
      <h3 id={`${id}-titulo`} className={styles.titulo} tabIndex={-1} ref={refTitulo}>
        3. Descarga los ficheros
      </h3>
      <ul>
        <li>
          Entrenamiento (<code>train.csv</code>): {resumen.filasEntrenamiento} filas{periodo(resumen.periodoEntrenamiento)}.
        </li>
        <li>
          Prueba (<code>test.csv</code>): {resumen.filasPrueba} filas{periodo(resumen.periodoPrueba)}.
        </li>
        <li>
          {resumen.idGenerado ? 'Los id los ha generado la herramienta' : `Los id son los de la columna ${resumen.id}`}, por
          ejemplo <code>{resumen.ejemploId}</code>.
        </li>
      </ul>
      {resumen.avisos.length > 0 && (
        <Admonition type="warning" title="Revisa esto antes de seguir">
          <ul>
            {resumen.avisos.map((a) => (
              <li key={a}>{a}</li>
            ))}
          </ul>
        </Admonition>
      )}
      <p>
        Las notas de referencia, calculadas con las mismas cuentas que hará Codabench. Si subes{' '}
        <code>sample_submission.csv</code> como envío, tiene que salir la de la solución del kit de inicio.
      </p>
      <TablaReferencias resumen={resumen} />
      {!puedeComprimir() && (
        <p className={styles.ayuda}>
          Este navegador no puede comprimir: los zip van sin comprimir. Ocupan más, pero Codabench los abre igual.
        </p>
      )}
      <div className={styles.descargas}>
        {ORDEN_ZIPS.map((papel) => (
          <button
            key={papel}
            type="button"
            className="button button--outline button--primary"
            onClick={() => descargar(resumen.zips[papel], zips[papel])}
          >
            {resumen.zips[papel]} ({tamano(zips[papel].length)})
          </button>
        ))}
      </div>
      <div className={styles.acciones}>
        <button type="button" className="button button--primary" onClick={() => descargar(resumen.zips.todo, zips.todo)}>
          Descargar todo ({tamano(zips.todo.length)})
        </button>
        <span className={styles.ayuda}>
          Los cuatro zip, <code>INSTRUCCIONES.md</code> con dónde va cada uno y las páginas base en{' '}
          <code>paginas/</code>.
        </span>
      </div>
    </section>
  );
}

// -------------------------------------------------------------------------------- comprobar

// El estado va siempre escrito; el borde de color solo lo acompaña.
const ESTADO = {
  ok: { texto: 'Correcto', clase: styles.estadoOk },
  error: { texto: 'Error', clase: styles.estadoError },
  aviso: { texto: 'Aviso', clase: styles.estadoAviso },
  'sin-comprobar': { texto: 'Sin comprobar', clase: styles.estadoSinComprobar },
};

function Comprobar() {
  const id = useId();
  const [archivos, setArchivos] = useState({});
  const [informe, setInforme] = useState(null);
  const [ocupado, setOcupado] = useState(false);
  const refInforme = useRef(null);

  useEffect(() => {
    if (informe && refInforme.current) refInforme.current.focus();
  }, [informe]);

  async function comprobar(e) {
    e.preventDefault();
    setOcupado(true);
    try {
      const entrada = {};
      for (const papel of PAPELES) {
        const archivo = archivos[papel.clave];
        if (archivo) entrada[papel.clave] = { nombre: archivo.name, bytes: new Uint8Array(await archivo.arrayBuffer()) };
      }
      setInforme(await comprobarZips(entrada));
    } catch (err) {
      setInforme([{ zip: '', estado: 'error', mensaje: `No se ha podido comprobar: ${err.message}`, arreglo: '' }]);
    } finally {
      setOcupado(false);
    }
  }

  const errores = informe ? informe.filter((r) => r.estado === 'error').length : 0;
  const avisos = informe ? informe.filter((r) => r.estado === 'aviso').length : 0;

  return (
    <form className={styles.herramienta} onSubmit={comprobar} aria-labelledby={`${id}-titulo`}>
      <h3 id={`${id}-titulo`} className={styles.titulo}>
        Tus cuatro zip
      </h3>
      <p className={styles.ayuda}>Elige los que tengas. Los que falten se quedan sin comprobar.</p>
      <div className={styles.campos}>
        {PAPELES.map((papel) => (
          <ZonaFichero
            key={papel.clave}
            etiqueta={`${papel.titulo} (${papel.tipo})`}
            accept=".zip,application/zip"
            elegido={archivos[papel.clave] && archivos[papel.clave].name}
            onArchivo={(archivo) => {
              setInforme(null);
              setArchivos((a) => ({ ...a, [papel.clave]: archivo }));
            }}
          />
        ))}
      </div>
      <div className={styles.acciones}>
        <button type="submit" className="button button--primary" disabled={ocupado}>
          Comprobar
        </button>
        <span role="status" className={styles.ayuda}>
          {ocupado ? 'Comprobando…' : ''}
        </span>
      </div>

      {informe && (
        <section aria-labelledby={`${id}-informe`}>
          <h3 id={`${id}-informe`} className={styles.titulo} tabIndex={-1} ref={refInforme}>
            {errores ? `${errores} ${errores === 1 ? 'cosa que corregir' : 'cosas que corregir'}` : 'Nada que corregir'}
            {avisos ? ` y ${avisos} ${avisos === 1 ? 'aviso' : 'avisos'}` : ''}
          </h3>
          {PAPELES.filter((p) => informe.some((r) => r.zip === p.clave)).map((papel) => (
            <div key={papel.clave}>
              <h4 className={styles.subtitulo}>
                {papel.titulo} <code>{papel.tipo}</code>
              </h4>
              <ul className={styles.informe}>
                {informe
                  .filter((r) => r.zip === papel.clave)
                  .map((r, i) => (
                    <li key={i} className={clsx(styles.resultado, ESTADO[r.estado].clase)}>
                      <strong>{ESTADO[r.estado].texto}.</strong> <ConCodigo texto={r.mensaje} />
                      {r.arreglo && (
                        <span className={styles.arreglo}>
                          Cómo arreglarlo: <ConCodigo texto={r.arreglo} />
                        </span>
                      )}
                    </li>
                  ))}
              </ul>
            </div>
          ))}
          {informe
            .filter((r) => !r.zip)
            .map((r, i) => (
              <Fallo key={i} error={{ mensaje: r.mensaje }} />
            ))}
        </section>
      )}
    </form>
  );
}

// ----------------------------------------------------------------- programa de puntuación

function Programa() {
  const id = useId();
  const cargarPlantillas = usePlantillas();
  const [columna, setColumna] = useState('');
  const [tipo, setTipo] = useState('numero');
  const [idCol, setIdCol] = useState('id');
  const [error, setError] = useState(null);
  const [ocupado, setOcupado] = useState(false);

  async function bajar(e) {
    e.preventDefault();
    setError(null);
    setOcupado(true);
    try {
      const { scorePy, metadata } = await cargarPlantillas();
      const config = { columna: columna.trim(), tipo, id: idCol.trim() || 'id' };
      const zip = await crearZip([
        { nombre: 'metadata', datos: metadata },
        { nombre: 'score.py', datos: scorePy },
        { nombre: 'config.json', datos: JSON.stringify(config, null, 2) + '\n' },
      ]);
      descargar('scoring_program.zip', zip);
    } catch (err) {
      setError(comoError(err, 'No se ha podido preparar el programa'));
    } finally {
      setOcupado(false);
    }
  }

  return (
    <form className={styles.herramienta} onSubmit={bajar} aria-label="Descargar el programa de puntuación">
      <div className={styles.campos}>
        <div className={styles.campo}>
          <label htmlFor={`${id}-columna`} className={styles.etiqueta}>
            Columna a predecir
          </label>
          <input id={`${id}-columna`} type="text" required value={columna} onChange={(e) => setColumna(e.target.value)} />
          <p className={styles.ayuda}>Tal como se llama en tus CSV, con las mismas mayúsculas.</p>
        </div>
        <div className={styles.campo}>
          <label htmlFor={`${id}-id`} className={styles.etiqueta}>
            Columna del id
          </label>
          <input id={`${id}-id`} type="text" required value={idCol} onChange={(e) => setIdCol(e.target.value)} />
        </div>
      </div>
      <fieldset className={styles.opciones}>
        <legend className={styles.etiqueta}>Tipo</legend>
        <label className={styles.opcion}>
          <input type="radio" name={`${id}-tipo`} value="numero" checked={tipo === 'numero'} onChange={() => setTipo('numero')} />
          Número (puntúa con <code>mae</code> y <code>rmse</code>)
        </label>
        <label className={styles.opcion}>
          <input type="radio" name={`${id}-tipo`} value="categoria" checked={tipo === 'categoria'} onChange={() => setTipo('categoria')} />
          Categoría (puntúa con <code>f1</code> y <code>aciertos</code>)
        </label>
      </fieldset>
      <div className={styles.acciones}>
        <button type="submit" className="button button--primary" disabled={ocupado}>
          Descargar scoring_program.zip
        </button>
      </div>
      <Fallo error={error} />
    </form>
  );
}

// ------------------------------------------------------------------------------ exportados

function Cargando() {
  return (
    <p className={styles.herramienta}>
      Cargando la herramienta. Si no aparece, comprueba que el navegador tiene JavaScript activado.
    </p>
  );
}

/** Generar los zip desde un CSV. */
export function GenerarFicheros() {
  return <BrowserOnly fallback={<Cargando />}>{() => <Generar />}</BrowserOnly>;
}

/** Comprobar unos zip hechos a mano. */
export function ComprobarFicheros() {
  return <BrowserOnly fallback={<Cargando />}>{() => <Comprobar />}</BrowserOnly>;
}

/** El programa de puntuación genérico, con su config.json ya escrito. */
export function DescargarPrograma() {
  return <BrowserOnly fallback={<Cargando />}>{() => <Programa />}</BrowserOnly>;
}
