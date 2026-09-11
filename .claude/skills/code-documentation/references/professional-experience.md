# Experiencia documental de nivel producto

## Principio

Diseñar una extensión reconocible del producto. Docusaurus aporta el motor;
Captia aporta la identidad. Priorizar comprensión, orientación y ejecución de
tareas por encima de ornamentación. Estas son reglas del paquete, no una
certificación externa de diseño.

Aquí el contenido documenta una plataforma ajena, así que la identidad visual y
el vocabulario no vienen del mismo sitio: el acabado es de Captia y los rótulos
son de Codabench, en su idioma original. Ninguno de los dos se adapta al otro.

## Arquitectura de la información

Organizar por lo que el lector necesita conseguir y por audiencia real, no por
el árbol de archivos del código. Distinguir uso del producto, desarrollo,
referencia API, administración y operación solo si hay contenido real para ello.
Separar tutoriales, guías, referencia y explicaciones. No crear categorías vacías.
Conservar IDs y rutas existentes o definir redirecciones comprobadas.

Preparar una portada documental propia: título directo, qué se puede conseguir,
acceso a empezar, agrupaciones por tareas y enlaces de continuación. Mostrar
novedades solo si hay releases documentadas. Una portada no es una landing de
marketing: no añadir testimonios, cifras, promesas ni capturas de funcionalidades
inexistentes. Usar tarjetas para entradas alternativas, no para cada párrafo.

Construir un shell coherente: cabecera de producto, navegación principal,
sidebar contextual, breadcrumbs e índice de página cuando aporten orientación.
Mostrar versión activa y acceso a otras versiones cuando existan. Mantener la
tarea legible en móvil sin superponer sidebar, cabecera, TOC y botones.

## Búsqueda y orientación

Reutilizar el buscador existente. Aquí lo hay y es local:
`@easyops-cn/docusaurus-search-local` construye el índice durante el build.
Comprobar consulta relevante, resultado, extracto, apertura, cierre, teclado y
estado sin resultados; se puede hacer de verdad, así que hacerlo. Un campo de
búsqueda decorativo es un fallo. No sustituirlo por otro proveedor ni dar de
alta un servicio para completar una maqueta.

Que el índice sea local no lo hace privado: se genera con todo lo que hay en
`docs/` y se descarga en el navegador de cualquier visitante del sitio público.
Una página fuera del sidebar sigue estando en el índice, y un `noindex` afecta a
los buscadores externos, no a esto. Si algo no puede ser público, no puede estar
en `docs/`.

## Composición y tipografía

Heredar familia, pesos, escalas, espacios, radios, bordes, elevaciones e iconos
del design system. Mantener un ancho de lectura cómodo y una jerarquía que permita
escanear título, resumen, secciones, ejemplos y siguiente acción. Como heurística,
probar líneas de unas 60–80 letras; no imponerla si contradice los tokens aprobados.
No justificar párrafos ni reducir la letra para hacer caber una tabla.

Reservar el color primario para acciones, selección y énfasis significativo.
Evitar mayúsculas, badges, bordes, sombras y cajas repetidos sin significado.
No usar emojis como sistema de iconos. No introducir otra tipografía, una paleta
de moda, un hero enorme o degradados nuevos para aparentar calidad. Los efectos
que ya pertenezcan a Captia se pueden reutilizar con su uso previsto.

## Anatomía editorial de una página

Comenzar con un título específico y un resumen que describa el resultado y el
alcance. Mostrar requisitos, permisos y versión cuando cambien la tarea. Mantener
un solo H1 renderizado y una secuencia de encabezados comprensible. Usar español
profesional y los nombres exactos de controles, opciones y conceptos de
Codabench, en negrita y sin traducir: son lo que el lector ve en pantalla.

En guías: presentar pasos ejecutables, resultado esperado, cómo comprobarlo y
cómo recuperarse de los errores conocidos. En referencias: usar contratos,
restricciones y ejemplos concretos; no esconder detalles obligatorios en tabs.
En arquitectura: explicar responsabilidades y flujos observados, no atribuir
intenciones a los autores. Terminar con enlaces de continuación pertinentes.
Eliminar secciones vacías y texto de relleno de las plantillas.

## Contenido enriquecido con criterio

Preferir componentes del producto o del tema existente; consultar el contrato
de componentes antes de crear otros. Usar tabs para alternativas equivalentes,
no para ocultar secuencias. Usar avisos para riesgos, condiciones o aclaraciones
que afecten una decisión, sin colorear cada párrafo. Mantener código con lenguaje,
título cuando sea útil, copia funcional y salida esperada diferenciada.

Adaptar tablas al móvil con encabezados claros y desplazamiento contenido cuando
sea inevitable. Esta guía hoy **no tiene capturas**: los procedimientos se
escriben con pasos numerados y los rótulos de la interfaz en negrita, que es lo
que no se queda obsoleto al cambiar un píxel. Si algún día se añaden capturas,
presentarlas con encuadre consistente, pie, texto alternativo y datos ficticios,
nunca con una instancia real identificable. Usar diagramas solo si aclaran
relaciones reales, y recordar que Mermaid no está instalado en este sitio.
Proporcionar siempre la explicación textual: una imagen no sustituye a las
instrucciones, y en una guía sin capturas es lo único que hay.

## Implementación mantenible

Reutilizar Docusaurus y los componentes Captia compatibles con SSR. No importar
la aplicación completa, sus proveedores de autenticación o su enrutador para
conseguir un botón. Preferir un adaptador pequeño sobre duplicar el design system.
Crear estilos compartidos y evitar CSS por página y selectores frágiles del tema.
Preservar el rendimiento y no añadir animación o JS sin una necesidad del lector.

Aplicar cambios globales solo dentro del alcance. Comprobar también documentos
históricos que usan el mismo tema, componentes y activos: no editar sus textos
no impide que un cambio compartido rompa su renderizado. Mantener compatibilidad
o adaptadores versionados. No cambiar rutas o proveedores por motivos estéticos.

## Criterio de acabado

No considerar terminado un cambio de interfaz mientras queden tokens de marca
inventados, imports inexistentes, enlaces ficticios, controles sin función,
contenido de plantilla, overflow del viewport o errores de consola no explicados.
Evaluar por separado exactitud, composición, accesibilidad y comportamiento.
Registrar el alcance real de la revisión en `visual-qa-report.md`.
