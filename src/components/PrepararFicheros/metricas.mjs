/**
 * Las métricas de `static/plantillas/puntuacion/score.py`, en JavaScript.
 *
 * La herramienta calcula con ellas las notas de referencia que escribe en las instrucciones y
 * en el kit de inicio («si subes el envío de ejemplo, deberías obtener 3,3421»). Esa frase solo
 * es verdad si las cuentas son EXACTAMENTE las de score.py: mismo orden al sumar (el de la
 * solución), mismas operaciones y mismo redondeo. Cualquier cambio aquí o allí tiene que ir a
 * los dos sitios, y la prueba cruzada de scripts/preparar.test.mjs ejecuta score.py para
 * comprobarlo.
 */

/**
 * `round(x, 4)` de Python.
 *
 * `toFixed` y `round` solo discrepan en los empates exactos, cuando el valor binario cae justo
 * en la mitad: Python redondea al par y `toFixed` hacia arriba. A cuatro decimales, los únicos
 * números representables que caen en un empate son los múltiplos impares de 1/32 (0,03125,
 * 0,09375…), y una media de enteros entre 32 filas da uno de esos con facilidad.
 */
export function redondear4(x) {
  if (!Number.isFinite(x)) return x;
  const t = x * 32;
  if (Number.isInteger(t) && Math.abs(t) % 2 === 1) {
    const abajo = Math.floor(x * 1e4);
    const elegido = abajo % 2 === 0 ? abajo : abajo + 1;
    return elegido / 1e4;
  }
  return Number(x.toFixed(4));
}

/**
 * Puntúa unas predicciones contra la solución, como score.py.
 *
 * `solucion` es la lista ordenada de `[id, valor]` (el orden de solution.csv) y `prediccion`
 * un `Map` de id a valor. Números: `{ mae, rmse, n }`. Clases: `{ aciertos, f1, n }`, con el F1
 * macro sobre las clases presentes en la solución.
 */
export function puntuar(solucion, prediccion, tipo) {
  const n = solucion.length;
  if (tipo === 'numero') {
    let sumaAbs = 0;
    let sumaCuad = 0;
    for (const [id, valor] of solucion) {
      const diferencia = Number(prediccion.get(id)) - Number(valor);
      sumaAbs += Math.abs(diferencia);
      sumaCuad += diferencia * diferencia;
    }
    return { mae: redondear4(sumaAbs / n), rmse: redondear4(Math.sqrt(sumaCuad / n)), n };
  }
  const pares = solucion.map(([id, real]) => [String(real), String(prediccion.get(id))]);
  const aciertos = pares.filter(([real, pred]) => real === pred).length;
  // Mismo orden que `sorted()` de Python para texto sin caracteres fuera del plano básico.
  const clases = [...new Set(pares.map(([real]) => real))].sort();
  let sumaF1 = 0;
  for (const clase of clases) {
    let vp = 0;
    let fp = 0;
    let fn = 0;
    for (const [real, pred] of pares) {
      if (real === clase && pred === clase) vp++;
      else if (pred === clase) fp++;
      else if (real === clase) fn++;
    }
    const precision = vp + fp ? vp / (vp + fp) : 0;
    const exhaustividad = vp + fn ? vp / (vp + fn) : 0;
    if (precision + exhaustividad) {
      sumaF1 += (2 * precision * exhaustividad) / (precision + exhaustividad);
    }
  }
  return { aciertos: redondear4(aciertos / n), f1: redondear4(sumaF1 / clases.length), n };
}

/** Las columnas del leaderboard de cada tipo: clave, título, orden y si es la principal. */
export const COLUMNAS = {
  numero: [
    { clave: 'mae', titulo: 'MAE', orden: 'Ascending', principal: true, explicacion: 'error absoluto medio: cuanto más bajo, mejor' },
    { clave: 'rmse', titulo: 'RMSE', orden: 'Ascending', principal: false, explicacion: 'raíz del error cuadrático medio, que castiga más los errores grandes: cuanto más bajo, mejor' },
  ],
  categoria: [
    { clave: 'f1', titulo: 'F1 macro', orden: 'Descending', principal: true, explicacion: 'F1 macro, que pesa igual todas las clases: cuanto más alto, mejor' },
    { clave: 'aciertos', titulo: 'Aciertos', orden: 'Descending', principal: false, explicacion: 'proporción de filas acertadas, de 0 a 1: cuanto más alto, mejor' },
  ],
};

/** Un número con coma decimal, como se escribe en español. */
export function formatoDecimal(x, decimales = 4) {
  return redondear4(x).toFixed(decimales).replace('.', ',');
}
