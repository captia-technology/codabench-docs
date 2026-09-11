# Contrato visual Captia: reutilizar, no reinventar

## En `codabench-docs` el tema ya está resuelto

El design system es el mismo para toda la organización y sigue siendo la única
autoridad visual, pero en este repositorio el trabajo de recuperarlo **ya está
hecho**: `src/css/custom.css` es una copia exacta de los tokens del manual de
captia.ai —verificada byte a byte fuera de los comentarios—, y lo mismo vale
para `src/components/Portada/` y para el mark de `static/img/logo-mark.svg`.

De ahí salen dos consecuencias prácticas:

- **No se rediseña.** Ni un valor cambia «para que quede mejor en esta guía».
  Si un token no encaja en un uso nuevo, el defecto es del uso, no del token; se
  registra y se propone al responsable del design system, como dice la sección
  de conflictos más abajo. Una guía no bifurca la marca de la organización.
- **No hay que rellenar el contrato para escribir una página.** El registro de
  `assets/captia-design-contract.example.json` se completa cuando se **propone**
  un cambio visual o se audita el acabado, no antes de tocar una tabla o un
  párrafo. Sus `null` siguen siendo deliberados: son un formulario en blanco,
  no una paleta.

El resto de este documento describe cómo se recupera y se verifica un design
system cuando no está resuelto. Se conserva íntegro porque sigue siendo la
referencia para auditar el acabado y para cualquier propuesta de extensión, y
porque el día que este repositorio deje de ser una copia exacta habrá que
volver a aplicarlo entero.

## Autoridad y recuperación

El usuario ha indicado que Claude ya conoce el design system de Captia.
Reutilizar primero el contexto autorizado, `CLAUDE.md`, reglas locales y los
recursos de diseño que ese contexto identifique. No volver a pedir paleta,
tipografía ni logotipo si ya están disponibles. Distinguir conocimiento de marca
de conocer los nombres exactos de variables y exports: verificar estos antes
de escribir código. No adivinar rutas del repositorio fuente.

Leer dentro del acceso permitido el paquete de UI, tokens, tema, CSS, estilos
globales, configuración de utilidades y documentación de componentes que existan.
No suponer que Captia usa Tailwind, shadcn, una biblioteca específica o nombres
`--captia-*`. Un recurso de Figma solo se usará si está identificado y autorizado;
no hace falta crear otro sistema en Figma para generar esta documentación.

## Registro privado antes del CSS

Completar `assets/captia-design-contract.example.json` en un lugar excluido de
la publicación, o registrar la información equivalente en la respuesta si es una
auditoría. Conservar repositorio, revisión, archivos y referencias del contexto.
No copiar fuentes de pago ni credenciales; los design tokens no son API tokens.
El archivo es una convención de la skill, no una configuración de Docusaurus.

Para cada rol visual utilizado, identificar su token o componente real, la
ubicación que lo define, los temas aplicables y su consumo en el portal. No
rellenar el contrato con nombres plausibles para que parezca completo. `null`
significa pendiente, no permite un fallback visual inventado.

Cubrir color de marca, superficies, texto, enlace, borde, foco y estados;
tipografía de lectura y código; espacios, radios, elevación, breakpoints, iconos,
activos de marca y movimiento. Un rol ausente se registra como tal. No crear
un token nuevo ni editar el paquete de diseño canónico sin autorización específica.

## Adaptación a Docusaurus

Preferir consumir la fuente canónica. Si se necesita un puente a variables del
tema, crear aliases que apunten a tokens reales; no duplicar sus valores en
muchos CSS. En el tema clásico, revisar los usos pertinentes de `--ifm-*`, no
cambiar solo `--ifm-color-primary` y asumir que el resto coincide con Captia.
Inspeccionar también menús, buscador, código, tabs, avisos y diagramas.

Heredar los selectores y el comportamiento real de claro/oscuro. No inventar
un tema oscuro, ni mostrar un conmutador sin un segundo tema completo. Registrar
la limitación si Captia solo dispone de un modo. Verificar tipografías realmente
cargadas, fallback aprobado, iconos y variantes de logotipo correspondientes.
No descargar nuevas fuentes o iconos por comodidad.

Si los componentes de la app dependen de su router, sesión o entorno de cliente,
reutilizar sus primitivas compatibles o preparar un adaptador fino con los mismos
tokens. Registrar qué parte se adapta. No importar toda la aplicación en MDX.

## Conflictos y bloqueos

Si el contexto y el checkout no coinciden, documentar ambas revisiones y seguir
la fuente canónica que establezcan las instrucciones vigentes. No mezclarlas
silenciosamente. Si faltan recursos, avanzar en contenido y estructura y
registrar `MARCA NO VERIFICADA`; no fabricar valores ni aprobar acabado visual.

Si un token no cumple el contraste requerido en un uso nuevo, buscar primero
una variante accesible existente. Si no existe, registrar el defecto y proponer
una corrección al responsable del design system; no recolorear Captia en secreto.
Una propuesta de extensión no es parte del sistema aprobado hasta aceptarse.

## Evidencia de conformidad

Comprobar identificadores contra fuentes y estilos calculados en el navegador.
Comparar una pantalla real autorizada de Captia y una página del portal cuando
estén disponibles. Revisar tipografía, espacios, superficies, botones y foco,
no solo el color del logo. Registrar archivos/revisión y capturas utilizadas.
Esta skill no contiene los tokens reales: debe obtenerlos del contexto de
Claude y los repositorios autorizados al ejecutarse.
