# La guía pide credencial, pero el repositorio sigue siendo público

Decidido el 2026-10-28. Es el mismo control de acceso que se montó el día antes en el manual de
captia.ai (`my-qa-captia-ai-app`), traído aquí casi sin cambios. Este documento cuenta **qué
significa en un repositorio público, cómo se pone en marcha y cómo se opera**. Por qué un
formulario propio en un Routing Middleware de Vercel, y no la Password Protection de Vercel,
Vercel Authentication, Passport o un proxy delante, está contrastado en
`docs-meta/12-control-de-acceso.md` de aquel repositorio; las razones valen igual aquí.

```
navegador ──► codabench-docs.vercel.app ──► middleware.js ──┬── sesión válida ───────────►  la guía
                                                            └── sin ella ──► /acceso ──►  cookie de sesión
```

## Lo primero: cierra el sitio, no el contenido

**El repositorio sigue siendo público en GitHub**, por decisión expresa del 2026-10-28. Todo lo
que el sitio enseña está en `docs/` —el texto, las capturas, los diagramas— y se lee en
github.com sin credencial. La credencial evita que la guía se navegue como un sitio web abierto y
que la indexen los buscadores; **no protege nada de lo que hay en el repositorio**.

De ahí salen tres cosas:

- **Las reglas de contenido no cambian en absoluto.** Nada en el árbol que identifique a nadie,
  igual que antes; el hook y `scripts/check_docs.py` siguen exactamente igual. Lo que no se
  pondría en un sitio abierto tampoco va aquí.
- **Si algún día el contenido tiene que ser restringido de verdad**, el paso es hacer privado el
  repositorio: Vercel despliega igual desde un repositorio privado de la organización. Aun así,
  lo que ya estuvo publicado en GitHub hay que darlo por visto.
- **Que `middleware.js` sea público no es un problema.** La seguridad descansa en las contraseñas
  y en el secreto de sesión, que viven en las variables del proyecto en Vercel, no en que nadie
  sepa cómo está hecho.

## Cómo funciona

Igual que en el manual de captia.ai. Sin sesión, el middleware responde según lo que se pida:

| Petición | Respuesta |
|---|---|
| Una página (el navegador pide HTML) | 303 a `/acceso?destino=<la página>` |
| `/acceso` | El formulario, con el diseño de la guía: el mark, Geist, los colores de marca, modo claro u oscuro según lo elegido en la guía |
| `POST /acceso` con credencial válida | Cookie de sesión de 30 días y 303 de vuelta al destino |
| `POST /acceso` con credencial mala | El formulario otra vez, con el aviso «Usuario o contraseña incorrectos» |
| Un chunk, una imagen, el índice del buscador | 401, **sin** `WWW-Authenticate`, para que el navegador no saque su diálogo nativo |
| `/salir` | Borra la cookie y vuelve al formulario. Está enlazado en la barra de la guía |

Va **sin `matcher`**, a propósito: los chunks de JS llevan el texto de cada página y el JSON del
buscador lo lleva entero, así que excluir los estáticos dejaría la guía abierta detrás de una
portada cerrada.

**`DOCS_ACCESOS`** es la lista de quién entra: una entrada `usuario:sha256(usuario:contraseña)`
por cliente, separadas por comas. **Es la misma lista que la del manual de captia.ai.** El hash
no depende del sitio, así que el mismo valor vale en los dos proyectos y las mismas contraseñas
entran en ambos. Pero cada proyecto tiene su copia de la variable: dar de alta o de baja a
alguien en uno no lo cambia en el otro.

**`DOCS_SESION_SECRETO`** firma la cookie (HMAC-SHA256) y es **propio de este proyecto**, distinto
del de captia.ai. La firma incluye el hash de la credencial, así que quitar a alguien o rotar su
contraseña cierra también sus sesiones abiertas.

**Un fallo de configuración cierra el sitio, nunca lo abre.** Sin `DOCS_ACCESOS` válida no entra
nadie; sin secreto (o con menos de 32 caracteres), el formulario dice que el acceso no está
disponible. Las dos cosas dejan su línea en los logs de Vercel.

### Qué cambia respecto al original

`middleware.js`, `scripts/acceso.test.mjs` y `scripts/credencial_cliente.py` son los de
`my-qa-captia-ai-app` con tres diferencias: los textos de la página de acceso («Guía de
Codabench»), el nombre de la cookie (`codabench_docs_sesion`) y las referencias a este
documento. `scripts/check_dominio.py` apunta además a `codabench-docs.vercel.app` y a rutas de
esta guía. El tema no se tocó: `src/css/custom.css` y el mark son copia exacta del design system
en los dos repositorios, y los tokens que lleva en línea la página de acceso son los mismos.

**Si allí se corrige algo del middleware, aquí se corrige igual.** Un diff entre los dos
`middleware.js` solo debe enseñar esas tres diferencias.

Y alrededor:

- **`vercel.json`**: `middleware.js` entra en la lista del `ignoreCommand`, y la caché de
  `/assets` e `/img` pasa de `public` a `private`, para que ningún proxy intermedio sirva a otro
  lo que se pidió con sesión.
- **CI** corre `node --test scripts/acceso.test.mjs`. El build de Docusaurus no ejecuta el
  middleware: sin esas pruebas, un cambio que abriera la guía pasaría todo en verde.
- **`docusaurus.config.js`**: el enlace «Salir» en la barra.

## Puesta en marcha

El orden importa: **las variables tienen que existir antes de que el middleware llegue a
producción**, o la guía queda cerrada para todos.

1. **Vercel** → proyecto `codabench-docs` → *Settings* → *Environment Variables* → *Add
   Environment Variable*, las dos en **Production y Preview**:
   - `DOCS_ACCESOS`, de tipo **Config**: el mismo valor que tiene en el proyecto
     `my-qa-captia-ai-app`, copiado de su panel. Pegado **por comas**: el campo es de una sola
     línea y el navegador quita los saltos al pegar.
   - `DOCS_SESION_SECRETO`, de tipo **Secret**, uno nuevo: `python scripts/credencial_cliente.py
     --secreto`. Vercel guarda un *Secret* por entorno, así que sale en dos filas.

   Para comprobar lo guardado, se copia el valor de `DOCS_ACCESOS` del panel y en PowerShell:
   `$env:DOCS_ACCESOS = Get-Clipboard -Raw; python scripts/credencial_cliente.py --check`.
2. **Redesplegar la preview** del pull request, para que reciba las variables: *Deployments* → el
   último despliegue *Ready* de la rama → *Redeploy*.
3. **Probar la preview** en el navegador. Si el proyecto protege las previews con Vercel
   Authentication, primero pide ese login. Después tiene que salir el formulario de la guía: la
   credencial entra, una mala muestra el aviso y «Salir» devuelve al formulario. **Si la preview
   sirve la guía sin pasar por el formulario, Vercel no ejecuta el middleware: no se fusiona.**
4. **Fusionar en `master`**, que es la rama de la que salen los despliegues de producción de este
   proyecto. El `ignoreCommand` solo mira el último commit: si no toca ninguna ruta vigilada,
   Vercel no construye. Comprobar en *Deployments* que el despliegue de producción no sale
   *Canceled*.
5. **Verificar producción**: `DOCS_CREDENCIAL=equipo:… python scripts/check_dominio.py`.

## Operación

Las variables solo llegan a los despliegues **nuevos**: cualquier cambio exige **redesplegar
producción** (*Deployments* → el último de producción → *Redeploy*). No hace falta commit.

| Qué | Cómo |
|---|---|
| Dar de alta a alguien | `python scripts/credencial_cliente.py <usuario>`, añadir su entrada a `DOCS_ACCESOS` tras una coma, redesplegar. Si tiene que entrar también al manual de captia.ai, lo mismo en aquel proyecto |
| Quitarle el acceso | Borrar su entrada y redesplegar, **en los dos proyectos** si estaba en ambos |
| Rotar su contraseña | Generar otra con el mismo usuario, sustituir su entrada, redesplegar. En los dos proyectos, o la vieja seguirá valiendo en el otro |
| Cerrar la sesión de todos | `python scripts/credencial_cliente.py --secreto`, sustituir `DOCS_SESION_SECRETO` en la fila de Production, redesplegar. Solo afecta a este proyecto |

## Límites conocidos

- **El contenido está en GitHub sin credencial.** Ver arriba: es la limitación que más pesa.
- **Una credencial vale en las dos guías.** Quien tenga una para el manual de captia.ai entra
  aquí, y al revés, mientras las listas sean iguales. Si algún día una de las dos necesita un
  público distinto, basta con que sus `DOCS_ACCESOS` dejen de coincidir.
- **La credencial es del cliente, no de la persona**, y no queda registro de quién entró.
- **La sesión dura 30 días.** Si caduca con la guía abierta, la navegación interna puede fallar
  hasta que se recarga la página, que lleva al formulario.
- **Revocar tarda lo que tarda un despliegue**: minutos, no segundos.
- **El middleware corre en cada petición**, también en cada imagen y cada chunk, y Vercel lo cobra
  como cómputo. Con el tráfico de una guía es marginal.

## Rollback

| Qué falló | Cómo se deshace |
|---|---|
| Nadie puede entrar | `DOCS_ACCESOS` vacía, mal formada o ausente en ese entorno. Validarla con `--check`, corregirla y redesplegar |
| El formulario dice que el acceso no está disponible | Falta `DOCS_SESION_SECRETO` o es demasiado corto. Generarlo con `--secreto` y redesplegar |
| El despliegue con el middleware falla | *Instant Rollback* en Vercel. **Ojo: cualquier despliegue anterior a este cambio sirve la guía abierta** |
| Se decide volver a abrir el sitio | Borrar `middleware.js`, su entrada del `ignoreCommand` y el enlace «Salir» de `docusaurus.config.js`, y desplegar |

## Problemas frecuentes

**No entra nadie, aunque `--check` sobre la lista pasa.** La lista se pegó en el panel con saltos
de línea, que el navegador quita: las entradas quedan unidas en una sola. Copiar el valor del
panel, pasarle `--check` y volver a pegarla unida por comas.

**He quitado a alguien y sigue entrando.** Falta redesplegar. O se quitó en un proyecto y no en el
otro.

**En local, con `npm start`, no pide nada y «Salir» da 404.** Es lo esperado: el servidor de
desarrollo de Docusaurus no ejecuta `middleware.js`; eso solo lo hace Vercel.

**`check_dominio.py` dice `LA GUIA ESTA ABIERTA`.** Es el fallo más grave posible. O el despliegue
publicado es anterior al middleware —un *Instant Rollback* lo provoca—, o Vercel no lo está
ejecutando.

**`check_dominio.py` da 401 en todas las páginas.** El sitio rechaza `DOCS_CREDENCIAL`: suele ser
un valor mal copiado. `$env:DOCS_CREDENCIAL.Length` tiene que dar la longitud del usuario más 30.
