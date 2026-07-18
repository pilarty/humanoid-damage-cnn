import boto3

s3 = boto3.client("s3")


def copiar_a_carpeta(bucket: str, key_origen: str, carpeta_destino: str) -> str:
    """
    Copia un objeto dentro del mismo bucket, a otra carpeta (prefix).
    Devuelve la key nueva.

    Ejemplo:
        copiar_a_carpeta(
            "mi-bucket",
            "raw/IDEA/no_damages/images/foto1.jpg",
            "raw/IDEA/no_damages/conservadas/"
        )
        -> copia el archivo a "raw/IDEA/no_damages/conservadas/foto1.jpg"
    """
    nombre_archivo = key_origen.split("/")[-1]
    if not carpeta_destino.endswith("/"):
        carpeta_destino += "/"
    key_destino = f"{carpeta_destino}{nombre_archivo}"

    s3.copy_object(
        Bucket=bucket,
        CopySource={"Bucket": bucket, "Key": key_origen},
        Key=key_destino,
    )
    return key_destino