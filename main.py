"""
Azure Image Pipeline: Azure gpt-image-2 → Direct Image → Scanned Image

Usage:
    python main.py --count 5 --language Hindi
    python main.py --count 3 --language Marathi --profile mobile_camera --quality medium
"""

import os, argparse, json, time, logging, logging.handlers, traceback
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

from generator import generate_invoice_image, SUPPORTED_LANGUAGES
from scan_augmentor import augment_image, SCAN_PROFILES


# 2 requests per minute
RATE_LIMIT_INTERVAL = 30


def setup_logging(log_dir="./logs"):
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("pipeline")
    logger.setLevel(logging.DEBUG)

    # Console: clean INFO messages (same as old print output)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter("%(message)s"))

    # File: full DEBUG with timestamps
    fh = logging.handlers.RotatingFileHandler(
        log_path / "pipeline.log", maxBytes=5 * 1024 * 1024, backupCount=3,
        encoding="utf-8",
    )
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)-8s %(name)s | %(message)s"))

    logger.addHandler(ch)
    logger.addHandler(fh)
    return logger


def run(api_key, endpoint, count=1, language="random", output_dir="./output",
        profile=None, size="1024x1792", quality="low", fmt="PNG"):

    log = logging.getLogger("pipeline.run")
    log.info(f"\n=== Pipeline start | count={count} language={language} size={size} quality={quality} profile={profile or 'weighted_random'} ===")
    log.debug(f"output_dir={output_dir} format={fmt} endpoint={endpoint}")

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    results = []
    last_request_time = None

    for i in range(1, count + 1):
        if last_request_time is not None:
            elapsed = time.time() - last_request_time
            wait = RATE_LIMIT_INTERVAL - elapsed
            if wait > 0:
                log.info(f"\n  [Rate limit] Waiting {wait:.1f}s before next request...")
                log.debug(f"Rate limit: elapsed={elapsed:.1f}s interval={RATE_LIMIT_INTERVAL}s wait={wait:.1f}s")
                time.sleep(wait)

        log.info(f"\n[{i}/{count}] Generating...")
        ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:19]
        name = f"invoice_azimg_{ts}_{i:04d}"
        lang = language if language != "random" else None
        log.debug(f"Item {i}: name={name} requested_lang={lang}")

        try:
            t0 = time.time()
            last_request_time = t0
            img, used_lang = generate_invoice_image(endpoint, api_key, language=lang,
                                                    size=size, quality=quality)
            gen_time = round(time.time() - t0, 2)
            log.info(f"  Language : {used_lang} | {gen_time}s")
            log.debug(f"Image generated: used_lang={used_lang} gen_time={gen_time}s img_size={img.size}")

            img_dir  = out / "images"
            meta_dir = out / "metadata"
            img_dir.mkdir(parents=True, exist_ok=True)
            meta_dir.mkdir(parents=True, exist_ok=True)
            log.debug(f"Output dirs: img={img_dir} meta={meta_dir}")

            aug = augment_image(img, profile=profile)
            img_path = str(img_dir / f"{name}.{fmt.lower()}")
            aug.save(img_path, format=fmt)
            log.info(f"  Saved    : {img_path}")
            log.debug(f"Image saved: path={img_path} size={aug.size}")

            meta = {"id": name, "language": used_lang, "scan_profile": profile or "weighted_random",
                    "image_path": img_path, "generation_time_seconds": gen_time, "timestamp": ts}
            meta_path = meta_dir / f"{name}.json"
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(meta, f, ensure_ascii=False, indent=2)
            log.debug(f"Metadata saved: {meta_path}")
            results.append(meta)

        except Exception as e:
            log.error(f"  ERROR: {e}")
            log.debug(f"Full traceback for item {i}:\n{traceback.format_exc()}")
            results.append({"id": name, "error": str(e)})

    ok = len([r for r in results if "error" not in r])
    log.info(f"\nDone. {ok}/{count} invoices generated.")
    log.debug(f"Results summary: {json.dumps(results, ensure_ascii=False, indent=2)}")
    return results


def main():
    p = argparse.ArgumentParser(description="Azure gpt-image-2 → Direct Scanned Invoice Image")
    p.add_argument("--api-key",  default=os.getenv("AZURE_API_KEY"))
    p.add_argument("--endpoint", default=os.getenv("AZURE_IMAGE_ENDPOINT"))
    p.add_argument("--count",    type=int, default=1)
    p.add_argument("--language", default="random", choices=["random"] + SUPPORTED_LANGUAGES)
    p.add_argument("--output",   default="./output")
    p.add_argument("--profile",  default=None, choices=list(SCAN_PROFILES.keys()))
    p.add_argument("--size",     default="1024x1792", choices=["1024x1024", "1024x1792"])
    p.add_argument("--quality",  default="low", choices=["low", "medium", "high"])
    p.add_argument("--format",   default="PNG", choices=["PNG", "JPEG", "TIFF"])
    args = p.parse_args()

    setup_logging()
    log = logging.getLogger("pipeline")

    if not args.api_key:
        log.error("AZURE_API_KEY not set. Use .env or --api-key")
        raise ValueError("Set AZURE_API_KEY in .env or pass --api-key")
    if not args.endpoint:
        log.error("AZURE_IMAGE_ENDPOINT not set. Use .env or --endpoint")
        raise ValueError("Set AZURE_IMAGE_ENDPOINT in .env or pass --endpoint")

    log.debug(f"API key loaded (last 4 chars): ...{args.api_key[-4:]}")
    log.debug(f"Endpoint: {args.endpoint}")

    run(args.api_key, args.endpoint, args.count, args.language, args.output,
        args.profile, args.size, args.quality, args.format)


if __name__ == "__main__":
    main()
