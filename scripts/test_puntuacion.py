#!/usr/bin/env python3
"""Pruebas del programa de puntuación genérico (`static/plantillas/puntuacion/`).

    python scripts/test_puntuacion.py

Ese programa no lo ejecuta nadie en este repositorio: lo descarga un docente, lo sube a
Codabench y allí puntúa los envíos de sus alumnos. Si se rompe, el build del sitio sigue en
verde y el fallo aparece semanas después, como un envío que no puntúa en una competición
ajena. Estas pruebas son lo único que lo ve antes.

Se ejecuta el programa como lo hace Codabench —en un proceso aparte, con `$input` y
`$output`— y no importándolo, porque lo que importa es el contrato: qué lee, de dónde, qué
escribe y con qué mensaje falla. Los datos son sintéticos (AULA01, AULA02…): el repositorio
es público.
"""

from __future__ import annotations

import ast
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PROGRAMA = REPO / "static" / "plantillas" / "puntuacion"
KIT = REPO / "static" / "plantillas" / "kit"


class Competicion:
    """Un árbol como el que monta Codabench: programa, input/ref, input/res y output."""

    def __init__(self, config: dict | None):
        self.raiz = Path(tempfile.mkdtemp(prefix="puntuacion-"))
        self.programa = self.raiz / "program"
        self.programa.mkdir()
        shutil.copy(PROGRAMA / "score.py", self.programa / "score.py")
        if config is not None:
            (self.programa / "config.json").write_text(json.dumps(config), encoding="utf-8")
        self.ref = self.raiz / "input" / "ref"
        self.res = self.raiz / "input" / "res"
        self.ref.mkdir(parents=True)
        self.res.mkdir(parents=True)
        self.salida = self.raiz / "output"

    def escribir(self, carpeta: Path, nombre: str, texto: str, codificacion="utf-8") -> None:
        (carpeta / nombre).write_bytes(texto.encode(codificacion))

    def puntuar(self) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(self.programa / "score.py"), str(self.raiz / "input"), str(self.salida)],
            capture_output=True,
        )

    def notas(self) -> dict:
        proceso = self.puntuar()
        if proceso.returncode != 0:
            raise AssertionError(proceso.stderr.decode("utf-8", "replace"))
        return json.loads((self.salida / "scores.json").read_text(encoding="utf-8"))

    def fallo(self) -> str:
        """El mensaje de error. Falla la prueba si el programa NO falla."""
        proceso = self.puntuar()
        if proceso.returncode == 0:
            raise AssertionError("se esperaba un error y puntuó: " + proceso.stdout.decode())
        if (self.salida / "scores.json").exists():
            raise AssertionError("falló pero dejó un scores.json")
        return proceso.stderr.decode("utf-8")

    def limpiar(self) -> None:
        shutil.rmtree(self.raiz, ignore_errors=True)


NUMERO = {"columna": "personas", "tipo": "numero"}
CATEGORIA = {"columna": "calidad", "tipo": "categoria"}

SOLUCION_NUM = "id,personas\nAULA01_202602100800,10\nAULA01_202602100900,20\nAULA02_202602100800,0\n"
SOLUCION_CAT = (
    "id,calidad\n"
    "AULA01_1,buena\nAULA01_2,buena\nAULA01_3,aceptable\n"
    "AULA02_1,deficiente\nAULA02_2,buena\nAULA02_3,aceptable\n"
)


class PruebasNumero(unittest.TestCase):
    def setUp(self):
        self.c = Competicion(NUMERO)
        self.addCleanup(self.c.limpiar)
        self.c.escribir(self.c.ref, "solution.csv", SOLUCION_NUM)

    def test_mae_y_rmse(self):
        # Errores 2, -4 y 3: MAE = 9/3 = 3; RMSE = sqrt((4 + 16 + 9) / 3) = 3.1091
        self.c.escribir(
            self.c.res,
            "submission.csv",
            "id,personas\nAULA02_202602100800,3\nAULA01_202602100800,12\nAULA01_202602100900,16.0\n",
        )
        self.assertEqual(self.c.notas(), {"mae": 3.0, "rmse": 3.1091, "n": 3})

    def test_empareja_por_id_y_no_por_orden(self):
        self.c.escribir(
            self.c.res,
            "submission.csv",
            "personas,id\n0,AULA02_202602100800\n20,AULA01_202602100900\n10,AULA01_202602100800\n",
        )
        self.assertEqual(self.c.notas(), {"mae": 0.0, "rmse": 0.0, "n": 3})

    def test_faltan_ids(self):
        self.c.escribir(self.c.res, "submission.csv", "id,personas\nAULA01_202602100800,10\n")
        self.assertIn("le faltan 2 de los 3 ids", self.c.fallo())

    def test_sobran_ids(self):
        self.c.escribir(
            self.c.res,
            "submission.csv",
            "id,personas\nAULA01_202602100800,1\nAULA01_202602100900,1\n"
            "AULA02_202602100800,1\nAULA09_202602100800,1\n",
        )
        self.assertIn("AULA09_202602100800", self.c.fallo())

    def test_ids_repetidos(self):
        self.c.escribir(
            self.c.res,
            "submission.csv",
            "id,personas\nAULA01_202602100800,1\nAULA01_202602100800,2\n",
        )
        self.assertIn("repetido", self.c.fallo())

    def test_falta_la_columna(self):
        self.c.escribir(self.c.res, "submission.csv", "id,prediccion\nAULA01_202602100800,1\n")
        mensaje = self.c.fallo()
        self.assertIn("le falta la columna 'personas'", mensaje)
        self.assertIn("el envío", mensaje)

    def test_valor_no_numerico(self):
        self.c.escribir(
            self.c.res,
            "submission.csv",
            'id,personas\nAULA01_202602100800,"3,5"\nAULA01_202602100900,1\nAULA02_202602100800,1\n',
        )
        mensaje = self.c.fallo()
        self.assertIn("'3,5' no es un número", mensaje)
        self.assertIn("punto como separador decimal", mensaje)

    def test_nan_no_es_un_numero(self):
        self.c.escribir(
            self.c.res,
            "submission.csv",
            "id,personas\nAULA01_202602100800,nan\nAULA01_202602100900,1\nAULA02_202602100800,1\n",
        )
        self.assertIn("no es un número", self.c.fallo())

    def test_punto_y_coma(self):
        self.c.escribir(self.c.res, "submission.csv", "id;personas\nAULA01_202602100800;10\n")
        self.assertIn("punto y coma", self.c.fallo())

    def test_no_utf8(self):
        self.c.escribir(
            self.c.res, "submission.csv", "id,personas,nota\nAULA01_202602100800,10,año\n", "latin-1"
        )
        self.assertIn("no está en UTF-8", self.c.fallo())

    def test_bom_de_excel(self):
        self.c.escribir(
            self.c.res,
            "submission.csv",
            "﻿id,personas\nAULA01_202602100800,10\nAULA01_202602100900,20\nAULA02_202602100800,0\n",
        )
        self.assertEqual(self.c.notas()["mae"], 0.0)

    def test_prefiere_submission_si_hay_varios(self):
        self.c.escribir(self.c.res, "a_notas.csv", "otra,cosa\n1,2\n")
        self.c.escribir(
            self.c.res,
            "submission.csv",
            "id,personas\nAULA01_202602100800,10\nAULA01_202602100900,20\nAULA02_202602100800,0\n",
        )
        self.assertEqual(self.c.notas()["n"], 3)

    def test_prefiere_solution_si_hay_varios(self):
        self.c.escribir(self.c.ref, "a_otra.csv", "id,personas\nX,1\n")
        self.c.escribir(
            self.c.res,
            "submission.csv",
            "id,personas\nAULA01_202602100800,10\nAULA01_202602100900,20\nAULA02_202602100800,0\n",
        )
        self.assertEqual(self.c.notas()["n"], 3)

    def test_sin_csv_en_el_envio(self):
        self.assertIn("no hay ningún fichero .csv", self.c.fallo())


class PruebasCategoria(unittest.TestCase):
    def setUp(self):
        self.c = Competicion(CATEGORIA)
        self.addCleanup(self.c.limpiar)
        self.c.escribir(self.c.ref, "solution.csv", SOLUCION_CAT)

    def test_aciertos_y_f1_macro(self):
        # Real: buena, buena, aceptable, deficiente, buena, aceptable
        # Pred: buena, aceptable, aceptable, buena, buena, aceptable  -> 4 de 6
        # buena:      vp=2 fp=1 fn=1 -> p=2/3 r=2/3 f1=2/3
        # aceptable:  vp=2 fp=1 fn=0 -> p=2/3 r=1   f1=0.8
        # deficiente: vp=0 fp=0 fn=1 -> f1=0
        # F1 macro = (2/3 + 0.8 + 0) / 3 = 0.4889
        self.c.escribir(
            self.c.res,
            "submission.csv",
            "id,calidad\nAULA01_1,buena\nAULA01_2,aceptable\nAULA01_3,aceptable\n"
            "AULA02_1,buena\nAULA02_2,buena\nAULA02_3,aceptable\n",
        )
        self.assertEqual(self.c.notas(), {"aciertos": 0.6667, "f1": 0.4889, "n": 6})

    def test_clase_que_no_esta_en_la_solucion(self):
        # «regular» no está en la solución: no suma una clase al promedio, pero sí es fallo.
        self.c.escribir(
            self.c.res,
            "submission.csv",
            "id,calidad\nAULA01_1,regular\nAULA01_2,buena\nAULA01_3,aceptable\n"
            "AULA02_1,deficiente\nAULA02_2,buena\nAULA02_3,aceptable\n",
        )
        notas = self.c.notas()
        self.assertEqual(notas["aciertos"], 0.8333)
        # buena: vp=2 fp=0 fn=1 -> f1=0.8; aceptable y deficiente: 1 -> (0.8+1+1)/3
        self.assertEqual(notas["f1"], 0.9333)

    def test_prediccion_vacia(self):
        self.c.escribir(
            self.c.res,
            "submission.csv",
            "id,calidad\nAULA01_1,\nAULA01_2,buena\nAULA01_3,aceptable\n"
            "AULA02_1,deficiente\nAULA02_2,buena\nAULA02_3,aceptable\n",
        )
        self.assertIn("falta la predicción", self.c.fallo())


class PruebasConfig(unittest.TestCase):
    def test_sin_config(self):
        c = Competicion(None)
        self.addCleanup(c.limpiar)
        self.assertIn("falta config.json", c.fallo())

    def test_tipo_desconocido(self):
        c = Competicion({"columna": "personas", "tipo": "regresion"})
        self.addCleanup(c.limpiar)
        self.assertIn('"tipo" tiene que ser', c.fallo())

    def test_columna_de_id_propia(self):
        c = Competicion({"columna": "personas", "tipo": "numero", "id": "franja"})
        self.addCleanup(c.limpiar)
        c.escribir(c.ref, "solution.csv", "franja,personas\nF1,4\nF2,6\n")
        c.escribir(c.res, "submission.csv", "franja,personas\nF1,5\nF2,6\n")
        self.assertEqual(c.notas(), {"mae": 0.5, "rmse": 0.7071, "n": 2})


class PruebasFicheros(unittest.TestCase):
    """El zip que se sube a Codabench: lo que lleva y en qué versión de Python corre."""

    def test_metadata_con_command(self):
        texto = (PROGRAMA / "metadata").read_text(encoding="utf-8")
        self.assertEqual(texto.strip(), "command: python3 $program/score.py $input $output")

    def test_config_de_ejemplo_valida(self):
        config = json.loads((PROGRAMA / "config.json").read_text(encoding="utf-8"))
        self.assertIn(config["tipo"], ("numero", "categoria"))
        self.assertTrue(config["columna"])

    def test_sintaxis_de_python_37(self):
        # La imagen por defecto de Codabench es Python 3.7. Aquí no se puede ejecutar con
        # 3.7, pero sí rechazar la sintaxis posterior (`:=`, `match`, `/` en parámetros…).
        # Las funciones nuevas de la biblioteca estándar no las caza esto: se evitan a mano.
        # Los scripts del kit de inicio corren en el ordenador del participante, que puede
        # tener un Python viejo: se les pide lo mismo. Lo que hacen lo prueba
        # scripts/preparar.test.mjs, que los ejecuta sobre unos ficheros generados.
        for ruta in [PROGRAMA / "score.py", *sorted(KIT.glob("*.py"))]:
            with self.subTest(ruta.name):
                ast.parse(ruta.read_text(encoding="utf-8"), feature_version=(3, 7))

    def test_finales_de_linea_lf(self):
        for ruta in [*sorted(PROGRAMA.iterdir()), *sorted(KIT.iterdir())]:
            self.assertNotIn(b"\r\n", ruta.read_bytes(), ruta.name)


if __name__ == "__main__":
    unittest.main(verbosity=2)
