import boto3

s3 = boto3.client("s3")


def eliminar_de_s3(bucket: str, key: str) -> None:
    s3.delete_object(Bucket=bucket, Key=key)