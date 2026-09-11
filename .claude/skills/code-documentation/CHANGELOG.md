# Cambios del paquete

## 1.1.0 — adaptación a `codabench-docs` — 2026-09-10

El paquete se copia del manual de captia.ai y se adapta a un repositorio que
documenta una **plataforma externa**, no una aplicación propia. La versión del
paquete no sube: son las mismas instrucciones aplicadas a otra fuente.

Lo que cambia de fondo: la evidencia ya no es el commit de un repositorio de
código, sino la documentación oficial de Codabench, la observación directa de su
interfaz y las competiciones reales ya montadas. `SKILL.md` lo declara en una
tabla y reescribe el modo `sync`, que aquí no parte de un diff. Los seis modos,
la tabla de escrituras permitidas y los límites de seguridad se conservan.

`references/captia-profile.md` pasa a `references/perfil-repositorio.md` y se
reescribe con las rutas, los scripts, el dominio y las reglas de este
repositorio, incluida la navegación declarada en `scripts/build_nav.py`.

`references/multi-repo-and-releases.md` deja de describir dos checkouts: la
fuente es Codabench y el vecino privado `codabench-dataset-pipeline`, y la
sincronización parte de señales observadas, no de `git diff`.

`references/data-formats.md` documenta que `docs-map.json` declara **URLs** en
`paths` y que, por eso, `validate-map` y `drift` del helper rechazan el mapa de
este repositorio: exigen rutas relativas. No se relaja el helper; el mapa lo
valida `build_nav.py --check`. `docusaurus.md` recoge lo que este sitio declara
de verdad —docs en la raíz, `format: 'detect'`, enlaces rotos que tumban el
build, buscador local, sin Mermaid— y `documentation-method.md` sustituye la
lectura de código por las tres evidencias de una plataforma externa.

`captia-design-contract.md` se conserva íntegro y se le antepone lo único que
cambia aquí: el tema ya está resuelto como copia exacta y no se rediseña.
`assets/captia-design-contract.example.json` sigue sin resolver a propósito.

Las plantillas públicas incorporan el H1 y el rótulo `**Objetivo:**` que exigen
las reglas de este repositorio, y las internas dejan de pedir commits como
evidencia. Los ejemplos de `docs-map` y `docs.config` pasan a URLs e id
`codabench`. Los 20 escenarios de aceptación se reescriben para esta guía.

`scripts/docs_tools.py` y `tests/test_docs_tools.py` se conservan sin un solo
cambio. `MANIFEST.sha256` se regenera con el formato original.

## 1.1.0 — 2026-09-07

Estándar obligatorio de experiencia documental profesional y modo `design`.
Contrato de fidelidad al design system Captia ya conocido por Claude.
Referencias estructurales del showcase: Ionic, Refine y React Native.
Guía de componentes sin imports ficticios y plantillas editoriales ampliadas.
Matriz de QA visual, responsive, accesibilidad y compatibilidad histórica.
Escenarios de aceptación adicionales y pruebas de estructura del paquete.
Sin cambios en `scripts/docs_tools.py` ni en sus 41 pruebas existentes.

## 1.0.0 — 2026-09-07

Paquete inicial: evidencia de código, auditoría, sincronización, conservación
histórica, releases y perfil Captia con repositorios separados.
