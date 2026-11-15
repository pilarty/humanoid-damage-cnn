"""
Elige fotos reales de interiores de Open Images (sin personas) y las baja.

Open Images publica, para cada foto, sus etiquetas verificadas por humanos,
el autor y la licencia. Se eligen fotos con etiquetas de interior (pared,
habitacion, piso, puerta, muebles...) y se descartan las que tienen
personas, animales, comida o texto. Se guarda una lista con el autor y la
licencia de cada foto para poder citarlas.

Uso (desde notebooks/data_interiores):
    python elegir_y_bajar.py --cuantas 200

Salida: fotos/*.jpg y fotos_interiores.csv
Requiere los csv de meta/ (se bajan de storage.googleapis.com/openimages).
"""
import argparse
import csv
import io
import os
import random
from concurrent.futures import ThreadPoolExecutor

import requests
from PIL import Image

AQUI = os.path.dirname(os.path.abspath(__file__))
META = os.path.join(AQUI, "meta")
SALAS = {"Room", "Living room", "Bedroom", "Office", "Classroom", "Kitchen", "Bathroom", "Dining room", "Lobby",
         "Hall", "Interior design"}
PARTES = {"Wall", "Floor", "Flooring", "Ceiling", "Door", "Furniture", "Plaster", "Stairs", "Table", "Chair"}
EXCLUIR = {"Person", "Human face", "Man", "Woman", "Girl", "Boy", "People", "Child", "Human body", "Human hair",
           "Face", "Clothing", "Animal", "Dog", "Cat", "Food", "Text", "Poster", "Art", "Painting", "Toy",
           "Vehicle", "Car", "Tree", "Sky", "Plant", "Flower", "Screenshot", "Drawing", "Illustration", "Graffiti",
           "Ruins", "Abandoned", "Rubble", "Demolition", "Construction", "Mold", "Rust", "Crowd", "Event", "Selfie"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cuantas", type=int, default=200)
    ap.add_argument("--semilla", type=int, default=0)
    args = ap.parse_args()

    with open(os.path.join(META, "oidv7-class-descriptions.csv"), encoding="utf-8") as f:
        nombre_de = {r[0]: r[1] for r in csv.reader(f)}

    candidatas = {}
    for parte in ("validation", "test"):
        etiquetas = {}
        with open(os.path.join(META, f"{parte}-annotations-human-imagelabels.csv"), encoding="utf-8") as f:
            for r in csv.DictReader(f):
                if r["Confidence"] == "1":
                    etiquetas.setdefault(r["ImageID"], set()).add(nombre_de.get(r["LabelName"], r["LabelName"]))
        with open(os.path.join(META, f"{parte}-images-with-rotation.csv"), encoding="utf-8") as f:
            for r in csv.DictReader(f):
                e = etiquetas.get(r["ImageID"], set())
                if e & EXCLUIR or not (e & SALAS) or len(e & (SALAS | PARTES)) < 2:
                    continue
                if "creativecommons.org/licenses/by/" not in r["License"]:
                    continue
                candidatas[r["ImageID"]] = dict(id=r["ImageID"], parte=parte, licencia=r["License"], autor=r["Author"],
                                               titulo=r["Title"], pagina=r["OriginalLandingURL"],
                                               etiquetas="|".join(sorted(e & (SALAS | PARTES))))
    print(f"fotos de interiores sin personas disponibles: {len(candidatas)}")

    random.seed(args.semilla)
    elegidas = random.sample(sorted(candidatas.values(), key=lambda c: c["id"]), min(args.cuantas, len(candidatas)))
    os.makedirs(os.path.join(AQUI, "fotos"), exist_ok=True)

    def bajar(c):
        destino = os.path.join(AQUI, "fotos", c["id"] + ".jpg")
        if os.path.exists(destino):
            return c
        try:
            url = f"https://open-images-dataset.s3.amazonaws.com/{c['parte']}/{c['id']}.jpg"
            img = Image.open(io.BytesIO(requests.get(url, timeout=60).content)).convert("RGB")
            img.thumbnail((640, 640))
            img.save(destino, quality=90)
            return c
        except Exception:
            return None

    with ThreadPoolExecutor(8) as ex:
        bajadas = [c for c in ex.map(bajar, elegidas) if c]
    with open(os.path.join(AQUI, "fotos_interiores.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(bajadas[0].keys()))
        w.writeheader()
        w.writerows(bajadas)
    print(f"bajadas: {len(bajadas)} fotos en {os.path.join(AQUI, 'fotos')}")


if __name__ == "__main__":
    main()
