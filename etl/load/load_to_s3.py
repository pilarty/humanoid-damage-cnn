"""Funciones de carga: copiar imagenes y subir archivos generados a S3 (processed/)."""
import boto3

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