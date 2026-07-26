"""Funciones de extraccion: listar y descargar anotaciones XML desde S3 (raw/)."""
from typing import List

import boto3

s3 = boto3.client("s3")


def list_xml_keys(bucket: str, prefix: str) -> List[str]:
    """Devuelve la lista de keys de S3 que terminan en .xml dentro de un prefix."""
    keys = []
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            if obj["Key"].lower().endswith(".xml"):
                keys.append(obj["Key"])
    return keys


def download_xml(bucket: str, key: str) -> bytes:
    """Descarga el contenido crudo de un XML desde S3."""
    return s3.get_object(Bucket=bucket, Key=key)["Body"].read()