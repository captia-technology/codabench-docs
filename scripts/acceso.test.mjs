/**
 * Pruebas del control de acceso (`middleware.js`).
 *
 *     node --test scripts/acceso.test.mjs
 *
 * Corren en CI. El build de Docusaurus no ejecuta el middleware, así que sin esto un cambio que
 * dejase pasar peticiones sin credencial llegaría a producción con todo en verde.
 */
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import middleware, {
  COOKIE,
  autorizado,
  crearSesion,
  destinoSeguro,
  leerAccesos,
  sesionValida,
} from '../middleware.js';

// Entrada generada con `scripts/credencial_cliente.py`. Si Python y el middleware dejan de
// calcular el mismo hash, los clientes dados de alta no podrían entrar: lo dice esta constante.
const USUARIO = 'cliente-ejemplo';
const CONTRASENA = 'abcde-fghjk-mnpqr-stuvw-xyz23';
const ENTRADA_PYTHON =
  'cliente-ejemplo:aded9a8c2ac02b7d84367dbf54fff0b7cb8c1a9736caea9a7b2ba95d9e733b69';
const SECRETO = 'secreto-de-pruebas-con-mas-de-32-caracteres';
const SITIO = 'https://docs.codabench.captia.ai';

const basic = (credencial) => `Basic ${Buffer.from(credencial).toString('base64')}`;
const entrada = (usuario, contrasena) =>
  `${usuario}:${createHash('sha256').update(`${usuario}:${contrasena}`).digest('hex')}`;

/**
 * Fija las dos variables para una prueba y las restaura al acabar. `undefined` explícito significa
 * «variable ausente», por eso no se usan valores por defecto en la desestructuración: convertirían
 * ese `undefined` en el valor válido y la prueba de la variable ausente no probaría nada.
 */
function configurar(t, opciones = {}) {
  const accesos = 'accesos' in opciones ? opciones.accesos : ENTRADA_PYTHON;
  const secreto = 'secreto' in opciones ? opciones.secreto : SECRETO;
  const antes = { a: process.env.DOCS_ACCESOS, s: process.env.DOCS_SESION_SECRETO };
  const poner = (nombre, valor) =>
    valor === undefined ? delete process.env[nombre] : (process.env[nombre] = valor);
  poner('DOCS_ACCESOS', accesos);
  poner('DOCS_SESION_SECRETO', secreto);
  t.after(() => {
    poner('DOCS_ACCESOS', antes.a);
    poner('DOCS_SESION_SECRETO', antes.s);
  });
  t.mock.method(console, 'error', () => {}); // los avisos de configuración son esperados aquí
}

/** Lo que pide un navegador al escribir una URL o seguir un enlace. */
const navegar = (ruta, cabeceras = {}) =>
  middleware(new Request(SITIO + ruta, { headers: { accept: 'text/html', ...cabeceras } }));
/** Lo que pide la página por debajo: chunks, imágenes, el índice del buscador. */
const pedir = (ruta, cabeceras = {}) => middleware(new Request(SITIO + ruta, { headers: cabeceras }));
const enviar = (campos) =>
  middleware(
    new Request(`${SITIO}/acceso`, { method: 'POST', body: new URLSearchParams(campos) }),
  );

const pasa = (res) => res.headers.get('x-middleware-next') === '1';
const cookieDe = (res) => (res.headers.get('set-cookie') ?? '').split(';')[0];
const conCookie = (valor) => ({ cookie: `otra=1; ${COOKIE}=${valor}` });

test('Python y el middleware calculan el mismo hash', () => {
  assert.equal(entrada(USUARIO, CONTRASENA), ENTRADA_PYTHON);
});

test('sin sesión, una página lleva a /acceso recordando adónde iba', async (t) => {
  configurar(t);
  const res = await navegar('/Alarmas?pestana=2');
  assert.equal(res.status, 303);
  assert.equal(res.headers.get('location'), '/acceso?destino=%2FAlarmas%3Fpestana%3D2');
  assert.equal((await navegar('/')).headers.get('location'), '/acceso');
});

test('sin sesión, los estáticos dan 401 y sin desafío Basic (nada de diálogo nativo)', async (t) => {
  configurar(t);
  for (const ruta of ['/assets/js/main.js', '/img/logo-mark.svg', '/search-index.json', '/sitemap.xml']) {
    const res = await pedir(ruta);
    assert.equal(res.status, 401, ruta);
    assert.equal(res.headers.get('www-authenticate'), null, ruta);
  }
});

test('/acceso sirve el formulario, sin caché ni indexación', async (t) => {
  configurar(t);
  const res = await navegar('/acceso?destino=%2FAlarmas');
  assert.equal(res.status, 200);
  const html = await res.text();
  assert.match(html, /<form[^>]+method="post"[^>]+action="\/acceso"/);
  assert.match(html, /name="contrasena" type="password"/);
  assert.match(html, /name="destino" value="\/Alarmas"/);
  assert.equal(res.headers.get('cache-control'), 'no-store');
  assert.equal(res.headers.get('x-robots-tag'), 'noindex, nofollow');
  assert.equal(res.headers.get('x-frame-options'), 'DENY');
});

test('entrar: cookie de sesión y de vuelta al destino; con ella pasa todo', async (t) => {
  configurar(t);
  const res = await enviar({ usuario: USUARIO, contrasena: CONTRASENA, destino: '/Alarmas' });
  assert.equal(res.status, 303);
  assert.equal(res.headers.get('location'), '/Alarmas');
  const setCookie = res.headers.get('set-cookie');
  for (const atributo of ['HttpOnly', 'SameSite=Lax', 'Secure', 'Path=/', 'Max-Age=2592000']) {
    assert.ok(setCookie.includes(atributo), atributo);
  }
  const cookie = { cookie: cookieDe(res) };
  assert.ok(pasa(await navegar('/Alarmas', cookie)));
  assert.ok(pasa(await pedir('/search-index.json', cookie)));
});

test('el usuario no distingue mayúsculas; la contraseña sí', async (t) => {
  configurar(t);
  assert.equal((await enviar({ usuario: ' Cliente-Ejemplo ', contrasena: CONTRASENA })).status, 303);
  const res = await enviar({ usuario: USUARIO, contrasena: CONTRASENA.toUpperCase() });
  assert.equal(res.status, 401);
});

test('credencial equivocada: el formulario otra vez, con aviso y sin cookie', async (t) => {
  configurar(t);
  for (const campos of [
    { usuario: USUARIO, contrasena: 'otra' },
    { usuario: 'otro-cliente', contrasena: CONTRASENA },
    {},
  ]) {
    const res = await enviar(campos);
    assert.equal(res.status, 401);
    assert.equal(res.headers.get('set-cookie'), null);
    assert.match(await res.text(), /role="alert">Usuario o contraseña incorrectos/);
  }
});

test('lo que se devuelve al formulario va escapado', async (t) => {
  configurar(t);
  const html = await (await enviar({ usuario: '"><script>x()</script>', contrasena: 'x' })).text();
  assert.ok(!html.includes('<script>x()'));
  assert.ok(html.includes('&quot;&gt;&lt;script&gt;'));
});

test('el destino solo puede ser una ruta del propio sitio', () => {
  for (const malo of ['//otro.com', '/\\otro.com', '/\t/otro.com', 'https://otro.com', 'otro', '/acceso', null]) {
    assert.equal(destinoSeguro(malo), '/', String(malo));
  }
  for (const bueno of ['/', '/Alarmas', '/Widgets/Configuracion/Graficos/Area?x=1']) {
    assert.equal(destinoSeguro(bueno), bueno);
  }
});

test('una sesión deja de valer al caducar, al dar de baja, al rotar o al cambiar el secreto', () => {
  const { accesos } = leerAccesos(ENTRADA_PYTHON);
  const ahora = Date.now();
  const sesion = crearSesion(USUARIO, accesos, SECRETO, ahora);
  assert.ok(sesionValida(sesion, accesos, SECRETO, ahora));

  const treintaYUnDias = ahora + 31 * 24 * 3600 * 1000;
  assert.ok(!sesionValida(sesion, accesos, SECRETO, treintaYUnDias), 'caducada');
  assert.ok(!sesionValida(sesion, new Map(), SECRETO, ahora), 'dado de baja');
  const rotada = leerAccesos(entrada(USUARIO, 'contrasena-nueva')).accesos;
  assert.ok(!sesionValida(sesion, rotada, SECRETO, ahora), 'contraseña rotada');
  assert.ok(!sesionValida(sesion, accesos, `${SECRETO}-nuevo`, ahora), 'secreto rotado');

  const [u, expira, firma] = [sesion.slice(0, sesion.indexOf('.')), ...sesion.split('.').slice(-2)];
  assert.ok(!sesionValida(`${u}.${Number(expira) + 999999}.${firma}`, accesos, SECRETO, ahora), 'expira manipulada');
  assert.ok(!sesionValida(`equipo.${expira}.${firma}`, accesos, SECRETO, ahora), 'otro usuario');
  assert.ok(!sesionValida(`${sesion}x`, accesos, SECRETO, ahora), 'firma manipulada');
  for (const basura of ['', 'a', 'a.b', '..', `${u}.NaN.${firma}`]) {
    assert.ok(!sesionValida(basura, accesos, SECRETO, ahora), basura);
  }
});

test('una cookie manipulada manda al formulario', async (t) => {
  configurar(t);
  const res = await navegar('/Alarmas', conCookie(`${USUARIO}.99999999999.firma-inventada`));
  assert.equal(res.status, 303);
  assert.match(res.headers.get('location'), /^\/acceso/);
});

test('/salir borra la cookie y vuelve al formulario', async (t) => {
  configurar(t);
  const res = await navegar('/salir');
  assert.equal(res.status, 303);
  assert.equal(res.headers.get('location'), '/acceso');
  assert.match(res.headers.get('set-cookie'), new RegExp(`^${COOKIE}=; .*Max-Age=0`));
});

test('/acceso con sesión abierta lleva directamente al destino', async (t) => {
  configurar(t);
  const sesion = cookieDe(await enviar({ usuario: USUARIO, contrasena: CONTRASENA }));
  const res = await navegar('/acceso?destino=%2FCopiloto', { cookie: sesion });
  assert.equal(res.headers.get('location'), '/Copiloto');
});

test('sin DOCS_SESION_SECRETO el formulario no abre sesiones', async (t) => {
  for (const secreto of [undefined, '', 'corto']) {
    configurar(t, { secreto });
    const res = await enviar({ usuario: USUARIO, contrasena: CONTRASENA });
    assert.equal(res.status, 503, String(secreto));
    assert.equal(res.headers.get('set-cookie'), null);
  }
});

test('sin DOCS_ACCESOS, vacía o toda mal formada: no entra nadie', async (t) => {
  for (const accesos of [undefined, '', '   ', 'cliente-ejemplo:no-es-un-hash']) {
    configurar(t, { accesos });
    assert.equal((await enviar({ usuario: USUARIO, contrasena: CONTRASENA })).status, 401);
    assert.equal((await pedir('/', { authorization: basic(`${USUARIO}:${CONTRASENA}`) })).status, 401);
  }
});

test('la autenticación básica sigue sirviendo a los automatismos', async (t) => {
  configurar(t);
  assert.ok(pasa(await pedir('/Alarmas', { authorization: basic(`${USUARIO}:${CONTRASENA}`) })));
  assert.equal((await pedir('/', { authorization: basic(`${USUARIO}:otra`) })).status, 401);
});

test('un POST fuera de /acceso sin sesión no pasa', async (t) => {
  configurar(t);
  const res = await middleware(new Request(`${SITIO}/Alarmas`, { method: 'POST', body: 'x' }));
  assert.equal(res.status, 401);
});

test('una entrada mal formada no deja fuera a las demás', () => {
  const valor = `roto:1234\n${ENTRADA_PYTHON}, ${entrada('equipo', 'x')}`;
  const { accesos, ignoradas } = leerAccesos(valor);
  assert.deepEqual([...accesos.keys()], ['cliente-ejemplo', 'equipo']);
  assert.deepEqual(ignoradas, ['roto']);
});

test('una contraseña pegada por error no llega a los logs', () => {
  // La línea que imprime el alta, y la credencial en vez de su hash.
  const { accesos, ignoradas } = leerAccesos(`contraseña  ${CONTRASENA}\n${USUARIO}:${CONTRASENA}`);
  assert.equal(accesos.size, 0);
  assert.deepEqual(ignoradas, ['(sin usuario)', '(sin usuario)', USUARIO]);
});

test('la contraseña puede contener dos puntos', () => {
  const { accesos } = leerAccesos(entrada('equipo', 'a:b:c'));
  assert.ok(autorizado(basic('equipo:a:b:c'), accesos));
  assert.ok(!autorizado(basic('equipo:a:b'), accesos));
});

test('cabeceras malformadas se rechazan sin excepción', () => {
  const { accesos } = leerAccesos(ENTRADA_PYTHON);
  for (const cabecera of [
    null,
    '',
    'Basic',
    'Basic !!!',
    `Bearer ${Buffer.from(`${USUARIO}:${CONTRASENA}`).toString('base64')}`,
    basic('sin-dos-puntos'),
    basic(`:${CONTRASENA}`),
  ]) {
    assert.equal(autorizado(cabecera, accesos), false, String(cabecera));
  }
});
