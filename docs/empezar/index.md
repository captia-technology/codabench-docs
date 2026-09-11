---
title: "Antes de empezar"
description: "Saber qué cubre esta guía, por qué recorre el editor web en vez del bundle YAML, y en qué orden se montan las piezas de una competición."
---

# Antes de empezar

**Objetivo:** saber qué cubre esta guía, por qué recorre el editor web en vez del bundle YAML, y en qué orden se montan las piezas de una competición.

Guía de referencia para publicar un benchmark/competición en [Codabench](https://www.codabench.org/) usando el **editor web** (formularios, sin escribir `competition.yaml` a mano ni subir un bundle `.zip` completo). Es el flujo recomendado para crear y mantener una competición directamente desde la interfaz.

:::note[El bundle YAML es otro camino, y no es este]
Codabench también admite crear la competición subiendo un bundle `.zip` con un `competition.yaml` (útil para versionar en un repo). Esta guía no cubre ese método — ver [fuentes y documentación oficial](../referencia/fuentes.md) si se necesita en el futuro.
:::

## El recorrido completo

Las seis secciones siguen el orden en que se monta una competición, y ese orden no admite atajos: una Task no puede referenciar un Dataset o un Program que todavía no se ha subido, y una Phase no puede asignar una Task que todavía no existe.

1. **Antes de empezar** — esta sección: los [conceptos clave](./conceptos.md) con los que se construye una competición, [la competición de ejemplo](./ejemplo.md) que sirve de hilo conductor, y los [requisitos previos](./requisitos.md) que hay que tener listos antes de abrir el editor.
2. **[Crear la competición](../competicion/index.md)** — las pestañas que definen la competición en sí: **Details**, **Participation**, **Pages** y **Collaborators**.
3. **[Recursos y tasks](../recursos/index.md)** — subir los Datasets y Programs y combinarlos en la Task que evaluará las submissions.
4. **[Fases y evaluación](../evaluacion/index.md)** — las **Phases** con sus fechas y límites, los **Leaderboards** con sus columnas, y la regla que decide qué submission de cada participante se muestra.
5. **[Submissions](../submissions/index.md)** — el formato exacto que se le pide al participante y cómo probar la competición de extremo a extremo antes de abrirla.
6. **[Referencia](../referencia/index.md)** — los síntomas más frecuentes con su causa probable, y las fuentes oficiales en las que se apoya la guía.
