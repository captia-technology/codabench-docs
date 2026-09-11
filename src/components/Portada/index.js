/**
 * Piezas de la portada de la guía.
 *
 * Copia exacta de las de `my-qa-captia-ai-app`: mismos componentes, mismas clases, mismos
 * tokens. Lo único propio de este sitio es el contenido que se les pasa desde `docs/index.mdx`.
 *
 * Son adaptadores documentales, no componentes de la aplicación: no importan nada de
 * Codabench ni de captia.ai, no tocan `window` al evaluar el módulo y renderizan igual en servidor y en
 * cliente. Toda la marca sale de los tokens de `src/css/custom.css`.
 *
 * El logotipo se importa desde `static/img/logo-mark.svg` —el mark real del design system—
 * y Docusaurus lo convierte en componente React. No se recolorea ni se sustituye.
 */

import React from 'react';
import Link from '@docusaurus/Link';
import MarcaCaptia from '@site/static/img/logo-mark.svg';
import styles from './styles.module.css';

/**
 * Panel de cabecera: qué es esto, para qué sirve y por dónde se entra.
 *
 * `rotulo` es la única diferencia con el componente del manual de captia.ai, del que esto es
 * copia: allí el texto «Manual funcional» estaba fijado en el JSX porque solo servía a un sitio.
 * Aquí es una prop con ese mismo valor por defecto —el original renderiza idéntico— y este sitio
 * pasa el suyo, porque una guía de una plataforma ajena no es el manual funcional de nada.
 */
export function Portada({ version, titulo, entradilla, acciones = [], rotulo = 'Manual funcional' }) {
  return (
    <header className={styles.hero}>
      <div className={styles.heroGrid}>
        <div className={styles.heroTexto}>
          <p className={styles.heroEyebrow}>
            {rotulo}
            <span>{version}</span>
          </p>
          <h1 className={styles.heroTitulo}>{titulo}</h1>
          <p className={styles.heroEntradilla}>{entradilla}</p>
          {acciones.length > 0 && (
            <div className={styles.heroAcciones}>
              {acciones.map((accion, i) => (
                <Link
                  key={accion.to}
                  to={accion.to}
                  className={i === 0 ? styles.accionPrimaria : styles.accionSecundaria}
                >
                  {accion.label}
                </Link>
              ))}
            </div>
          )}
        </div>
        <div className={styles.heroMarca} aria-hidden="true">
          <MarcaCaptia />
        </div>
      </div>
    </header>
  );
}

/** Bloque con título, entradilla opcional y contenido. */
export function Bloque({ titulo, entradilla, children }) {
  return (
    <section className={styles.bloque}>
      <div className={styles.bloqueCabecera}>
        <h2 className={styles.bloqueTitulo}>{titulo}</h2>
        {entradilla && <p className={styles.bloqueEntradilla}>{entradilla}</p>}
      </div>
      {children}
    </section>
  );
}

/** Rejilla de tarjetas. `ancha` da columnas más anchas para textos largos. */
export function Rejilla({ ancha = false, children }) {
  return (
    <div className={`${styles.rejilla} ${ancha ? styles.rejillaAncha : ''}`}>{children}</div>
  );
}

/**
 * Tarjeta de entrada. La tarjeta ENTERA es el enlace, así que no lleva controles dentro:
 * un enlace anidado dentro de otro no es navegable con teclado.
 *
 * El contenedor del texto es un `div`, no un `p`. MDX ya envuelve en `<p>` el párrafo que se
 * escribe dentro de `<Tarjeta>`; meterlo dentro de otro `<p>` produce un anidamiento inválido
 * que el navegador deshace al parsear, y ahí el HTML del servidor deja de coincidir con el que
 * React espera: la portada entera caía a renderizado en cliente (errores React #418 y #423).
 */
export function Tarjeta({ titulo, meta, to, accion = 'Abrir', children }) {
  return (
    <Link to={to} className={styles.tarjeta}>
      <div className={styles.tarjetaCabecera}>
        <span className={styles.tarjetaTitulo}>{titulo}</span>
        {meta && <span className={styles.tarjetaMeta}>{meta}</span>}
      </div>
      <div className={styles.tarjetaTexto}>{children}</div>
      <span className={styles.tarjetaPie}>{accion}</span>
    </Link>
  );
}

/** Los tres bloques que tiene cada documento del manual, explicados una sola vez. */
export function Anatomia({ pasos }) {
  return (
    <div className={styles.anatomia}>
      {pasos.map((paso, i) => (
        <div key={paso.titulo} className={styles.anatomiaPaso}>
          <span className={styles.anatomiaOrden}>{String(i + 1).padStart(2, '0')}</span>
          <h3 className={styles.anatomiaTitulo}>{paso.titulo}</h3>
          <p className={styles.anatomiaTexto}>{paso.texto}</p>
        </div>
      ))}
    </div>
  );
}
