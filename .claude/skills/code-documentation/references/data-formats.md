# Formatos propios del paquete

Estos archivos no forman parte del estándar de Claude Code ni de Docusaurus.

## docs.config.json

Usar el ejemplo como instrucciones declarativas para el agente. Resolver rutas
relativas a su ubicación. `source_repositories` identifica las fuentes
autorizadas; `documentation` define el repositorio de salida; `policy` expresa
restricciones. Los helpers no cargan este archivo automáticamente: sus
argumentos son explícitos. No guardar credenciales ni URLs con tokens.

En este repositorio la fuente no es un checkout: es la plataforma externa
Codabench. Por eso `assets/docs.config.example.json` declara la fuente con su
documentación oficial y su versión contrastada en vez de con una ruta local, y
deja escrito que no hay repositorio de código que comparar.

## docs-map.json

Esquema 1: `documents` contiene objetos con `doc` (archivo `.md` o `.mdx`
relativo al repo documental) y `sources` (lista de `id` y `paths`). Cada `id`
identifica una fuente; `paths` contiene lo que respalda esa página. No repetir
`doc`.

**Aquí `paths` son URLs, no rutas de fichero.** En un manual de producto propio
apuntarían a directorios del repositorio de la aplicación, y la pregunta que
responde el mapa sería «si se ha tocado este módulo, ¿qué páginas hay que
revisar?». La pregunta es la misma, pero la fuente es externa: «si Codabench
cambia esta pantalla o esta página de su documentación, ¿qué páginas hay que
revisar?».

```json
{
  "schema_version": 1,
  "documents": [
    {
      "doc": "docs/recursos/tasks.md",
      "sources": [
        {"id": "codabench", "paths": [
          "https://docs.codabench.org/v1.23/Organizers/Running_a_benchmark/Resource-Management/"
        ]}
      ]
    }
  ]
}
```

El fichero real lo **genera** `scripts/build_nav.py` desde la lista `SECCIONES`,
con una cabecera `_generado_por` y un bloque `_fuentes` que identifica el
producto y la revisión contrastada. No se edita a mano: un mapa escrito a mano
se pierde en la siguiente ejecución de `build_nav.py --apply`, y uno que no
cuadre con `SECCIONES` hace fallar `build_nav.py --check` y con él el CI.

No todas esas URLs son documentación oficial: alguna es un recurso público de la
comunidad. Distinguirlo al citarlas, porque no envejecen igual ni tienen el
mismo peso como evidencia.

Los ejemplos de este paquete no afirman que esas URLs existan. Comprobarlas
abriéndolas antes de declararlas. Una coincidencia solo indica que una página
debe revisarse, nunca que esté obsoleta ni que esté al día.

### Lo que el helper NO puede validar en este repositorio

`docs_tools.py` valida rutas relativas POSIX: rechaza de entrada cualquier
cadena con `:`, con `\` o con segmentos vacíos. Una URL empieza por `https:` y
lleva `//`, así que **`validate-map` y `drift` rechazan el `docs-map.json` de
este repositorio** con un error de entrada (código de salida 2). No es un fallo
del mapa ni del helper: son dos convenciones distintas del mismo esquema.

No «arreglar» esto relajando el validador del helper. Esa comprobación de rutas
es también la que impide que un mapa haga que el helper lea fuera del
repositorio, y las pruebas del paquete la cubren. Quien ocupa su lugar aquí es
`scripts/build_nav.py --check`, que comprueba que todo documento esté declarado,
que el mapa generado coincida con la declaración y que no haya documentos
huérfanos.

De los cuatro subcomandos del helper, en este repositorio siguen siendo útiles
`inventory` —enumerar el árbol y sus manifiestos— y `baseline` —conservar los
bytes de `docs/` antes de una migración—. `validate-map` y `drift` no aplican.

## Registro de evidencia

Usar `assets/templates/evidence-ledger.json` para relacionar afirmaciones con
fuentes y controles. Guardarlo fuera de `docs/` —`docs-meta/` es el sitio—
salvo revisión explícita de visibilidad. Los nombres y estados son una
convención humana, no un verificador semántico. Sustituir todos los marcadores
antes de entregarlo.

En este repositorio el campo `revision` de cada evidencia no es un commit: es
la versión de la documentación oficial que aparece en la URL, o la fecha en que
se observó la interfaz. Escribir cuál de las dos es, no un identificador que
parezca un commit.

## Archivo histórico

`baseline` conserva archivos regulares del directorio elegido, excepto carpetas
generadas, enlaces y nombres sensibles conocidos. Recorre el directorio, no
solo archivos seguidos por Git. Por ello puede incluir borradores no seguidos
o ignorados: revisarlos antes de versionar o publicar el ZIP.

`BASELINE-MANIFEST.json` identifica directorio, HEAD si existe, estado de cambios
Git, hashes SHA-256, tamaños y exclusiones. `complete_within_selected_directory`
es falso si hubo exclusiones. El indicador no garantiza ausencia de secretos
ni que se hayan incluido documentos de otros directorios.

## Contrato de marca y experiencia

`assets/captia-design-contract.example.json` es un registro privado para el
agente. `source_of_truth` identifica evidencias; `themes` recoge los modos
reales; `roles` mapea necesidades visuales a identificadores y archivos
canónicos; `reused_components` documenta reutilización; `approved_exceptions`
solo recoge excepciones autorizadas. Los `null` iniciales son intencionados.

En este repositorio el tema es copia exacta del manual de captia.ai, así que
ese contrato solo se rellena para **proponer** o **auditar** un cambio visual,
no para escribir una página. El detalle está en `captia-design-contract.md`.

La sección `experience` de `docs.config.json` expresa políticas leídas por el
agente; no activa configuraciones Docusaurus ni verificación automática. Los
helpers no interpretan el contrato visual ni prueban fidelidad de marca.
Registrar evidencias visuales con la plantilla de QA, no con una bandera `true`
sin comprobaciones.
