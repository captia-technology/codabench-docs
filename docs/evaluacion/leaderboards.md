---
title: "Leaderboards"
description: "Montar la tabla de resultados de la competición y conseguir que sus columnas se rellenen con las métricas que devuelve el scoring program."
sidebar_position: 2
---

# Leaderboards

**Objetivo:** montar la tabla de resultados de la competición y conseguir que sus columnas se rellenen con las métricas que devuelve el scoring program.

## Crear el leaderboard y sus columnas

Pestaña **Leaderboards**:

1. Crear un leaderboard: **Title** y **Key**, los dos obligatorios. La ayuda del propio campo explica para qué sirve la clave: es la que el scoring program usa para asignar puntuaciones a este leaderboard. Preferiblemente en minúsculas.
2. **Leaderboard is Hidden** deja la tabla montada pero invisible para los participantes. Sirve para preparar una fase final sin enseñar los resultados mientras tanto.
3. **Submission Rule**: qué submission de cada participante ocupa su fila. Son [seis reglas](./submission-rule.md) y la elección cambia si el participante tiene que hacer algo o no.
4. Añadir columnas, una por cada métrica que devuelva el scoring program:

| Campo | Qué hace |
|---|---|
| **Title** | Nombre visible de la columna. |
| **Column Key** | Obligatorio. Debe coincidir *exactamente* con la clave que el scoring program escribe en `scores.txt` (ver más abajo). |
| **Column Precision** | Obligatorio. Decimales con los que se muestra el valor, de 1 a 10; por defecto **2**. No redondea el score guardado, solo cómo se presenta — y también gobierna el que se ve en el panel de la submission. |
| **Sorting** | `Descending` o `Ascending`. La ayuda del campo lo resume: ascendente significa que menor es mejor, descendente que mayor es mejor. |
| **Primary Column** | Marca la columna principal de ranking. Es la que ordena la tabla y la que se muestra como puntuación de la submission. |
| **Hidden** | Oculta esa columna concreta a los participantes sin dejar de calcularla. |
| **Computation** | Cómo se calcula la columna. Ver abajo. |

## Las columnas calculadas

`Computation` admite **seis** valores: `None`, `Average`, `Sum`, `Min`, `Max` y `Average Rank`. Con `None` —lo normal— la columna recibe su valor directamente del scoring program, por su `Column Key`.

Con cualquiera de las otras cinco, la columna **no** recibe score del scoring program: se calcula a partir de otras columnas. Al elegir una aparece un segundo desplegable, **Apply to:**, donde se marcan las columnas que entran en el cálculo.

:::tip[`Average Rank` no es la media de los valores]
`Average`, `Sum`, `Min` y `Max` operan sobre los valores de esa fila. **`Average Rank` opera sobre la tabla entera**: calcula la posición de cada submission en cada una de las columnas seleccionadas y promedia esas posiciones. Por eso su valor cambia cuando otro participante añade o quita una submission, aunque la propia no se haya tocado.

Es útil cuando las métricas tienen escalas distintas y promediarlas sin más daría un número sin sentido. Está disponible desde **Codabench v1.29**.
:::

En el [ejemplo](../empezar/ejemplo.md) son dos columnas: `f1_macro`, marcada como **Primary Column** porque es la que ordena la tabla, y `accuracy` al lado como referencia. Las dos con `Computation` en `None`: las calcula el scoring program y llegan ya hechas.

## El fichero `scores.txt`

El scoring program debe escribir un `scores.txt` con líneas `clave: valor`, por ejemplo:

```
accuracy: 0.8721
f1_score: 0.8390
```

:::warning[La Column Key tiene que ser literal]
Si la `Column Key` no coincide con la clave de `scores.txt`, la columna aparece vacía en el leaderboard sin error explícito — es el fallo más frecuente al montar el leaderboard.
:::

## Antes de la primera submission

Mientras no haya ninguna submission añadida al leaderboard, la pestaña **Results** muestra "No visible leaderboard for this benchmark" — es el estado normal antes de la primera submission válida, no un error de configuración.

**Siguiente paso:** [Submission rule](./submission-rule.md) — cuál de las submissions de cada participante ocupa su fila en esta tabla.
