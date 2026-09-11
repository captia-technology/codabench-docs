---
paths:
  - "src/css/**"
  - "src/**/*.js"
  - "src/**/*.jsx"
  - "docusaurus.config.js"
  - "static/img/**"
---

# Base de estilos: Captia Technology Design System

Los tokens **no se eligen aquí**. Salen del Captia Technology Design System, extraído de la web de
producción `captiatechnology.com`. El contrato completo viaja dentro de la skill de este
repositorio —[`.claude/skills/code-documentation/references/captia-design-contract.md`](../skills/code-documentation/references/captia-design-contract.md),
con su ejemplo en `assets/captia-design-contract.example.json`— y es el mismo fichero, byte a
byte, que el del manual de captia.ai: la skill se copió entera y esa parte no se adaptó, porque el
sistema de diseño es el mismo. No lo dupliques aquí ni en `CLAUDE.md`: lo que se copia por
comodidad se queda desactualizado sin que nadie lo note.

## Este sitio no bifurca el sistema: el tema es una copia exacta

Y aquí hay un eslabón más que en el manual: **el tema de este repositorio es una copia exacta del
de `my-qa-captia-ai-app`**, no una adaptación:

- `src/css/custom.css` y `src/components/Portada/styles.module.css` son **byte a byte los mismos
  ficheros** fuera de los comentarios. Ahí está todo lo que es token, color, tipografía, radio y
  medida. Comprobarlo es una orden:

  ```bash
  diff <(grep -v '^\s*\*\|^/\*\*' src/css/custom.css)        <(grep -v '^\s*\*\|^/\*\*' ../../CAPTIA-TENANTS/my-qa-captia-ai-app/src/css/custom.css)
  ```

- `static/img/logo-mark.svg` es idéntico también dentro de los comentarios.
- `src/components/Portada/index.js` tiene **una sola diferencia**, y no toca ni un estilo: el
  rótulo del panel de portada, que allí estaba fijado a «Manual funcional» dentro del JSX, aquí es
  la prop `rotulo` con ese mismo valor por defecto. El componente de la referencia renderiza
  exactamente igual; este sitio pasa el suyo, porque una guía de una plataforma ajena no es el
  manual funcional de nada. Cualquier otra divergencia en ese fichero es un defecto.

La consecuencia práctica es la regla: **un valor no se decide aquí**.

- Si un token cambia en el manual de captia.ai, cambia aquí igual y con el mismo valor.
- Si aquí hace falta algo que allí no existe, se lleva allí primero y después se copia.
- Nunca al revés, y nunca «solo en este sitio, que es más pequeño».

Dos sitios con el mismo logotipo y distinto azul se leen como dos marcas, y la divergencia empieza
siempre por un ajuste local que parecía inocente. Antes de tocar un fichero de este bloque,
comprueba si el cambio pertenece al sistema —entonces va al manual— o es de este sitio en
exclusiva; en la práctica, casi nunca lo segundo.

## Los cuatro colores de marca

| Token | Valor | Uso |
|---|---|---|
| `--color-black` | `#0a0a0a` | Texto en modo claro |
| `--color-brand-primary` | `#0000dc` | Enlaces en modo claro |
| `--color-accent` | `#00ff79` | Acento y enlaces en modo oscuro |
| `--color-accent-on-light` | `#007a3d` | El acento cuando el fondo es claro |

Tipografía **Geist** (texto) y **JetBrains Mono** (datos), cargadas desde Google Fonts en
`docusaurus.config.js`. Escala de espaciado de 4 px. Radios `.25 / .5 / .75 / 1rem`.

## Por qué el color de enlace cambia entre modos

No es una preferencia. Está medido:

```
#0000dc sobre blanco    10.33  AAA
#0000dc sobre #0c0e14    1.87  FALLA
#00ff79 sobre blanco     1.35  FALLA
#00ff79 sobre #0c0e14   14.31  AAA
```

Ninguno de los dos colores de marca sirve para los dos modos. Claro usa azul, oscuro usa verde —
que es lo que hace la propia web de la que salió el sistema.

**El verde nunca como texto sobre fondo claro.** Para eso existe `--color-accent-on-light`, y así
está aplicado: la barra del enlace activo del menú lateral es `--captia-accent-on-light` en claro y
`--captia-accent` en oscuro. El verde puro solo aparece sobre superficie negra —el pie del sitio y
el panel de la portada—, que es donde alcanza contraste.

## La única desviación permitida, y está documentada

El sistema define `--color-text-secondary: #64748b`, que en oscuro da **4.05**: por debajo del 4.5
que WCAG AA exige para texto normal. En la web de marketing se usa en texto grande y pasa; aquí el
texto secundario son celdas de tabla. `src/css/custom.css` lo sube a `#94a3b8` (**7.52**, AAA), con
el motivo escrito en el propio fichero.

Es **la única**, y lo es en los dos repositorios a la vez: la desviación vive en el tema copiado,
no en este sitio. Si añades un token nuevo, **mide su contraste en los dos modos antes de usarlo**
y anota el ratio junto a la declaración, como está el resto. Un rebrand que copia colores sin medir
produce texto por debajo de AA sin que nada avise: el build pasa, el sitio se ve «bien» en la
pantalla de quien lo escribió, y el problema solo aparece en la revisión de accesibilidad.

## El logotipo

`static/img/logo-mark.svg` es el mark real del sistema, con su geometría exacta: cuadrado `#00FF79`
con los arcos y el anillo en `#0000DC`. **No lo sustituyas por una aproximación ni lo recolorees.**
Se usa como logo del navbar, como favicon y, importado como componente React, en la portada.

No hay tarjeta social, y es deliberado: generarla exigiría rasterizar el mark y la binaria de Geist,
que el propio sistema declara no vendorizada. Antes que publicar un logo falso, ninguno.

## Los componentes de `src/`

Los de `src/components/Portada/` son adaptadores documentales, no componentes de la aplicación: no
importan nada de Codabench ni de captia.ai, no tocan `window` al evaluar el módulo —Docusaurus los
renderiza también en servidor— y toda su marca sale de los tokens de `src/css/custom.css`. Un
componente nuevo se escribe igual: sin colores literales, sin fuentes propias y sin depender del
navegador para pintarse la primera vez.
