
#Recorre un bucket de S3, clasifica cada imagen con la API de Gemini (exterior / interior) y, 
#si detecta que es "exterior", elimina el objeto del bucket.

import base64
import json
import logging
import os

import boto3
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Carga variables desde un archivo .env local (si existe).
# En producción/CI, las variables de entorno se setean directamente,
# no hace falta el .env.
load_dotenv()

#config
BUCKET_NAME = "humanoid-damage-cnn-834257582282-us-east-1-an"
PREFIX = "raw/IDEA/no_damages/"
MODEL = "gemini-3.5-flash"

# Con DRY_RUN=True el script SOLO loguea qué borraría, no borra nada.
DRY_RUN = True

# Para probar sin gastar muchos tokens: poné un número (ej. 5) y el
# script corta después de procesar esa cantidad de imágenes.
# Poné None para procesar el bucket completo.
MAX_IMAGENES = 5

EXTENSIONES_VALIDAS = (".jpg", ".jpeg", ".png", ".webp", ".gif")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

s3 = boto3.client("s3")

# El client de Gemini toma GEMINI_API_KEY del entorno automáticamente.
gemini_client = genai.Client()

def media_type_desde_key(key: str) -> str:
    ext = key.lower().rsplit(".", 1)[-1]
    mapa = {
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "webp": "image/webp",
        "gif": "image/gif",
    }
    return mapa.get(ext, "image/jpeg")

def clasificar_imagen(img_bytes: bytes, media_type: str) -> dict:
    """Devuelve un dict {"exterior": bool, "confianza": str, "razon": str}"""

    prompt = (
        "Analiza esta imagen y decime si fue tomada en un espacio EXTERIOR "
        "(calle, naturaleza, patio, playa, montaña, etc.) o INTERIOR "
        "(adentro de un edificio, casa, oficina, etc.).\n"
        "Respondé ÚNICAMENTE con un JSON válido, sin texto adicional ni "
        "bloques de código, con este formato exacto:\n"
        '{"exterior": true o false, "confianza": "alta/media/baja", "razon": "breve explicación"}'
    )

    response = gemini_client.models.generate_content(
        model=MODEL,
        contents=[
            types.Part.from_bytes(data=img_bytes, mime_type=media_type),
            prompt,
        ],
    )

    texto = (response.text or "").strip()
    texto = texto.replace("```json", "").replace("```", "").strip()

    try:
        return json.loads(texto)
    except json.JSONDecodeError:
        log.warning("No se pudo parsear la respuesta como JSON: %s", texto)
        return {"exterior": False, "confianza": "baja", "razon": "error de parseo"}

def procesar_bucket():
    paginator = s3.get_paginator("list_objects_v2")
    pages = paginator.paginate(Bucket=BUCKET_NAME, Prefix=PREFIX)

    total = 0
    exteriores = 0
    errores = 0

    limite_alcanzado = False

    for page in pages:
        if limite_alcanzado:
            break

        for obj in page.get("Contents", []):
            if MAX_IMAGENES is not None and total >= MAX_IMAGENES:
                log.info("Se alcanzó MAX_IMAGENES=%d, cortando.", MAX_IMAGENES)
                limite_alcanzado = True
                break

            key = obj["Key"]

            if not key.lower().endswith(EXTENSIONES_VALIDAS):
                continue

            total += 1
            try:
                resp = s3.get_object(Bucket=BUCKET_NAME, Key=key)
                img_bytes = resp["Body"].read()
                media_type = media_type_desde_key(key)

                resultado = clasificar_imagen(img_bytes, media_type)
                log.info(
                    "%s -> exterior=%s (confianza=%s) %s",
                    key,
                    resultado.get("exterior"),
                    resultado.get("confianza"),
                    resultado.get("razon", ""),
                )

                if resultado.get("exterior") is True:
                    exteriores += 1
                    if DRY_RUN:
                        log.info("[DRY_RUN] Se borraría: %s", key)
                    else:
                        s3.delete_object(Bucket=BUCKET_NAME, Key=key)
                        log.info("Borrado: %s", key)

            except Exception as e:
                errores += 1
                log.error("Error procesando %s: %s", key, e)

    log.info(
        "Listo. Total procesadas=%d, exteriores=%d, errores=%d, dry_run=%s",
        total,
        exteriores,
        errores,
        DRY_RUN,
    )


procesar_bucket()

