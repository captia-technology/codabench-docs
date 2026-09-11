# Validación del paquete adaptado a `codabench-docs`

Fecha: 10 de septiembre de 2026.
Entorno ejecutado: Windows 11, Python 3.11.9, invocado como `python`.
Compatibilidad objetivo de los helpers: Python 3.10+ con biblioteca estándar.
No se ha ejecutado una matriz de versiones de Python ni una pasada en Linux.

## Ejecutado

- **56 de 57 pruebas aprobadas**, con `python -B -m unittest discover -s tests -v`
  desde la carpeta de la skill. Salida íntegra en `tests/validation-output.txt`.
- La prueba restante, `test_real_git_filenames_with_spaces_and_newlines`, **no
  puede ejecutarse en Windows**: crea a propósito un fichero con un salto de
  línea en el nombre y NTFS lo rechaza con `OSError 22` antes de que el helper
  intervenga. Se comprobó que el paquete original, sin modificar, falla
  exactamente igual en esta máquina, así que no es una regresión de la
  adaptación. En Linux pasa, y así consta en la validación del ZIP 1.1.0.
- `scripts/docs_tools.py` y `tests/test_docs_tools.py` comparados byte a byte
  con el paquete de origen: **idénticos**, hash SHA-256 incluido.
- Todos los enlaces Markdown relativos entre ficheros del paquete extraídos y
  resueltos contra el disco: ninguno roto. Es la comprobación que importa tras
  renombrar `references/captia-profile.md` a `references/perfil-repositorio.md`.
- Los 5 JSON y el YAML del paquete parseados; los 3 ficheros Python analizados
  sintácticamente; los frontmatters de las plantillas públicas comprobados.
- Un solo `SKILL.md`, menos de 500 líneas, frontmatter con nombre y descripción.
- Todos los ficheros del paquete con final de línea LF y sin BOM.
- `MANIFEST.sha256` regenerado con el formato original —`sha256sum` en modo
  texto, dos espacios, orden `LC_ALL=C` por ruta, todos los ficheros salvo el
  propio manifiesto—. El formato se dedujo reproduciendo el manifiesto original
  byte a byte antes de tocar nada; de no haberlo conseguido, se habría borrado,
  porque un manifiesto que no cuadra es peor que ninguno.
- Sin dependencias nuevas, hooks, instalaciones, credenciales ni llamadas de red
  en los helpers. Se conserva su código original.

Comando desde la carpeta de la skill:

```bash
python -B -m unittest discover -s tests -v
```

Los tests de estructura protegen la integridad de instrucciones y recursos; no
demuestran que un modelo vaya a seguirlas correctamente.

## Revisión posterior del paquete — 10 de septiembre de 2026

Auditoría del paquete ya instalado, con `scripts/` y `docs/` completos, en la
misma máquina y con el mismo Python. Lo ejecutado y observado:

- `python -B -m unittest discover -s tests -v` desde la carpeta de la skill y
  `python -B -m unittest discover -s .claude/skills/code-documentation/tests -v`
  desde la raíz del repositorio: los dos, **57 ejecutadas, 56 aprobadas**, con el
  mismo `OSError 22` de arriba como única incidencia.
- `sha256sum -c MANIFEST.sha256`: **37 de 37 correctos** antes de esta revisión.
  Tras las correcciones de este apartado se regeneró con el mismo formato y se
  volvió a verificar.
- Enlaces Markdown relativos del paquete extraídos y resueltos contra el disco:
  21 enlaces, ninguno roto, ninguna referencia al nombre antiguo
  `captia-profile.md` fuera de las dos menciones históricas que narran el cambio
  (`CHANGELOG.md` y este fichero).
- `python .claude/skills/code-documentation/scripts/docs_tools.py validate-map
  --map docs-map.json --docs-root .`: **código de salida 2**, rechazando la
  primera URL. Confirma lo que `data-formats.md` y `README.md` afirman.
- `python .claude/skills/code-documentation/scripts/docs_tools.py inventory
  --root .`: código 0.
- `python scripts/check_fuentes.py --listar` (sin red): código 0, 7 URLs
  externas distintas. `python scripts/check_codabench.py --help`: código 0.
- El comando de inventario tal y como estaba escrito en `SKILL.md`
  —`python "${CLAUDE_SKILL_DIR}/scripts/docs_tools.py" inventory --root .`—
  **fallaba con código 2**: esa variable no está definida en el shell de esta
  máquina y, vacía, deja la ruta en `/scripts/docs_tools.py`, que Git Bash
  resuelve dentro del directorio de instalación de Git.

Dos correcciones salieron de aquí. La primera, ese comando: ahora lleva la ruta
completa desde la raíz del repositorio y está comprobado con código 0. La
segunda, que el perfil, `SKILL.md`, `README.md` y `multi-repo-and-releases.md`
no mencionaban `scripts/check_codabench.py` ni `scripts/check_fuentes.py` —el
`scripts/` vacío del apartado siguiente explica por qué— y el último llegaba a
afirmar que nada avisa de una versión nueva de Codabench, que es exactamente lo
que hace el primero de los dos scripts.

## No ejecutado

- **No se han ejecutado los validadores del repositorio** —`check_docs.py`,
  `build_nav.py --check`— ni `npm run build`. Los escriben otros agentes en
  paralelo y en el momento de esta validación `scripts/` estaba vacío. Lo que
  esta skill afirma sobre ellos sale del contrato del setup y de la lectura del
  repositorio de referencia, no de haberlos visto correr aquí.
- No se ha invocado la skill dentro de una sesión real de Claude Code.
- No se ha abierto ninguna instancia de Codabench ni se ha contrastado ningún
  procedimiento de la guía contra su interfaz. La versión `Codabench v1.23` sale
  de las URLs de la documentación oficial, no de una comprobación desplegada.
- No se ha construido el sitio Docusaurus ni renderizado páginas, MDX o
  pantallas. No se han ejecutado Playwright, axe ni Lighthouse.
- No se ha resuelto el contrato visual: `assets/captia-design-contract.example.json`
  conserva sus `null` a propósito. Aquí el tema es copia exacta y no se
  rediseña, así que ese contrato solo se rellena al proponer o auditar un cambio.
- Los 20 casos de `evals/scenarios.json` son escenarios para una sesión
  posterior, no evaluaciones ejecutadas ni parte de las 57 pruebas.

No se afirma aval externo, certificación WCAG, auditoría de seguridad completa
ni garantía de acabado visual por pasar los tests del paquete.

## Referencias consultadas

Las del paquete original: showcase de Docusaurus, páginas oficiales de Ionic,
Refine y React Native, documentación oficial de Docusaurus, Playwright, WCAG 2.2
y `anthropics/skills:frontend-design`. Al adaptar no se consultaron fuentes de
terceros nuevas. Los detalles están en `references/showcase-patterns.md` y
`references/community-sources.md`.
