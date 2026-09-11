# Fuente externa, línea base y versiones

## Separar las identidades

En un manual de producto propio hay dos repositorios: el del código y el de la
documentación, y se comparan por commit. **Aquí no.** La fuente que documenta
este repositorio es Codabench, una plataforma externa de la que no hay
checkout, y el vecino privado `captia-technology/codabench-dataset-pipeline`
prepara ficheros que la guía asume ya listos. Ninguno de los dos es un
repositorio de código que se pueda diferenciar con Git.

| Fuente | Qué es | Qué se puede comparar |
| --- | --- | --- |
| Codabench | Plataforma externa; su código es open-source pero aquí no se clona ni se audita | Su documentación oficial por URL y versión, y su interfaz por observación fechada |
| `codabench-dataset-pipeline` | Repositorio privado de la organización, acceso restringido | Nada desde aquí: no se enlaza como si el lector tuviera acceso |
| `codabench-docs` | Este repositorio documental | Su propio historial Git |

Registrar por cada fuente: identificador, qué la respalda y con qué fecha o
versión se contrastó. Registrar también el estado local de este repositorio.
No comparar tags de este repositorio como si fueran versiones de Codabench:
son cosas distintas y confundirlas produce afirmaciones falsas en un sitio
público.

## La versión contrastada, y por qué es frágil

El sitio se rotula `Codabench v1.23`. Esa etiqueta sale de las URLs de la
documentación oficial que cita la guía —las que llevan `/v1.23/` en la ruta—,
**no** de una comprobación contra una instancia desplegada. Es una afirmación
más débil de lo que parece y hay que decirlo así donde se afirme.

Si Codabench publica una versión que cambia un rótulo, ni el build, ni
`check_docs.py`, ni el CI lo detectan: el sitio seguirá diciendo
`Codabench v1.23` y seguirá compilando. Lo único que avisa es
`python scripts/check_codabench.py`, que compara esa etiqueta con la última
release publicada del producto y dice qué páginas dependen de qué fuentes; hay
que lanzarlo a mano, porque necesita red y por eso no está en el CI. Ese aviso
no sustituye la revisión: el script **no** mira el contenido, así que releer las
páginas contra la fuente sigue siendo obligatorio, y su `--fijar` —el cierre
mecánico que sube la etiqueta— va después de haberlas releído, nunca antes.
Subirla sin revisar convierte una afirmación caducada en una falsa, que es peor.
Si ya no se sostiene, se retira.

## Conservación inicial

En `bootstrap`, inventariar documentos actuales, recursos, navegación y
archivos fuera de `docs/`. Elegir un destino fuera del contenido publicado.
El helper puede preservar el directorio elegido con bytes y hashes:

```bash
python .claude/skills/code-documentation/scripts/docs_tools.py baseline \
  --root . --docs docs --output .docs-baselines/legacy-inicial.zip
```

Sustituir rutas tras verificarlas. El ZIP contiene `BASELINE-MANIFEST.json` y
`content/` con los archivos originales incluidos. La operación rechaza un
destino existente, no sigue enlaces simbólicos y excluye nombres sensibles y
carpetas generadas. Inspeccionar el manifiesto: si hay exclusiones, no afirmar
que se conservó absolutamente todo. No editar el original hasta cubrir el
alcance histórico acordado; archivos fuera de `--docs` requieren otra copia.
No incluir secretos para obtener artificialmente una copia «completa».

Usar una etiqueta como `legacy-inicial` para expresar procedencia documental,
no una versión ficticia de la plataforma. Registrar que su contenido está sin
contrastar. Un commit Git autorizado puede versionar el archivo, pero crear el
ZIP **no** crea un commit, tag ni versión de Docusaurus.

Si se autoriza conservar un snapshot de Docusaurus, ejecutar el comando de
versionado correspondiente a esta instalación: `package.json` declara el script
`"docs:version": "docusaurus docs:version"`, de modo que
`npm run docs:version -- <etiqueta>` crea el snapshot del plugin por defecto.
Hoy no hay `versioned_docs/` ni `versions.json`: la versión viva es la única, y
el primer corte tendrá sentido cuando Codabench publique una versión que cambie
la interfaz descrita, no antes.
Referencia: `https://docusaurus.io/docs/versioning`.

## Sincronización sin diff

No hay `git diff` que leer. Lo que dispara una revisión es una de estas señales,
y cada una se registra con lo que la respalda:

1. **Cambia la documentación oficial.** Una URL nueva, una que desaparece, o
   —lo más traicionero— una que sigue existiendo con otro contenido detrás. La
   que desaparece la caza `python scripts/check_fuentes.py`, que recorre las URLs
   externas de `docs/` y de `docs-map.json`; la que cambia por dentro no aparece
   como cambio en ningún sitio y hay que abrir la página.
2. **Cambia la interfaz.** Un rótulo con otro nombre, un campo nuevo, un paso
   que ya no existe. Se ve navegando, y se registra con instancia y fecha.
3. **Una competición real se comporta distinto de lo documentado.** Es la señal
   más fuerte de las tres y la que más caro sale ignorar.

Con la señal identificada, cruzarla con `docs-map.json` —donde cada página
declara las URLs que la respaldan— para saber qué páginas revisar, y releerlas.
Una página mapeada puede no verse afectada, y una señal sin correspondencia en
el mapa puede invalidar varias páginas: esa decisión es semántica y va en el
informe. Que el mapa no dé coincidencias no significa que no haya trabajo.

El subcomando `drift` del helper compara dos commits de un repositorio de
código y aquí no aplica; además rechaza URLs en `paths`. El porqué está en
`data-formats.md`.

## Preparar una versión documental

Exigir una versión documental, una fuente verificable y correspondencia entre
ambas. Actualizar primero las docs actuales, validar y después crear el
snapshot pedido. Comprobar que no cambien snapshots previos. Respetar cambios
locales ajenos. No generar notas de versión a partir de los títulos de los
commits de este repositorio: describen el trabajo de documentar, no lo que
cambió en Codabench.

Este paquete no trae CI, hooks ni un servicio de sincronización; el CI de este
repositorio es `.github/workflows/docs-ci.yml` y **solo verifica**, la
publicación la hace Vercel. Para automatizar el seguimiento de una fuente
externa haría falta una integración revisada, con permisos mínimos, versiones
fijadas y revisión por PR; no crearla implícitamente.
