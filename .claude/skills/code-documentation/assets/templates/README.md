# Uso de las plantillas

Estas plantillas no son páginas terminadas ni describen capacidades conocidas de
Codabench. Sustituir todos los marcadores `{{...}}`, eliminar las secciones no
aplicables y resolver los enlaces desde evidencia. No copiar esta carpeta dentro
de `docs/`: solo se publica lo que hay ahí, y una plantilla con marcadores
publicada es un fallo visible.

| Necesidad | Plantilla |
| --- | --- |
| Entrada al portal | `portal-home.md` |
| Tarea o tutorial | `guide.md` |
| Contrato técnico | `api-reference.md` |
| Sistema y flujos | `architecture.md` |
| Conexión con otro servicio | `integration.md` |
| Operación y recuperación | `runbook.md` |
| Release | `release-notes.md` |
| Diseño del portal, interno | `experience-spec.md` |
| QA visual, interno | `visual-qa-report.md` |
| Auditoría técnica, interna | `audit-report.md` |

## Lo que cambia en este repositorio

Las plantillas públicas ya vienen con la forma que exige
`.claude/rules/documentacion.md`, que es la que valida `check_docs.py` y el hook:

- **Front matter con `title`,** y un **único H1** que dice exactamente lo mismo,
  sin emoji. No es cosmético: si no coinciden, la validación bloquea.
- **El rótulo de objetivo abre el cuerpo.** La primera línea es
  `**Objetivo:**` seguido de una frase que diga qué consigue el lector en esa
  página. De ahí sale la `description` del front matter.
- **`sidebar_position`, `sidebar_label` y `description` no se escriben a mano.**
  Los pone `python scripts/build_nav.py --apply` desde la declaración
  `SECCIONES`. La `description` que traen estas plantillas es un marcador que se
  regenera; lo que hay que cuidar es el `**Objetivo:**`.
- **Los rótulos de Codabench van en negrita y sin traducir** —**Benchmarks →
  Management**, **Add Dataset/Program**, **Force Best**—: son lo que el lector
  tiene delante en la pantalla.

Las plantillas internas —`experience-spec.md`, `visual-qa-report.md`,
`audit-report.md`, `evidence-ledger.json`— van a `docs-meta/`, nunca a `docs/`,
y por eso no llevan front matter ni `**Objetivo:**`.

`portal-home.md` es la excepción entre las públicas, y lo es por partida doble:
no lleva `**Objetivo:**` —la portada y el mapa generado son los dos únicos
documentos que no lo llevan, porque no son páginas de tarea— y tampoco lleva H1,
porque la portada real no es un `.md`: es `docs/index.mdx`, servida en `/`
porque `routeBasePath` es la raíz, con `hide_title: true` y el H1 dentro del
componente de `src/components/Portada/`. Por eso esa plantilla no se copia a
`docs/` como `.md`: ahí la falta de H1 haría fallar a `check_docs.py`, que en un
`.md` exige uno y solo uno. Es el guion de qué tiene que contener la portada,
no su maquetado. Y una portada no es una landing de marketing: ni
testimonios, ni cifras, ni promesas, ni funcionalidades que Codabench no tenga.

Convertir una página a MDX solo cuando los componentes lo justifiquen y sus
imports existan; hoy el único `.mdx` del sitio es la portada. Estas plantillas no
traen componentes React ni una paleta alternativa: el tema ya está resuelto y se
reutiliza tal cual.
