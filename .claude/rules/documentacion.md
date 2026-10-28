---
paths:
  - "docs/**/*.md"
  - "docs/**/*.mdx"
---

# Reglas de los documentos de `docs/`

Se cargan solo al tocar un documento.

Este repositorio se estrena con esta guía, así que lo que sigue no cuenta lo que pasó —no hay
historial del que sacarlo— sino **por qué mecanismo falla cada cosa si se incumple**. Ese
mecanismo sí está comprobado contra la configuración real del sitio: `onBrokenLinks: 'throw'`,
`onBrokenMarkdownLinks: 'throw'`, `routeBasePath: '/'` y una navegación **declarada** en
`scripts/build_nav.py`, no deducida del sistema de ficheros.

## La plantilla de página

Las 23 páginas comparten una estructura. Al crear o editar una, mantenerla:

```markdown
---
title: "Título sin emoji"        # dice lo MISMO que el H1
sidebar_position: <n>            # NO se escribe a mano: lo pone scripts/build_nav.py
sidebar_label: "Nombre corto"    # opcional, también de build_nav.py
description: "…"                 # la genera build_nav.py del «Objetivo» (ver abajo)
---

# Título

**Objetivo:** una frase que diga qué consigue el lector en esta página.

## <secciones en H2>
```

- **`**Objetivo:**` en negrita, primera línea del cuerpo**, exactamente ese rótulo. De ahí sale la
  `description` del front matter —la primera frase—, igual que en el manual de captia.ai sale de
  «**Objetivo Principal:**».
- **Pasos numerados** para lo que es un procedimiento y **tablas** para inventarios y errores. Esta
  guía es procedimental de principio a fin: casi todo lo que cuenta es «haz esto, después esto».
  Un procedimiento escrito en prosa corrida obliga al lector a reconstruir el orden mientras tiene
  la interfaz delante.
- Los admonitions de Docusaurus (`:::note`, `:::tip`, `:::warning`, `:::info`) para lo que el
  documento original marcaba con `>`. Una cita `>` se renderiza como cita, no como aviso: el
  lector no distingue una advertencia de un inciso, y la advertencia es justo lo que no puede
  saltarse.

`sidebar_position`, `sidebar_label` y `description` las escribe `scripts/build_nav.py`. Escribirlas
a mano no sirve de nada: el siguiente `--apply` las regenera desde `SECCIONES` y desde el
«Objetivo», y mientras tanto el árbol declarado y el fichero dicen cosas distintas.

El rótulo va **en minúscula tras los dos puntos** —«**Objetivo:** subir a Codabench los datos…»—
para que se lea como una sola frase. La `description` del front matter sí sale capitalizada, y de
eso se encarga `build_nav.py`; no hay que capitalizarla en el cuerpo.

### El pie que continúa el recorrido

Cada página de detalle cierra con una línea que lleva a la siguiente, y **esa línea tiene que
coincidir con el orden real del sidebar**:

```markdown
**Siguiente paso:** [Tasks](./tasks.md) — combinar estos recursos en la unidad que evalúa las
submissions.
```

No es decorativo y no es redundante con la paginación automática de Docusaurus: el prev/next del
tema dice *cómo se llama* la página siguiente, y este pie dice *por qué* se va allí. Pero por eso
mismo, cuando los dos discrepan el lector ve dos «siguientes» distintos al pie de la misma página
y deja de fiarse de ambos. El caso que hay que vigilar es la página que precede a una opcional:
si el sidebar coloca detrás una pestaña que el recorrido considera prescindible, el pie escrito a
mano tiende a saltársela y a apuntar a la siguiente «de verdad» — y ahí es donde los dos
«siguientes» dejan de coincidir. Ante la duda, manda el sidebar: es lo que el lector tiene
delante.

Dos excepciones, y son las únicas:

- **Las páginas índice** (`index.md` de cada sección) no lo llevan: su cuerpo entero ya es la lista
  ordenada de por dónde seguir.
- **Las páginas de referencia** (`referencia/troubleshooting.md` y `referencia/fuentes.md`) tampoco:
  no son pasos de un recorrido sino material de consulta, y no hay ningún «después» al que mandar
  al lector.

Y una precisión sobre el destino, no solo sobre la forma: el pie de una página de diagnóstico
apunta a donde está la respuesta, no al siguiente ítem del sidebar. Detrás de
`submissions/probar.md` el sidebar pone la sección `referencia/` entera, pero mandar allí al
lector que acaba de ver fallar una submission le obliga a un salto de más.

`submissions/probar.md`, que es la última del recorrido, cierra con **`Si algo no cuadra:`** en vez
de «Siguiente paso»: lo que viene después de probar no es otro paso, es un diagnóstico.

## Los rótulos de la interfaz van en negrita y en inglés

La interfaz de Codabench está en inglés y el lector la tiene delante mientras lee. Los nombres de
pantallas, pestañas, botones y campos se escriben **en negrita y sin traducir**:

- **Benchmarks → Management**, con flecha para las rutas de navegación.
- **Add Dataset/Program**, **Force Best**, **Submission rule**.

Traducir un rótulo obliga al lector a hacer la traducción inversa contra una pantalla que solo
existe en inglés, y además lo saca del buscador: ni el `Ctrl+F` sobre la interfaz ni el buscador
de este sitio encuentran «Forzar el mejor». La negrita es lo que separa el rótulo de la prosa que
lo rodea; sin ella, «pulsa en add dataset» se lee como una instrucción vaga y no como el nombre
exacto de un botón.

La versión contrastada es **Codabench v1.31.2**, y se apoya en las notas de publicación y en el
código de esa versión —los formularios del editor y los modelos—, **no** en haber montado una
competición sobre una instancia con ella. Donde una página afirme la versión, tiene que decir de
dónde sale: una versión afirmada a secas se lee como verificada de punta a punta, y aquí no lo
está. El procedimiento de revisión, en `docs-meta/04-sync-codabench-v1.31.2.md`.

## Las once invariantes

Son la fuente única del harness. Las mismas que comprueba el hook `.claude/hooks/validar_doc.py`
sobre el fichero recién escrito y las mismas que comprueba `scripts/check_docs.py` sobre el árbol
entero: si cambia una, cambian las tres. Las diez primeras son **bloqueantes**; la undécima es un
**aviso**.

**1. Front matter obligatorio, con al menos `title`.** Sin bloque de front matter,
`build_nav.py` no tiene dónde escribir `sidebar_position`, `sidebar_label` ni `description`: la
página se queda fuera del orden declarado y cae al final de su sección. Y sin `title`, lo que se
ve en la pestaña del navegador, en las migas y en los resultados del buscador lo deduce Docusaurus
del H1 o del nombre del fichero, que es justo lo que la invariante 3 impide que diverja.

**2. Un solo H1 por documento.** El índice lateral derecho de Docusaurus arranca en H2: una
sección escrita con `#` no aparece en él, así que el lector que navega por el índice no llega
nunca a esa parte de la página. Además, dos H1 dejan el documento con dos títulos de nivel de
página para los buscadores. Lo arregla `python scripts/normalize_headings.py --apply`.

**3. El `title` del front matter dice lo mismo que el H1, y sin emoji.** El `title` es lo que se
ve fuera de la página —pestaña, migas, resultado del buscador, vista previa de un enlace
compartido— y el H1 es lo que se lee dentro. Cuando se separan, el lector llega buscando una cosa
y lee otra. El riesgo aquí es concreto y se repite: estas páginas nacen de repartir un único
documento, y una página creada copiando a su vecina hereda el `title` de la vecina. El emoji va
aparte: el `title` acaba en la pestaña y en los metadatos, donde un emoji no aporta nada y ensucia
el resultado del buscador.

**4. Imágenes en sintaxis Markdown, nunca `<img>`, nunca remotas, co-ubicadas.** Docusaurus solo
pasa por `require()` —y por tanto por el bundler, que comprueba que el fichero existe y le pone
hash— las rutas de `![alt](./fichero.png)`. Un `<img src="./x.png">` compila sin protestar y en
producción apunta a una ruta que no existe: imagen rota, y el build en verde. Las remotas añaden
a un sitio público una dependencia de un tercero, y las de `github.com/user-attachments` son
además efímeras y exigen autenticación: se ven mientras las mira quien las subió y no después.
Co-ubicada junto al `.md` significa que mover el documento se lleva su imagen con él.

**5. Todo enlace relativo a un `.md` resuelve, con la caja exacta del fichero.** Este es el fallo
que más caro sale porque **no se reproduce donde se escribió**: en Windows el sistema de ficheros
es insensible a mayúsculas, así que `../Submissions/formato.md` abre perfectamente en el
`npm start` del autor. El CI y el build de Vercel corren en Linux, donde sí se distingue, y con
`onBrokenLinks: 'throw'` eso no es un enlace roto: es un despliegue que no sale. Los enlaces se
escriben con la extensión `.md` y con la caja exacta del nombre del fichero.

**6. Filas de tabla cuadradas, y `\|` para el `|` que va dentro de código.** Una fila con celdas
de más no rompe el build: GFM la renderiza igual y recorta el sobrante **en silencio**, así que el
contenido desaparece del sitio publicado sin que nada avise. Y la regla que menos se espera es que
un `|` dentro de `` `código` `` también separa celdas: escribir `` `Force Best | Force Last` `` en
una tabla parte la fila en dos columnas de más y se come el final. Dentro de una tabla, siempre
`\|`.

**7. Rutas ASCII y en minúscula.** Un fichero con tilde genera una URL percent-encoded
(`/evaluaci%C3%B3n`), que se pega mal en un chat, se lee peor en un correo y se rompe al copiarla
a mano. Las mayúsculas reabren el problema de la invariante 5, esta vez en el propio nombre. Aquí
se prohíbe de entrada, en vez de exigir un `slug:` transliterado como hace el manual de captia.ai:
aquel arrastra rutas heredadas de antes de la regla y este árbol se estrena hoy, así que sale más
barato no crear el problema que documentarlo página por página.

**8. Nada publicable que identifique a nadie.** **El repositorio es público**: el sitio pide
credencial, pero `docs/` se lee en GitHub sin ella, así que no hay ninguna zona de borrador donde pegar algo «de momento»: lo que se escribe,
se publica. Es fácil de olvidar cuando se copia un ejemplo tomado de una competición real. Fuera,
por tanto: correos con dominio real (los ejemplos usan `@ejemplo.com` o
`@example.com`), direcciones IP, credenciales y tokens (`api_key`, `token:`, `Bearer …`, cadenas
hex o base64 largas), URLs de instancias internas de Codabench y cualquier identificador de
`scripts/privados.txt` si el equipo mantiene esa lista (no versionada; ver `.gitignore`). Un token
pegado en un ejemplo de submission se publica igual que el resto del texto, y sigue en el
histórico de git aunque después se borre de la página.

**9. Ninguna imagen huérfana en `docs/`.** Una imagen que ya no cita ningún documento no llega a
publicarse —Docusaurus solo emite las que algún `.md` requiere— pero se queda en el repositorio
sin que ningún build vuelva a mirarla, y sobre todo delata una edición a medias: alguien quitó la
sección y dejó la captura, o la renombró y no actualizó el enlace. Si la imagen ya no hace falta,
se borra con la sección.

**10. Todo documento declarado en `SECCIONES` de `build_nav.py`; en la raíz de `docs/`, solo
`index.mdx` y `mapa-de-la-guia.md`.** La navegación de este sitio es declarada. Un documento que
existe pero no está declarado no recibe `sidebar_position`, no entra en el mapa ni en
`docs-map.json` y se publica **inalcanzable**: no está en el menú lateral, no está en el mapa y
solo aparece si alguien acierta a buscarlo. Al revés también falla: declarado y no escrito, y
`build_nav.py --check` se cae. La raíz solo admite la portada y el mapa porque toda página de
contenido pertenece a una de las seis secciones; una suelta en la raíz no tendría padre en el
recorrido.

**11. El rótulo `**Objetivo:**` en toda página que no sea la portada ni el mapa.** *(Aviso, no
bloqueante.)* De ahí saca `build_nav.py` la `description`, que es lo que se lee en la tarjeta del
buscador y en la vista previa de un enlace compartido: sin él, la página no tiene resumen y el
generador no tiene de dónde sacarlo. No bloquea porque una página sin «Objetivo» se publica
perfectamente: es calidad editorial, no algo que rompa el sitio.

## Rutas y nombres

Todo en minúscula ASCII bajo `docs/`: sin tildes, sin mayúsculas, sin guiones bajos. El guion
medio separa palabras (`mapa-de-la-guia.md`, `datasets-programs.md`), porque es lo que Docusaurus
lleva tal cual a la URL y lo que un buscador entiende como separador. La regla vale para carpetas
y para ficheros, y el motivo está en las invariantes 5 y 7: una URL percent-encoded no se puede
compartir a mano, y una mayúscula solo se nota cuando el build ya está corriendo en Linux.

`index.md` es el índice de su carpeta y Docusaurus lo sirve **en la ruta de la carpeta**:
`docs/empezar/index.md` se publica en `/empezar`. Docusaurus admite también `carpeta/carpeta.md`
para lo mismo; aquí no se usa, para que haya una sola forma y la invariante 10 pueda enunciarse en
una línea.

De ahí sale una trampa que conviene tener presente al enlazar: **la URL parece de un nivel menos
que el fichero**. El índice se publica en `/empezar` pero vive dentro de `docs/empezar/`, así que
sus enlaces relativos se resuelven desde esa carpeta: a una hermana, `./conceptos.md`; a otra
sección, `../recursos/tasks.md`. Escribir `empezar/conceptos.md` desde el índice —copiando la
forma de la URL— apunta a `docs/empezar/empezar/conceptos.md` y tira el build.

## Añadir una página

Crear el fichero no basta: hay que **declararlo a mano en `SECCIONES`**, en
`scripts/build_nav.py`. No es burocracia. Colocar una página en el recorrido es una decisión —en
qué sección entra y en qué orden dentro de ella— y no se puede deducir del nombre del fichero: por
orden alfabético, «leaderboards» iría antes que «phases» cuando el lector necesita entender las
fases primero, y «formato» antes que «probar» solo por casualidad.

Después, `python scripts/build_nav.py --apply` propaga esa decisión: front matter,
`_category_.json` de cada sección, `docs/mapa-de-la-guia.md` y `docs-map.json`. Ninguno de esos
cuatro se edita a mano; si hace falta cambiar algo en ellos, se cambia en `SECCIONES` y se vuelve
a aplicar.

## Antes de dar por buena una edición

```
python scripts/check_docs.py
```

Sale con código 1 si algo falla y dice exactamente qué. Es la misma comprobación que corre en CI
(`.github/workflows/docs-ci.yml`), así que si pasa aquí, pasa allí.

El hook de escritura no la sustituye: mira solo el fichero que acabas de tocar y solo lo que se
puede decidir sin leer los demás. Los enlaces, las imágenes huérfanas y el árbol declarado se
resuelven contra todo el repositorio, y eso únicamente lo ve `check_docs.py`.

Si has añadido, quitado o movido una página, además:

```
python scripts/build_nav.py --check
```
