# Code Documentation para Claude Code

Skill original 1.1.0, preparada el 7 de septiembre de 2026, **adaptada a
`codabench-docs` el 10 de septiembre de 2026**. Documentación técnica
contrastada con su fuente, con perfil de este repositorio y Docusaurus. No es
una skill oficial de Anthropic ni un plugin de Superpowers.

## Qué cambia al adaptarla a este repositorio

El paquete original documenta una aplicación propia: la evidencia de cada
afirmación es un commit del repositorio de código y la deriva se detecta con un
`git diff` entre dos revisiones. **Aquí la fuente es Codabench, una plataforma
externa**, y no hay checkout que comparar. La evidencia es la documentación
oficial de Codabench, la observación directa de su interfaz y las competiciones
reales ya montadas; el modo `sync` funciona a partir de esas señales, no de un
diff. Los modos, la tabla de escrituras permitidas y los límites de seguridad
se conservan intactos.

Cambia también dónde vive cada cosa: la navegación y la trazabilidad se declaran
en `SECCIONES`, dentro de `scripts/build_nav.py`, que genera el sidebar, el mapa
de la guía y `docs-map.json`. Y el tema ya está resuelto —es copia exacta del
manual de captia.ai—, así que el contrato de marca solo se rellena para proponer
o auditar un cambio visual, no para escribir una página.

El detalle operativo está en `references/perfil-repositorio.md`; el
cambio de modelo de evidencia, en `SKILL.md` y en
`references/multi-repo-and-releases.md`.

Este paquete contiene instrucciones y recursos, no un tema visual instalado ni
un portal ya construido. No incluye tokens del design system, componentes React
ni capturas.

## Instalación

Ya está instalada en este repositorio, en
`.claude/skills/code-documentation/`. La estructura tiene que ser exactamente
esta, sin un nivel extra `skill/`:

```text
.claude/skills/code-documentation/SKILL.md
.claude/skills/code-documentation/references/
.claude/skills/code-documentation/scripts/
.claude/skills/code-documentation/assets/
```

Para llevarla a otro repositorio, copiar la carpeta completa. Si en el destino
ya existe una `code-documentation`, conservar una copia de la anterior **fuera**
de `.claude/skills/` antes de reemplazarla: dos carpetas con el mismo nombre se
descubren las dos, y mezclar archivos de dos versiones deja instrucciones que se
contradicen. Abrir Claude Code y comprobar que `/code-documentation` aparece;
reiniciar la sesión si no se detecta.
Referencia oficial: `https://code.claude.com/docs/en/skills`.

Para uso personal en todos los proyectos, la misma carpeta va en
`~/.claude/skills/`. La instalación por proyecto es la que se versiona junto al
repositorio, que es lo que interesa aquí: la skill y las reglas que describe
viajan con el contenido que validan.

## Ejemplos de uso

```text
/code-documentation audit Revisa la guía frente a la documentación oficial de Codabench. No cambies archivos.

/code-documentation document Documenta la creación de una Task con los rótulos exactos de la interfaz y enlaza la fuente oficial.

/code-documentation sync Codabench ha cambiado el formulario de Phases. Dime qué páginas hay que revisar y actualiza solo esas.

/code-documentation bootstrap Conserva primero el contenido actual y prepara después su reparto en secciones.

/code-documentation release Prepara el snapshot documental de la versión contrastada actual. No publiques ni crees tags Git.
```

Para trabajar el acabado del portal:

```text
/code-documentation design Revisa el portal Docusaurus de esta guía. El tema es copia exacta del design system de Captia y no se rediseña: reutilízalo y verifica los identificadores en src/css/custom.css. Toma ideas de organización del showcase, sin copiar otras marcas. Trabaja sobre portada, navegación y páginas con contenido real. Valida una página piloto y extiende los patrones al alcance acordado. Usa el navegador disponible para revisar responsive, los dos temas e interacciones. No publiques, no hagas push ni instales dependencias sin autorización. Declara toda comprobación no ejecutada.
```

Para evaluar sin modificar:

```text
/code-documentation audit Revisa exactitud frente a la fuente, claridad, fidelidad al design system y acabado visual. No modifiques el repositorio. Separa hallazgos observados de controles que no hayas podido ejecutar.
```

Los modos son instrucciones interpretadas por Claude, no ejecutables externos.

## La fuente es externa

No hace falta `--add-dir` a ningún repositorio de código: Codabench no se clona.
Lo que sí hace falta es acceso a su documentación oficial
(`https://docs.codabench.org/`) y, para contrastar la interfaz, un navegador y
una cuenta en la instancia que corresponda. Si no hay ninguna de las dos cosas,
se documenta lo comprobable y se declara el bloqueo.

El repositorio privado `captia-technology/codabench-dataset-pipeline` prepara
los ficheros que la guía asume ya listos. Es un vecino, no una fuente, y su
acceso está restringido: no enlazarlo como si el lector lo tuviera.

Opcionalmente se puede copiar `assets/docs.config.example.json` como
`docs.config.json` en la raíz, **después de sustituir sus valores de ejemplo**.
No es un archivo nativo de Docusaurus: lo interpreta el agente. `docs-map.json`
**no** se copia del ejemplo: lo genera `scripts/build_nav.py`.

## Helpers locales

Requisitos: Python 3.10+ y solo biblioteca estándar. En esta máquina Python es
3.11 y se invoca como `python`; en Linux o macOS puede ser `python3`.

```bash
# Inventario: lee archivos y metadatos; no ejecuta configuraciones JS.
python .claude/skills/code-documentation/scripts/docs_tools.py inventory --root .

# Conservar los bytes del directorio documental antes de una migración.
# Es la única operación del helper que escribe archivos.
python .claude/skills/code-documentation/scripts/docs_tools.py baseline \
  --root . --docs docs --output .docs-baselines/legacy-inicial.zip

# Pruebas del paquete: helpers y estructura. No prueban la guía ni Docusaurus.
python -B -m unittest discover \
  -s .claude/skills/code-documentation/tests -v
```

`inventory` escribe JSON en stdout, no en el proyecto. Un error de entrada o de
operación devuelve 2. `baseline` genera un ZIP con hashes y un manifiesto de
exclusiones; no crea una versión de Docusaurus ni un tag Git, y no conserva
archivos fuera de `--docs`. Los nombres de archivo y los metadatos de los
informes pueden ser internos: revisarlos antes de publicarlos, y recordar que
los filtros de nombres no sustituyen una revisión de secretos.

**`validate-map` y `drift` no se usan en este repositorio.** Ambos exigen rutas
relativas POSIX y rechazan cualquier cadena con `:`, es decir, cualquier URL; y
`docs-map.json` aquí declara URLs porque la fuente es externa. No relajar esa
validación del helper: es la misma que impide que un mapa lo haga leer fuera del
repositorio. Quien valida el mapa aquí es `python scripts/build_nav.py --check`.
El porqué completo, en `references/data-formats.md`.

## Los validadores del repositorio

Son otra cosa, y son los que corren en CI:

```bash
python scripts/check_docs.py          # invariantes del contenido de docs/
python scripts/build_nav.py --check   # navegación declarada, mapa y docs-map
npm run build                         # build de producción, SIN --locale
```

`scripts/` tiene además dos comprobaciones de la fuente externa que **no** corren
en CI, porque necesitan red y dependen de servidores ajenos:
`python scripts/check_codabench.py` —¿hay release nueva de Codabench y qué
páginas dependen de qué fuentes— y `python scripts/check_fuentes.py` —¿siguen
vivas las URLs externas que cita la guía; `--listar` las enumera sin red—.

Aprobar las pruebas del paquete no dice nada sobre ellos, ni al revés.

## Contenido

`SKILL.md` controla el flujo; `references/` contiene reglas específicas que se
cargan según la tarea; `assets/` incluye configuración, mapa y plantillas;
`scripts/docs_tools.py` aporta comprobaciones deterministas; `tests/` y
`evals/scenarios.json` permiten comprobar el paquete. `agents/openai.yaml` es
metadato complementario para entornos compatibles y no configura Claude Code.

## Recursos de diseño y QA

`references/perfil-repositorio.md`: rutas, scripts, publicación y límites de aquí.
`references/professional-experience.md`: estándar editorial y de interfaz.
`references/captia-design-contract.md`: el tema ya resuelto y cuándo se rellena.
`references/showcase-patterns.md`: referencias y decisiones de adaptación.
`references/component-contracts.md`: comportamiento esperado, sin imports ficticios.
`references/visual-qa.md`: matriz, evidencia y criterios de aprobación.

`assets/captia-design-contract.example.json` se conserva sin resolver a
propósito: sus `null` no son valores de marca, y aquí solo se completa al
proponer o auditar un cambio visual. Las plantillas públicas se adaptan al
contenido; las de especificación y QA viven en `docs-meta/` y nunca se publican.

## Procedencia y límites

Ver `references/community-sources.md`. Se consultaron las prácticas de
`anthropics/skills:doc-coauthoring` y
`obra/superpowers:verification-before-completion`, además de Docusaurus y Diátaxis.
No se redistribuyen ni descargan sus paquetes. La popularidad de esos
repositorios no equivale a un aval de esta skill ni a una certificación de seguridad.
Codabench es un proyecto independiente y no avala esta skill ni esta guía.

Las instrucciones reducen riesgos, pero no son un sandbox. La seguridad efectiva
sigue dependiendo de permisos, revisión y aislamiento. No hay hooks, credenciales,
telemetría, llamadas de red, instaladores remotos ni publicación automática en
este paquete —el hook del repositorio es otra cosa y vive en `.claude/hooks/`—.
Los helpers se prueban con repositorios temporales; el comportamiento completo
del agente debe validarse en tu Claude Code y en este repositorio.
