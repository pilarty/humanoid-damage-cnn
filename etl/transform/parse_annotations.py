"""Funciones de transformacion: parsear XML (Pascal VOC-like) a los formatos
que necesita cada modelo, y armar el split train/val/test."""
import xml.etree.ElementTree as ET
from pathlib import PurePosixPath
from typing import Dict


def parse_binary_annotation(xml_bytes: bytes) -> Dict:
    """Parsea un XML para el modelo 1 (damaged/undamaged).

    Devuelve: {"image_basename": str, "is_damaged": bool}
    """
    root = ET.fromstring(xml_bytes)

    filename_tag = root.findtext("filename", default="").strip()
    image_basename = PurePosixPath(filename_tag).name if filename_tag else None

    damage_presence = (root.findtext("damagePresence", default="") or "").strip().lower()
    has_objects = root.find("object") is not None

    if not damage_presence:
        damage_presence = "damage" if has_objects else "no damage"

    is_damaged = "no" not in damage_presence  # "damage" -> True, "no damage" -> False

    return {"image_basename": image_basename, "is_damaged": is_damaged}


def parse_yolo_annotation(xml_bytes: bytes) -> Dict:
    """Parsea un XML para el modelo 2 (tipo de dano + ubicacion).

    Devuelve: {"image_basename": str, "width": int, "height": int,
               "objects": [{"damage_type": str, "xmin": float, "ymin": float,
                             "xmax": float, "ymax": float}, ...]}
    """
    root = ET.fromstring(xml_bytes)

    filename_tag = root.findtext("filename", default="").strip()
    image_basename = PurePosixPath(filename_tag).name if filename_tag else None

    size_elem = root.find("size")
    width = int(size_elem.findtext("width")) if size_elem is not None else None
    height = int(size_elem.findtext("height")) if size_elem is not None else None

    objects = []
    for obj in root.findall("object"):
        name_elem = obj.find("name")
        if name_elem is None:
            continue
        damage_type = name_elem.attrib.get("damage") or (name_elem.text or "").strip()
        if not damage_type:
            continue
        bndbox = obj.find("bndbox")
        if bndbox is None:
            continue
        objects.append({
            "damage_type": damage_type.strip(),
            "xmin": float(bndbox.findtext("xmin")),
            "ymin": float(bndbox.findtext("ymin")),
            "xmax": float(bndbox.findtext("xmax")),
            "ymax": float(bndbox.findtext("ymax")),
        })

    return {"image_basename": image_basename, "width": width, "height": height, "objects": objects}


def to_yolo_line(obj: Dict, class_to_id: Dict[str, int], width: int, height: int) -> str:
    """Convierte un objeto (daño con bndbox en pixeles) a una linea de formato YOLO normalizada."""
    class_id = class_to_id[obj["damage_type"]]
    x_center = ((obj["xmin"] + obj["xmax"]) / 2) / width
    y_center = ((obj["ymin"] + obj["ymax"]) / 2) / height
    box_width = (obj["xmax"] - obj["xmin"]) / width
    box_height = (obj["ymax"] - obj["ymin"]) / height
    return f"{class_id} {x_center:.6f} {y_center:.6f} {box_width:.6f} {box_height:.6f}"