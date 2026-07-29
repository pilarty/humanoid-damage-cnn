import io

import boto3
from PIL import Image

EXTENSIONES_VALIDAS = (".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif")

s3 = boto3.client("s3")


def listar_imagenes(bucket: str, prefix: str = "") -> list[str]:
    """Devuelve la lista ordenada de keys de imágenes dentro de un bucket/prefix."""
    imagenes = []
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if key.lower().endswith(EXTENSIONES_VALIDAS):
                imagenes.append(key)
    return sorted(imagenes)


def descargar_imagen(bucket: str, key: str, max_size: int = 500) -> Image.Image:
    """Baja los bytes de una imagen desde S3 y la abre con PIL, reducida para visualización."""
    resp = s3.get_object(Bucket=bucket, Key=key)
    data = resp["Body"].read()
    img = Image.open(io.BytesIO(data))
    img.load()  # fuerza la decodificación completa antes de cerrar el buffer
    img.thumbnail((max_size, max_size))  # reduce el tamaño en memoria
    return img


def descargar_bytes(bucket: str, key: str) -> bytes:
    """Baja los bytes crudos de una imagen (útil para mandarlos a un LLM)."""
    resp = s3.get_object(Bucket=bucket, Key=key)
    return resp["Body"].read()