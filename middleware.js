/**
 * Control de acceso a la guía: una credencial por cliente, con página de acceso propia.
 *
 * Es el mismo middleware que el del manual de captia.ai (`my-qa-captia-ai-app`), con los textos y
 * la cookie de este sitio. Si allí se corrige algo, aquí se corrige igual.
 *
 * Vercel lo ejecuta antes de servir cualquier fichero del despliegue, en producción y en las
 * previews. Quien no tiene sesión y pide una página va a `/acceso`, un formulario con el diseño
 * de la guía; al entrar recibe una cookie de sesión firmada y vuelve a donde iba. `/salir` la
 * borra. Las decisiones que no son obvias:
 *
 * - Cierra el SITIO, no el contenido. El repositorio es público en GitHub: todo lo que hay en
 *   `docs/`, las capturas incluidas, se lee allí sin credencial. Las reglas de qué no puede salir
 *   no cambian en absoluto.
 *
 * - SIN `matcher`, a propósito. Los ejemplos de Vercel excluyen «los estáticos», pero aquí los
 *   estáticos son la guía: los chunks de JS llevan el texto de cada página, el JSON del buscador
 *   lo lleva entero y las capturas son lo que más enseña. Excluirlos dejaría el contenido abierto
 *   detrás de una portada cerrada. Por eso la página de acceso es autocontenida: el logo va en
 *   línea y el CSS también.
 *
 * - Las credenciales viven en la variable `DOCS_ACCESOS` de Vercel, nunca en el repositorio: una
 *   entrada `usuario:sha256(usuario:contraseña)` por cliente, separadas por comas o saltos de
 *   línea. Las genera `scripts/credencial_cliente.py`. Se guarda el hash y no la contraseña para
 *   que quien abra el panel de Vercel no pueda entrar con lo que lee.
 *
 * - La cookie la firma `DOCS_SESION_SECRETO` (HMAC-SHA256), que NO se deriva de `DOCS_ACCESOS`
 *   por esa misma razón: con los hashes a la vista se podría fabricar una sesión. La firma incluye
 *   el hash de la credencial, así que quitar a un cliente o rotar su contraseña invalida también
 *   las sesiones que ya tenía abiertas; rotar el secreto cierra las de todos.
 *
 * - La autenticación básica se sigue aceptando, pero sin desafío: sirve a los automatismos
 *   (`scripts/check_dominio.py`, `curl -u`), que envían la cabecera de entrada. Al no responder
 *   nunca con `WWW-Authenticate`, el navegador no vuelve a sacar su diálogo nativo.
 *
 * - Un fallo de configuración cierra el sitio; nunca lo abre. Sin `DOCS_ACCESOS` válida no entra
 *   nadie, y sin `DOCS_SESION_SECRETO` el formulario no crea sesiones.
 *
 * Alta, baja, rotación y por qué esto y no la protección por contraseña de Vercel:
 * `docs-meta/06-control-de-acceso.md`.
 */
import { createHash, createHmac, timingSafeEqual } from 'node:crypto';
import { next } from '@vercel/functions/middleware';

export const RUTA_ACCESO = '/acceso';
export const RUTA_SALIR = '/salir';
export const COOKIE = 'codabench_docs_sesion';
const DURACION_SESION = 30 * 24 * 60 * 60; // segundos
const SECRETO_MINIMO = 32;

const RE_ENTRADA = /^([a-z0-9][a-z0-9._-]*):([0-9a-f]{64})$/;
const RE_USUARIO = /^[a-z0-9][a-z0-9._-]{0,63}$/;
const RE_BASIC = /^Basic +([A-Za-z0-9+/=]+)$/i;
// Una ruta del propio sitio: empieza por una sola barra y no lleva espacios ni caracteres de
// control. Un tabulador en `/\t/otro.com` lo borra el navegador y queda `//otro.com`, que es otro
// dominio: por eso no basta con mirar el segundo carácter.
const RE_DESTINO = /^\/(?![/\\])[\x21-\x7e]*$/;

// --- Credenciales ---------------------------------------------------------------------------

/** Convierte el valor de `DOCS_ACCESOS` en un mapa usuario -> hash, y aparta lo que no encaja. */
export function leerAccesos(valor = '') {
  const accesos = new Map();
  const ignoradas = [];
  for (const entrada of valor.split(/[\s,]+/).filter(Boolean)) {
    const m = RE_ENTRADA.exec(entrada);
    if (m) accesos.set(m[1], Buffer.from(m[2], 'hex'));
    else ignoradas.push(usuarioVisible(entrada));
  }
  return { accesos, ignoradas };
}

/**
 * Lo único que va a los logs de una entrada mal formada: su usuario, y solo si lo parece. Si lo
 * pegado era una contraseña —la línea que imprime el alta, o `usuario:contraseña`—, no debe
 * acabar allí.
 */
function usuarioVisible(entrada) {
  const usuario = entrada.includes(':') ? entrada.slice(0, entrada.indexOf(':')) : '';
  return RE_USUARIO.test(usuario) ? usuario : '(sin usuario)';
}

/** ¿Están `usuario` y `contraseña` en `accesos`? */
export function credencialValida(usuario, contrasena, accesos) {
  // El usuario no distingue mayúsculas: un cliente que escribe «Cliente-A» no debería quedarse
  // fuera por eso. La contraseña sí las distingue.
  const u = String(usuario).trim().toLowerCase();
  const recibido = createHash('sha256').update(`${u}:${contrasena}`).digest();
  const esperado = accesos.get(u);
  return esperado !== undefined && timingSafeEqual(recibido, esperado);
}

/** ¿Trae la cabecera `Authorization` una credencial básica que esté en `accesos`? */
export function autorizado(cabecera, accesos) {
  const m = RE_BASIC.exec(cabecera ?? '');
  if (!m) return false;
  const texto = Buffer.from(m[1], 'base64').toString('utf8');
  const corte = texto.indexOf(':');
  if (corte < 1) return false;
  return credencialValida(texto.slice(0, corte), texto.slice(corte + 1), accesos);
}

// --- Sesión ---------------------------------------------------------------------------------

const secretoValido = (secreto) => typeof secreto === 'string' && secreto.length >= SECRETO_MINIMO;

function firmar(usuario, expira, hash, secreto) {
  return createHmac('sha256', secreto)
    .update(`${usuario}.${expira}.${hash.toString('hex')}`)
    .digest('base64url');
}

/** Valor de la cookie de sesión: `usuario.expira.firma`. */
export function crearSesion(usuario, accesos, secreto, ahora = Date.now()) {
  const expira = Math.floor(ahora / 1000) + DURACION_SESION;
  return `${usuario}.${expira}.${firmar(usuario, expira, accesos.get(usuario), secreto)}`;
}

export function sesionValida(valor, accesos, secreto, ahora = Date.now()) {
  if (!valor || !secretoValido(secreto)) return false;
  // El usuario puede llevar puntos: se corta por los dos últimos.
  const fin = valor.lastIndexOf('.');
  const medio = valor.lastIndexOf('.', fin - 1);
  if (medio < 1) return false;
  const usuario = valor.slice(0, medio);
  const expira = Number(valor.slice(medio + 1, fin));
  const hash = accesos.get(usuario);
  if (!Number.isInteger(expira) || expira * 1000 <= ahora || !hash) return false;
  const recibida = Buffer.from(valor.slice(fin + 1));
  const esperada = Buffer.from(firmar(usuario, expira, hash, secreto));
  return recibida.length === esperada.length && timingSafeEqual(recibida, esperada);
}

function leerCookie(request, nombre) {
  for (const parte of (request.headers.get('cookie') ?? '').split(';')) {
    const i = parte.indexOf('=');
    if (i > 0 && parte.slice(0, i).trim() === nombre) return parte.slice(i + 1).trim();
  }
  return null;
}

function cookieSesion(valor, maxAge, url) {
  const segura = url.protocol === 'https:' ? '; Secure' : ''; // en local se sirve por http
  return `${COOKIE}=${valor}; Path=/; Max-Age=${maxAge}; HttpOnly; SameSite=Lax${segura}`;
}

export const destinoSeguro = (valor) =>
  typeof valor === 'string' && RE_DESTINO.test(valor) && !valor.startsWith(RUTA_ACCESO) ? valor : '/';

// --- Configuración --------------------------------------------------------------------------

// Las variables no cambian durante la vida de un despliegue: se interpretan una vez por
// instancia, y así los avisos de configuración salen una vez en los logs y no en cada petición.
// Por eso un cambio en ellas no llega hasta un despliegue nuevo: *Redeploy* en el panel o, si
// eso no está a mano, un push que toque una ruta del `ignoreCommand`; uno vacío no construye.
let leido = { clave: null, accesos: new Map(), secreto: '' };

function configuracion() {
  const valor = process.env.DOCS_ACCESOS ?? '';
  const secreto = process.env.DOCS_SESION_SECRETO ?? '';
  const clave = `${valor}\0${secreto}`;
  if (clave !== leido.clave) {
    const { accesos, ignoradas } = leerAccesos(valor);
    if (ignoradas.length) {
      console.error(`DOCS_ACCESOS: entradas mal formadas, ignoradas: ${ignoradas.join(', ')}`);
    }
    if (accesos.size === 0) {
      console.error('DOCS_ACCESOS no tiene ninguna entrada válida: la guía no deja entrar a nadie');
    }
    if (!secretoValido(secreto)) {
      console.error(
        `DOCS_SESION_SECRETO falta o tiene menos de ${SECRETO_MINIMO} caracteres: ` +
          'el formulario de acceso no puede abrir sesiones',
      );
    }
    leido = { clave, accesos, secreto };
  }
  return leido;
}

// --- Respuestas -----------------------------------------------------------------------------

const SIN_CACHE = {
  'Cache-Control': 'no-store',
  'X-Robots-Tag': 'noindex, nofollow',
  'X-Content-Type-Options': 'nosniff',
};

function redirigir(destino, extra = {}) {
  return new Response(null, { status: 303, headers: { Location: destino, ...SIN_CACHE, ...extra } });
}

const esNavegacion = (request) =>
  (request.method === 'GET' || request.method === 'HEAD') &&
  (request.headers.get('sec-fetch-mode') === 'navigate' ||
    (request.headers.get('accept') ?? '').includes('text/html'));

const escapar = (texto) =>
  String(texto).replace(
    /[&<>"']/g,
    (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c],
  );

// El mark real del Captia Technology Design System (static/img/logo-mark.svg), en línea: el
// fichero está detrás de este mismo control y no cargaría en la página de acceso.
const LOGO =
  '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1024 1024" aria-hidden="true">' +
  '<rect width="1024" height="1024" fill="#00FF79"/><g fill="#0000DC">' +
  '<path d="M542.465 847.49l-103.991 0c0 -196.605 -159.949 -356.549 -356.554 -356.549l0 -103.991c253.946 0 460.545 206.599 460.545 460.54"/>' +
  '<path d="M542.255 847.49l-103.991 0c0 -176.661 96.981 -374.047 259.425 -527.998l71.534 75.481c-142.12 134.69 -226.967 303.857 -226.967 452.517"/>' +
  '<path d="M881.913 264.88c0 -15.576 -12.627 -28.204 -28.204 -28.204c-15.581 0 -28.209 12.627 -28.209 28.204c0 15.576 12.627 28.204 28.209 28.204c15.576 0 28.204 -12.627 28.204 -28.204m60.167 0c0 48.804 -39.566 88.37 -88.37 88.37c-48.809 0 -88.375 -39.566 -88.375 -88.37c0 -48.804 39.566 -88.37 88.375 -88.37c48.804 0 88.37 39.566 88.37 88.37"/>' +
  '</g></svg>';

// Los tokens son los de src/css/custom.css, con dos añadidos medidos: el borde de los campos
// (#8c8c8c sobre blanco 3.36, #64748b sobre #12151d 3.83; WCAG pide 3 para controles) y el
// aviso de error (#991b1b sobre #fef2f2 7.60, #fecaca sobre #2a1215 12.14).
const OSCURO =
  '--fondo:#0c0e14;--tarjeta:#12151d;--texto:#f1f5f9;--secundario:#94a3b8;--borde:#ffffff14;' +
  '--campo:#64748b;--primario:#00ff79;--sobre-primario:#0a0a0a;--error-fondo:#2a1215;' +
  '--error-borde:#7f1d1d;--error-texto:#fecaca;--barra:#0c0e14;--pie:#08090d;--sombra:#00000080';

const ESTILOS = `
:root{--fondo:#f5f5f5;--tarjeta:#fff;--texto:#0a0a0a;--secundario:#6b6b6b;--borde:#e0e0e0;
--campo:#8c8c8c;--primario:#0000dc;--sobre-primario:#fff;--error-fondo:#fef2f2;
--error-borde:#fecaca;--error-texto:#991b1b;--barra:#fff;--pie:#0a0a0a;--sombra:#0000001a}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){${OSCURO}}}
:root[data-theme=dark]{${OSCURO}}
*{box-sizing:border-box}
body{margin:0;min-height:100vh;display:flex;flex-direction:column;background:var(--fondo);
color:var(--texto);font:16px/1.625 Geist,system-ui,-apple-system,'Segoe UI',Roboto,sans-serif}
.barra{height:3.75rem;display:flex;align-items:center;padding:0 1rem;background:var(--barra);
box-shadow:0 1px 0 var(--borde)}
.marca{display:flex;align-items:center;gap:.5rem;font-weight:600;letter-spacing:-.01em;font-size:1.125rem}
.marca svg{width:26px;height:26px}
main{flex:1;display:flex;align-items:center;justify-content:center;padding:3rem 1rem}
.tarjeta{width:100%;max-width:26rem;padding:2rem;background:var(--tarjeta);border:1px solid var(--borde);
border-radius:.75rem;box-shadow:0 10px 15px -3px var(--sombra)}
h1{margin:0 0 .5rem;font-size:1.5rem;font-weight:600;letter-spacing:-.022em;line-height:1.25}
.secundario,.ayuda{color:var(--secundario)}
.secundario{margin:0 0 1.5rem}
.ayuda{margin:1.5rem 0 0;font-size:.875rem}
label{display:block;margin:0 0 .375rem;font-size:.875rem;font-weight:500}
input{display:block;width:100%;height:2.75rem;margin:0 0 1rem;padding:0 .75rem;font:inherit;
color:var(--texto);background:var(--tarjeta);border:1px solid var(--campo);border-radius:.5rem}
input:focus-visible,button:focus-visible{outline:2px solid var(--primario);outline-offset:2px}
button{width:100%;height:2.75rem;margin-top:.5rem;border:0;border-radius:.5rem;cursor:pointer;
font:inherit;font-weight:600;color:var(--sobre-primario);background:var(--primario)}
button:hover{filter:brightness(1.12)}
.error{margin:0 0 1.25rem;padding:.75rem 1rem;font-size:.875rem;color:var(--error-texto);
background:var(--error-fondo);border:1px solid var(--error-borde);border-radius:.5rem}
footer{padding:1.5rem 1rem;text-align:center;font-size:.875rem;color:#f1f5f9;background:var(--pie);
border-top:1px solid #ffffff14}`;

const FAVICON = `data:image/svg+xml,${encodeURIComponent(LOGO)}`;

export function paginaAcceso({ usuario = '', destino = '/', error = '' } = {}, status = 200) {
  const html = `<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<meta name="color-scheme" content="light dark">
<title>Acceso · Guía de Codabench</title>
<link rel="icon" href="${FAVICON}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Geist:wght@300..900&display=swap">
<script>try{var t=localStorage.getItem('theme');if(t==='light'||t==='dark')document.documentElement.dataset.theme=t}catch(e){}</script>
<style>${ESTILOS}</style>
</head>
<body>
<header class="barra"><span class="marca">${LOGO}Codabench</span></header>
<main>
<form class="tarjeta" method="post" action="${RUTA_ACCESO}">
  <h1>Guía de Codabench</h1>
  <p class="secundario">Cómo crear y mantener competiciones en Codabench. Entra con el usuario y la contraseña de tu organización.</p>
  ${error ? `<p class="error" role="alert">${escapar(error)}</p>` : ''}
  <input type="hidden" name="destino" value="${escapar(destino)}">
  <label for="usuario">Usuario</label>
  <input id="usuario" name="usuario" type="text" autocomplete="username" autocapitalize="none" spellcheck="false" required value="${escapar(usuario)}"${usuario ? '' : ' autofocus'}>
  <label for="contrasena">Contraseña</label>
  <input id="contrasena" name="contrasena" type="password" autocomplete="current-password" required${usuario ? ' autofocus' : ''}>
  <button type="submit">Entrar</button>
  <p class="ayuda">¿No tienes acceso? Pídeselo a tu contacto en CAPTIA Technology.</p>
</form>
</main>
<footer>© ${new Date().getFullYear()} CAPTIA Technology</footer>
</body>
</html>
`;
  return new Response(html, {
    status,
    headers: {
      'Content-Type': 'text/html; charset=utf-8',
      'X-Frame-Options': 'DENY',
      'Referrer-Policy': 'same-origin',
      ...SIN_CACHE,
    },
  });
}

async function entrar(request, url, { accesos, secreto }) {
  let datos;
  try {
    datos = await request.formData();
  } catch {
    datos = new FormData();
  }
  const usuario = String(datos.get('usuario') ?? '').trim().toLowerCase();
  const contrasena = String(datos.get('contrasena') ?? '');
  const destino = destinoSeguro(String(datos.get('destino') ?? '/'));

  if (!secretoValido(secreto)) {
    const error = 'El acceso no está disponible ahora mismo. Avisa a tu contacto en CAPTIA Technology.';
    return paginaAcceso({ usuario, destino, error }, 503);
  }
  if (!credencialValida(usuario, contrasena, accesos)) {
    return paginaAcceso({ usuario, destino, error: 'Usuario o contraseña incorrectos.' }, 401);
  }
  const sesion = crearSesion(usuario, accesos, secreto);
  return redirigir(destino, { 'Set-Cookie': cookieSesion(sesion, DURACION_SESION, url) });
}

export default async function middleware(request) {
  const url = new URL(request.url);
  const config = configuracion();

  if (url.pathname === RUTA_SALIR) {
    return redirigir(RUTA_ACCESO, { 'Set-Cookie': cookieSesion('', 0, url) });
  }

  const enSesion =
    sesionValida(leerCookie(request, COOKIE), config.accesos, config.secreto) ||
    autorizado(request.headers.get('authorization'), config.accesos);

  if (url.pathname === RUTA_ACCESO) {
    if (request.method === 'POST') return entrar(request, url, config);
    const destino = destinoSeguro(url.searchParams.get('destino'));
    return enSesion ? redirigir(destino) : paginaAcceso({ destino });
  }

  if (enSesion) return next();

  if (esNavegacion(request)) {
    const destino = destinoSeguro(url.pathname + url.search);
    return redirigir(
      destino === '/' ? RUTA_ACCESO : `${RUTA_ACCESO}?destino=${encodeURIComponent(destino)}`,
    );
  }
  // Un chunk, una imagen o el índice del buscador pedidos sin sesión. Sin `WWW-Authenticate`
  // a propósito: con esa cabecera el navegador sacaría su diálogo nativo.
  return new Response('Acceso restringido\n', {
    status: 401,
    headers: { 'Content-Type': 'text/plain; charset=utf-8', ...SIN_CACHE },
  });
}
