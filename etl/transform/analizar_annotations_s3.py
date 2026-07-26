import argparse
import os
import sys
from collections import Counter
from pathlib import Path
from typing import Iterator, List, Tuple
import xml.etree.ElementTree as ET

import boto3
from botocore.exceptions import BotoCoreError, ClientError

DEFAULT_S3_URI = "s3://humanoid-damage-cnn-834257582282-us-east-1-an/raw/IDEA/damages/annotations/"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Lee annotations XML desde S3 o desde un directorio local y resume los tipos de daño detectados."
    )
    parser.add_argument(
        "source",
        nargs="?",
        default=DEFAULT_S3_URI,
        help=f"Ruta de entrada (por defecto: {DEFAULT_S3_URI})",
    )
    parser.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Formato de salida",
    )
    return parser.parse_args()


def iter_annotation_files(source: str) -> Iterator[Tuple[str, bytes]]:
    if source.startswith("s3://"):
        bucket, prefix = parse_s3_uri(source)
        yield from iter_s3_annotation_files(bucket, prefix)
        return

    local_path = Path(source)
    if not local_path.exists():
        raise FileNotFoundError(f"No existe la ruta local: {source}")

    for path in sorted(local_path.rglob("*.xml")):
        if path.is_file():
            yield str(path), path.read_bytes()


def parse_s3_uri(s3_uri: str) -> Tuple[str, str]:
    if not s3_uri.startswith("s3://"):
        raise ValueError(f"URI inválida: {s3_uri}")

    without_prefix = s3_uri[len("s3://") :]
    bucket, _, prefix = without_prefix.partition("/")
    if not bucket:
        raise ValueError(f"No se pudo obtener el bucket de: {s3_uri}")
    return bucket, prefix or ""


def iter_s3_annotation_files(bucket: str, prefix: str) -> Iterator[Tuple[str, bytes]]:
    s3 = boto3.client("s3")

    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if key.lower().endswith(".xml"):
                response = s3.get_object(Bucket=bucket, Key=key)
                yield key, response["Body"].read()


def extract_damage_types(xml_bytes: bytes) -> List[str]:
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


def resumir_tipos_de_dano(source: str) -> dict:
    counts = Counter()
    archivos = 0

    for path, xml_bytes in iter_annotation_files(source):
        archivos += 1
        for damage_type in extract_damage_types(xml_bytes):
            counts[damage_type] += 1

    return {
        "source": source,
        "archivos_procesados": archivos,
        "tipos_de_dano": dict(counts.most_common()),
    }


def print_text_summary(summary: dict) -> None:
    print(f"Fuente: {summary['source']}")
    print(f"Archivos procesados: {summary['archivos_procesados']}")
    print("Tipos de daño encontrados:")

    if not summary["tipos_de_dano"]:
        print("- (no se encontraron tipos de daño en las annotations)")
        return

    for damage_type, count in summary["tipos_de_dano"].items():
        print(f"- {damage_type}: {count}")


def main() -> int:
    args = parse_args()

    try:
        summary = resumir_tipos_de_dano(args.source)
    except (BotoCoreError, ClientError, FileNotFoundError, ValueError, ET.ParseError) as exc:
        print(f"Error al procesar las annotations: {exc}", file=sys.stderr)
        return 1

    if args.output == "json":
        import json

        print(json.dumps(summary, indent=2, ensure_ascii=False))
    else:
        print_text_summary(summary)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
