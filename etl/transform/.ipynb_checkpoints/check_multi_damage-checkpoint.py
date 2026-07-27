import argparse
import sys
from collections import Counter
from pathlib import Path
from typing import Iterator, Tuple
import xml.etree.ElementTree as ET
import boto3
from botocore.exceptions import BotoCoreError, ClientError

DEFAULT_S3_URI = "s3://humanoid-damage-cnn-834257582282-us-east-1-an/raw/IDEA/damages/annotations/"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verifica si cada XML tiene uno o varios tipos de daño distintos."
    )
    parser.add_argument(
        "source",
        nargs="?",
        default=DEFAULT_S3_URI,
        help=f"Ruta de entrada (por defecto: {DEFAULT_S3_URI})",
    )
    parser.add_argument(
        "--solo-multiples",
        action="store_true",
        help="Mostrar detalle solo de los archivos que tienen más de un tipo de daño",
    )
    parser.add_argument(
        "--detalle",
        action="store_true",
        help="Mostrar el detalle por archivo (por defecto solo se muestra el resumen general)",
    )
    return parser.parse_args()


def parse_s3_uri(s3_uri: str) -> Tuple[str, str]:
    without_prefix = s3_uri[len("s3://"):]
    bucket, _, prefix = without_prefix.partition("/")
    return bucket, prefix or ""


def iter_annotation_files(source: str) -> Iterator[Tuple[str, bytes]]:
    if source.startswith("s3://"):
        bucket, prefix = parse_s3_uri(source)
        s3 = boto3.client("s3")
        paginator = s3.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
            for obj in page.get("Contents", []):
                key = obj["Key"]
                if key.lower().endswith(".xml"):
                    response = s3.get_object(Bucket=bucket, Key=key)
                    yield key, response["Body"].read()
        return
    local_path = Path(source)
    for path in sorted(local_path.rglob("*.xml")):
        if path.is_file():
            yield str(path), path.read_bytes()


def extract_damage_types(xml_bytes: bytes) -> list:
    root = ET.fromstring(xml_bytes)
    tipos = []
    for elem in root.iter("name"):
        damage_value = elem.attrib.get("damage")
        if damage_value:
            tipos.append(damage_value.strip())
            continue
        text_value = (elem.text or "").strip()
        if text_value:
            tipos.append(text_value)
    return tipos


def main() -> int:
    args = parse_args()
    total_archivos = 0
    distribucion = Counter()  # cantidad_de_tipos_distintos -> cantidad_de_archivos

    try:
        for path, xml_bytes in iter_annotation_files(args.source):
            total_archivos += 1
            try:
                tipos = extract_damage_types(xml_bytes)
            except ET.ParseError as exc:
                print(f"[ERROR parseo] {path}: {exc}", file=sys.stderr)
                continue

            tipos_unicos = sorted(set(tipos))
            cantidad = len(tipos_unicos)
            distribucion[cantidad] += 1

            if args.detalle:
                if args.solo_multiples and cantidad <= 1:
                    pass
                elif cantidad == 0:
                    print(f"{path}: sin tipos de daño")
                else:
                    print(f"{path}: {cantidad} tipo(s) -> {tipos_unicos}")
    except (BotoCoreError, ClientError, FileNotFoundError, ValueError) as exc:
        print(f"Error al procesar las annotations: {exc}", file=sys.stderr)
        return 1

    print("\n--- Resumen general ---")
    print(f"Archivos procesados: {total_archivos}")
    for cantidad in sorted(distribucion):
        etiqueta = "tipo de daño" if cantidad == 1 else "tipos de daño"
        if cantidad == 0:
            print(f"Archivos sin tipos de daño: {distribucion[cantidad]}")
        else:
            print(f"Archivos con {cantidad} {etiqueta}: {distribucion[cantidad]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())