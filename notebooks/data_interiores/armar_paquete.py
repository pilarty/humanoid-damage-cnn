"""
Arma el paquete de fotos de interiores para el entrenamiento v4 del detector.

A partir de las fotos bajadas por elegir_y_bajar.py genera:
    paquete/interiores/<id>.jpg            foto completa (toma amplia)
    paquete/interiores_cerca/<id>_cN.jpg   recortes de cerca de la misma foto
    paquete/fotos_interiores.csv           autor y licencia de cada foto
y lo comprime en paquete_interiores.zip.

Los recortes existen para que el modelo vea paredes, puertas y muebles sanos
tambien de cerca, y no asocie "toma de cerca" con "daño".

Uso (desde notebooks/data_interiores):
    python armar_paquete.py
"""
import csv
import os
import shutil

import numpy as np
from PIL import Image

AQUI = os.path.dirname(os.path.abspath(__file__))
RECORTES_POR_FOTO = 2


def main():
    paquete = os.path.join(AQUI, "paquete")
    if os.path.isdir(paquete):
        shutil.rmtree(paquete)
    os.makedirs(os.path.join(paquete, "interiores"))
    os.makedirs(os.path.join(paquete, "interiores_cerca"))
    with open(os.path.join(AQUI, "fotos_interiores.csv"), encoding="utf-8") as f:
        filas = list(csv.DictReader(f))
    rng = np.random.default_rng(0)
    amplias = cerca = 0
    for fila in filas:
        origen = os.path.join(AQUI, "fotos", fila["id"] + ".jpg")
        if not os.path.exists(origen):
            continue
        img = Image.open(origen).convert("RGB")
        w, h = img.size
        if min(w, h) < 200:
            continue
        img.save(os.path.join(paquete, "interiores", fila["id"] + ".jpg"), quality=90)
        amplias += 1
        for n in range(RECORTES_POR_FOTO):
            lado = int(min(w, h) * rng.uniform(0.30, 0.50))
            x, y = int(rng.integers(0, w - lado + 1)), int(rng.integers(0, h - lado + 1))
            recorte = img.crop((x, y, x + lado, y + lado)).resize((320, 320), Image.LANCZOS)
            recorte.save(os.path.join(paquete, "interiores_cerca", f"{fila['id']}_c{n + 1}.jpg"), quality=90)
            cerca += 1
    shutil.copy(os.path.join(AQUI, "fotos_interiores.csv"), os.path.join(paquete, "fotos_interiores.csv"))
    shutil.make_archive(os.path.join(AQUI, "paquete_interiores"), "zip", paquete)
    peso = os.path.getsize(os.path.join(AQUI, "paquete_interiores.zip")) / 1e6
    print(f"interiores: {amplias} | interiores_cerca: {cerca} | paquete_interiores.zip: {peso:.0f} MB")


if __name__ == "__main__":
    main()
