---
name: Página nueva
about: Proponer una página que hoy no existe en la guía
title: 'Nueva página: '
labels: ''
assignees: ''
---

<!--
La guía es un recorrido, no una colección de páginas sueltas: se lee en orden desde «Antes de
empezar» hasta que la competición acepta submissions. Una página nueva solo se sostiene si tiene
un sitio en ese recorrido y una fuente que la respalde; si no, es material que envejecerá sin que
nadie se entere.
-->

## Qué cubre

<!--
Una frase, la que será el **Objetivo:** de la página: qué consigue el lector cuando termina de
leerla. Si no sale en una frase, probablemente sean dos páginas o ninguna.
-->

## En qué sección del recorrido va

<!--
Marca una. Son las que hay; si crees que hace falta una sección nueva, dilo abajo y explica por
qué el contenido no cabe en ninguna de estas.

- [ ] `empezar/` — Antes de empezar: conceptos y requisitos previos
- [ ] `competicion/` — Crear la competición: Details, Participation, Pages, Collaborators
- [ ] `recursos/` — Recursos y tasks: Datasets, Programs, Tasks
- [ ] `evaluacion/` — Fases y evaluación: Phases, Leaderboards, Submission rule
- [ ] `submissions/` — Submissions: formato y prueba de la competición
- [ ] `referencia/` — Referencia: troubleshooting y fuentes
-->

## Por qué no cabe en una página existente

<!--
Lo más habitual es que sí quepa. Di qué página has mirado y qué le falta, o por qué añadirlo allí
la haría ilegible.
-->

## Qué fuente la respalda

<!--
Sin fuente no entra. Vale cualquiera de estas, y conviene decir cuál es:

- URL de la documentación oficial de Codabench que lo describe.
- Observación directa de la interfaz: qué pantalla, qué versión de Codabench y cuándo la miraste.

Esa fuente no es decorativa: acaba en la sección correspondiente de `build_nav.py`, que genera
`docs-map.json`. Es lo que permite responder «Codabench ha cambiado esto, ¿qué páginas hay que
revisar?» sin releer la guía entera.
-->

## Esbozo del contenido

<!-- Los H2 que tendría la página, o cuatro líneas de lo que iría dentro. Basta con eso. -->

---

<!--
Al implementarla: la página se declara en `SECCIONES` de `scripts/build_nav.py` y se ejecuta
`python scripts/build_nav.py --apply`, que le pone el `sidebar_position`, la `description` y
regenera el mapa de la guía. Un fichero que aparece en `docs/` sin declarar hace fallar
`build_nav.py --check`, y con él el CI: la navegación no se mantiene a mano.
-->
