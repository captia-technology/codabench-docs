# Verificación visual y de experiencia

## Reglas de aprobación

Evaluar las cuatro capas de forma independiente: exactitud técnica, claridad
editorial, fidelidad a Captia y experiencia renderizada. Usar `APROBADO`,
`FALLIDO`, `NO EJECUTADO` o `NO APLICA` con evidencia y motivo. No convertir
`NO EJECUTADO` en aprobado ni calcular una nota estética que tape bloqueos.

La fidelidad a Captia se comprueba contra el tema que ya hay —copia exacta del
manual de captia.ai—, no contra un criterio propio: si una página se ve
distinta, el fallo está en la página, no en los tokens.

## Alcance y preparación

Inspeccionar los scripts del proyecto antes de ejecutar build, serve o tests.
Usar Playwright, Claude in Chrome o un navegador realmente disponible, sin
instalaciones automáticas. Trabajar en un entorno autorizado y con datos de prueba.
No exportar cookies, storageState, credenciales ni sesiones al paquete o al sitio.

Antes de una modificación visual, capturar el estado inicial cuando sea posible.
Después, revisar la compilación servida con la configuración real de rutas.
Esperar fuentes, imágenes y contenido estable; controlar animaciones en pruebas
de captura, sin ocultar errores ni contenido para hacerlas pasar. Conservar
ruta, commit, navegador, viewport, tema, fecha y hallazgos. Guardar evidencias
solo en un destino excluido de la publicación y permitido por el proyecto.

## Matriz mínima para cambios de shell o componentes

| Dimensión | Cobertura |
| --- | --- |
| Tipos de página | Portada (`/`, MDX con componentes), índice de sección, página procedimental con pasos, referencia con tabla ancha, troubleshooting y el mapa generado |
| Viewport | Móvil 390 px, tablet 768 px y desktop 1440 px de ancho; añadir el reflow a 320 px |
| Tema | Claro y oscuro: los dos existen, `respectPrefersColorScheme` está activo y el conmutador funciona |
| Navegación | Sidebar móvil, breadcrumbs, TOC/anclas, enlaces y el desplegable de versión |
| Búsqueda | Consulta, resultado relevante, vacío, teclado, cierre y extracto con la ruta visible |
| Interacción | Tabulación, foco, copiar código, desplegables y volver a contenido |
| Histórico | `NO APLICA` mientras no exista `versioned_docs/`; en cuanto exista, una ruta por familia afectada |

Las medidas son viewports de prueba, no nuevos breakpoints o tokens de Captia.
Para cambios locales, cubrir las rutas/componentes afectados y documentar por
qué no se necesita toda la matriz. La falta de una familia se marca `NO APLICA`,
no se crean páginas ficticias para completar una lista.

Dos casos que en esta guía dan problemas y conviene mirar siempre: las tablas
de inventario y de errores, que son anchas y en móvil tienen que desplazarse
dentro de su caja sin arrastrar la página entera, y los bloques de código con
rutas largas de recursos. Las capturas no están en la lista porque hoy no hay.

## Revisión de cada render

Abrir las capturas y navegar, no limitarse a generarlas. Revisar alineación,
ritmo, fuente realmente cargada, jerarquía, longitud de línea y densidad. Buscar
superposiciones, truncados, huérfanos visuales, saltos al cargar, imágenes rotas
y bloques que desborden el viewport. Un scroll interno de código/tabla puede ser
válido; el desbordamiento horizontal de toda la página debe corregirse.

Comprobar que menús, tabs y botones funcionan con teclado; el foco es visible y
no queda bajo cabeceras. Probar código largo, títulos largos, etiquetas de versión,
listas y estados vacíos con datos representativos, sin inventar contratos.
Revisar consola, errores de carga y comportamiento en rutas profundas.

## Accesibilidad

Usar WCAG 2.2 AA como objetivo de revisión: contraste de texto normal 4.5:1,
texto grande 3:1 según la definición WCAG, contraste no textual aplicable 3:1,
operación por teclado, encabezados, nombres accesibles, alt, foco no oculto y
reflow. Comprobar zoom al 200% y la lectura a 320 CSS px. Respetar preferencias
de movimiento reducido. Revisar los criterios y excepciones oficiales antes
de declarar conformidad. Si se usa axe u otro validador existente, acompañarlo
con revisión manual: un escaneo automático no certifica accesibilidad.

## Regresión y rendimiento

Cuando ya exista infraestructura, comparar snapshots con Playwright sin
actualizar baselines a ciegas. Toda diferencia aceptada necesita revisión y
motivo; una baseline nueva tampoco demuestra que el primer diseño sea correcto.
Usar la misma versión de navegador, sistema y fuentes para comparaciones fiables.

Ejecutar las comprobaciones de rendimiento disponibles. Registrar rutas,
entorno y resultados observados; no inventar puntuaciones Lighthouse ni afirmar
Core Web Vitals de usuarios reales a partir de una prueba de laboratorio.
Evitar nuevas fuentes remotas, scripts pesados y capturas sin optimizar.

## Bloqueos de entrega visual

No declarar el acabado aprobado con marca sin resolver, placeholders, controles
inertes, links ficticios, contraste/foco defectuoso, fugas de datos, errores de
renderizado o regresiones históricas. Si no hay navegador, entregar cambios y
revisión estática con estado visual `NO EJECUTADO`, sin capturas inventadas.
Tras corregir un fallo, repetir su prueba y registrar la nueva evidencia.

## Fuentes

```text
https://playwright.dev/docs/test-snapshots
https://www.w3.org/WAI/WCAG22/quickref/
```
