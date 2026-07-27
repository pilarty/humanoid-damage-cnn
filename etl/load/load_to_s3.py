"""Funciones de carga: copiar imagenes y subir archivos generados a S3 (processed/)."""
from typing import Optional

import boto3
from botocore.exceptions import ClientError

s3 = boto3.client("s3")


def copy_image(bucket: str, source_key: str, dest_key: str, dry_run: bool = False) -> None:
    """Copia una imagen dentro del mismo bucket, sin descargarla localmente."""
    if dry_run:
        return
    s3.copy_object(Bucket=bucket, CopySource={"Bucket": bucket, "Key": source_key}, Key=dest_key)


def upload_bytes(bucket: str, key: str, data: bytes, dry_run: bool = False) -> None:
    """Sube contenido (por ejemplo un .txt de labels, classes.txt o data.yaml) a S3."""
    if dry_run:
        return
    s3.put_object(Bucket=bucket, Key=key, Body=data)


def download_text_if_exists(bucket: str, key: str) -> Optional[str]:
    """Descarga un archivo de texto de S3. Devuelve None si no existe todavia."""
    try:
        return s3.get_object(Bucket=bucket, Key=key)["Body"].read().decode("utf-8")
    except ClientError as exc:
        if exc.response["Error"]["Code"] in ("NoSuchKey", "404"):
            return None
        raise