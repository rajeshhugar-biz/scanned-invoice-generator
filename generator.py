import base64
import logging
import random
import time
from io import BytesIO
import requests
from PIL import Image
from prompts import INVOICE_IMAGE_PROMPT, DOCUMENT_TYPES, SCAN_STYLES

log = logging.getLogger("pipeline.generator")

SUPPORTED_LANGUAGES = [
    "English", "Hindi", "Marathi", "Tamil", "Telugu",
    "Kannada", "Bengali",
    "English-Hindi bilingual", "English-Marathi bilingual",
    "English-Tamil bilingual", "English-Telugu bilingual",
]


def pick_random_language() -> str:
    return random.choice(SUPPORTED_LANGUAGES)


def generate_invoice_image(
    endpoint: str,
    api_key: str,
    language: str = None,
    size: str = "1024x1792",
    quality: str = "low",
    retries: int = 3,
) -> tuple[Image.Image, str]:
    if language is None:
        language = pick_random_language()
        log.debug(f"No language specified, randomly selected: {language}")

    doc_type  = random.choice(DOCUMENT_TYPES)
    scan_style = random.choice(SCAN_STYLES)
    prompt = INVOICE_IMAGE_PROMPT.format(language=language, doc_type=doc_type, scan_style=scan_style)

    log.debug(f"Prompt built: language={language} doc_type={doc_type!r} scan_style={scan_style!r}")
    log.debug(f"Prompt length: {len(prompt)} chars")

    url = endpoint.rstrip("/") + "?api-version=2024-02-01"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
    payload = {"prompt": prompt, "size": size, "quality": quality,
               "output_format": "png", "output_compression": 100, "n": 1}

    log.debug(f"Request URL: {url}")
    log.debug(f"Payload (no prompt): size={size} quality={quality} output_format=png n=1")

    for attempt in range(1, retries + 1):
        log.debug(f"POST attempt {attempt}/{retries}")
        t0 = time.time()
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=300)
        except requests.exceptions.Timeout:
            log.error(f"Attempt {attempt}: Request timed out after 300s")
            if attempt == retries:
                raise
            continue
        except requests.exceptions.ConnectionError as e:
            log.error(f"Attempt {attempt}: Connection error — {e}")
            if attempt == retries:
                raise
            continue

        elapsed = round(time.time() - t0, 2)
        log.debug(f"Response: status={response.status_code} elapsed={elapsed}s content_length={len(response.content)} bytes")

        if response.status_code == 429:
            wait = int(response.headers.get("Retry-After", 10))
            log.warning(f"Rate limited (429). Retry-After={wait}s (attempt {attempt}/{retries})")
            time.sleep(wait)
            continue

        if not response.ok:
            log.error(f"Attempt {attempt}: HTTP {response.status_code} — {response.text[:500]}")
            response.raise_for_status()

        try:
            body = response.json()
        except Exception as e:
            log.error(f"Failed to parse JSON response: {e} | raw={response.text[:300]}")
            raise

        log.debug(f"Response JSON keys: {list(body.keys())}")

        if "data" not in body or not body["data"]:
            log.error(f"Unexpected response structure (no 'data'): {body}")
            raise ValueError(f"No 'data' in response: {body}")

        item = body["data"][0]
        log.debug(f"data[0] keys: {list(item.keys())}")

        if "b64_json" not in item:
            log.error(f"No 'b64_json' in data[0]: {item}")
            raise ValueError(f"No 'b64_json' in response data: {item}")

        b64 = item["b64_json"]
        log.debug(f"b64_json length: {len(b64)} chars")

        img = Image.open(BytesIO(base64.b64decode(b64))).convert("RGB")
        log.debug(f"Image decoded: size={img.size} mode={img.mode}")
        return img, language

    raise RuntimeError(f"Azure gpt-image-2 failed after {retries} retries.")
