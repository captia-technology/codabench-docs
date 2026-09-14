# Auditoría de las capturas — 2026-09-14

Las diez capturas de `docs/**` salen de una competición **real**, montada sobre `codabench.org`
por la cuenta de organizador de CAPTIA. No son maquetas ni una instancia de pruebas: es la
pantalla que ve quien monta una competición, con sus datos dentro.

Eso obliga a una pasada de anonimización antes de publicarlas, y este documento la registra.

## La diferencia con el manual de captia.ai, y por qué importa

El manual de captia.ai tiene un documento equivalente que **guarda los datos reales retirados de
las capturas**, para poder rehacerlas. Puede hacerlo porque aquel repositorio es privado.

**Aquí no.** Este repositorio es público, así que un documento con los datos retirados sería
exactamente la filtración que la anonimización evita. Lo que sigue registra **qué clase de dato**
se retiró y **cómo**; ninguno de los valores originales aparece, ni debe aparecer nunca.

## Qué se retiró

| Clase de dato | Dónde aparecía | Con qué se sustituyó |
|---|---|---|
| Nombre del centro educativo | Título de la competición, en cinco capturas | `IES Ejemplo` |
| URL firmada de S3 del logo | Pestaña Details: el enlace llevaba `AWSAccessKeyId` y `Signature` | `logo-de-la-competicion.png` |
| Correo de contacto | Página de error de la plataforma | `organizador@ejemplo.com` |

La segunda es la que casi se cuela, y merece quedar escrita: **el enlace del logo que Codabench
muestra en la pestaña Details es una URL firmada**, con clave de acceso y firma en la propia
cadena. Caduca, sí, pero se publicaba entera y legible. No se vio leyendo la captura por encima:
se vio al leer el texto de la página antes de guardarla.

## Cómo se hizo

La sustitución se aplicó **sobre el DOM, antes de capturar**, recorriendo los nodos de texto y los
valores de los campos de formulario. No se editaron las imágenes después.

Es deliberado, y tiene una ventaja sobre pixelar o recortar: lo que se publica es una pantalla
coherente —la interfaz completa, con un nombre distinto— en vez de una imagen con manchas negras
que obligan al lector a adivinar qué había debajo. Y tiene un riesgo que hay que conocer: si la
lista de sustituciones se queda corta, el dato sale publicado sin que nada avise. Por eso la
comprobación final no fue automática, sino leer las diez capturas una por una.

## Lo que las capturas NO ocultan, a propósito

Sigue visible, y está bien que lo esté, porque describe la competición y no a nadie:

- El nombre y la versión del reto, los nombres de los recursos y de la Task.
- Las claves de las métricas (`macro_f1`, `accuracy`), la precisión y la submission rule.
- Los límites de la fase, la cuota consumida y la descripción técnica del dataset.
- El nombre de usuario de la organización (`captia`), que es quien publica la guía.

## Al rehacer una captura

1. Iniciar sesión **a mano**: quien captura introduce sus credenciales, nunca un agente.
2. Aplicar la anonimización antes de disparar, no después.
3. **Leer el texto de la pantalla** buscando URLs firmadas, correos y nombres propios — no fiarse
   de mirar la imagen.
4. Comprobar que la captura nueva sigue ilustrando lo que dice su pie, que a menudo señala un
   detalle concreto («la columna Public sin marcar»).
5. Si una captura deja de usarse, **borrarla**: `scripts/check_docs.py` falla con las huérfanas.
