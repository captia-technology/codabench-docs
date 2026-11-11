#!/usr/bin/env python3
"""Comprime submission.csv en submission.zip, con el CSV en la raíz del zip.

Es lo que pide Codabench: un zip con el CSV dentro de una carpeta no puntúa.

Uso:  python hacer_envio_zip.py [submission.csv]
"""

import sys
import zipfile
from pathlib import Path


def main():
    origen = Path(sys.argv[1] if len(sys.argv) > 1 else "submission.csv")
    if not origen.is_file():
        sys.exit("ERROR: no existe {}".format(origen))
    with zipfile.ZipFile("submission.zip", "w", zipfile.ZIP_DEFLATED) as z:
        z.write(str(origen), arcname=origen.name)
    print("submission.zip escrito, con {} en la raíz. Súbelo en My Submissions".format(origen.name))


if __name__ == "__main__":
    main()
