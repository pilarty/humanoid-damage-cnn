import json

from google import genai
from google.genai import types

MODEL = "gemini-3.5-flash"  # revisá ai.google.dev/gemini-api/docs/models por el listado vigente

_client = None


def _get_client():
    """Crea el client de Gemini de forma perezosa (solo si esta función se llega a usar)."""
    global _client
    if _client is None:
        _client = genai.Client()
    return _client


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

    client = _get_client()
    response = client.models.generate_content(
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
        return {"exterior": False, "confianza": "baja", "razon": "error de parseo"}