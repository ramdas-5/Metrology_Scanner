"""
OCR extraction service.

Two layers:

1. ``run_ocr_engine(image_path)`` - the "give it basically any image and pull
   as much text as possible" layer. The engine is chosen from ``OCR_ENGINE``
   in .env:

   - ``paddle``    -> PaddleOCR (best quality on printed labels / documents).
                      Used automatically when installed and OCR_ENGINE=auto.
   - ``tesseract`` -> pytesseract, merging several page-segmentation modes so
                      sparse and dense layouts both get a pass.

   Returns ``{"text": ..., "engine": ...}`` where ``engine`` is the engine
   that actually produced the text (PaddleOCR is never assumed - if it is
   configured but not installed, or returns nothing, we fall back).

2. ``parse_declarations(text)`` - regex heuristics that pull the mandatory
   declarations required under the Legal Metrology (Packaged Commodities)
   Rules, 2011 out of whatever raw text layer 1 produced:
     - MRP
     - Net Quantity
     - Manufacturer / Packer / Importer name & address
     - Month & Year of manufacture / packing / import
     - Consumer care details (phone / email)
     - Country of origin
     - Unit sale price (for multi-packs), where present

   ``extract_declarations(image_path)`` keeps the old one-call signature
   (run OCR, then parse) for backwards compatibility.
"""

import logging
import os
import re
from typing import Optional

import pytesseract
from PIL import Image

from app.config import settings

if settings.TESSERACT_CMD:
    pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD

logger = logging.getLogger(__name__)

# Tesseract page-segmentation modes to merge. PSM 3 = fully automatic,
# PSM 6 = uniform block, PSM 11 = sparse text (catches scattered labels).
# If the first pass already finds plenty of text we skip the extra passes so a
# scan returns in a couple of seconds instead of ten.
_TESSERACT_CONFIGS = [
    "--oem 3 --psm 3",
    "--oem 3 --psm 6",
    "--oem 3 --psm 11",
]

# Rough "is this enough text for a product label" bar. One good pass over a
# typical label yields far more than this many characters.
_GOOD_ENOUGH_CHARS = 220
_GOOD_ENOUGH_LINES = 6

# Downscale cap: OCR runs much faster on smaller images and phone/camera
# frames are usually far larger than OCR needs. 1600px on the long edge keeps
# small print legible while cutting the pixel count dramatically.
_MAX_OCR_SIDE = 1600

_PADDLE_AVAILABLE = None  # cache the availability probe (import is expensive)


def _prepare_image(image_path: str) -> Image.Image:
    """Load an image once, downscale oversized frames, grayscale + autocontrast.
    Grayscale alone typically halves OCR time with no accuracy loss on labels."""
    img = Image.open(image_path).convert("L")
    w, h = img.size
    longest = max(w, h)
    if longest > _MAX_OCR_SIDE:
        scale = _MAX_OCR_SIDE / longest
        img = img.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.LANCZOS)
    try:
        from PIL import ImageOps
        img = ImageOps.autocontrast(img, cutoff=1)
    except Exception:
        pass
    return img


def is_paddle_available() -> bool:
    """True if the optional PaddleOCR package can be imported (checked once)."""
    global _PADDLE_AVAILABLE
    if _PADDLE_AVAILABLE is None:
        try:
            import paddleocr  # noqa: F401
            _PADDLE_AVAILABLE = True
        except Exception as exc:  # ImportError or platform/dll issues
            logger.warning("PaddleOCR not usable (%s); will use Tesseract.", exc)
            _PADDLE_AVAILABLE = False
    return _PADDLE_AVAILABLE


def resolve_ocr_engine() -> str:
    """Map OCR_ENGINE (auto|paddle|tesseract) to the engine that will run now."""
    wanted = (settings.OCR_ENGINE or "auto").strip().lower()
    if wanted == "paddle":
        return "paddle" if is_paddle_available() else "tesseract"
    if wanted == "tesseract":
        return "tesseract"
    return "paddle" if is_paddle_available() else "tesseract"


# ---------------- PaddleOCR ----------------

def _flatten_paddle_text(result) -> list:
    """
    PaddleOCR returns differently-shaped results depending on the version:

    * v2.x:  [[ [box, ("text", conf)], ... ]]           (per image, per line)
    * v3.x:  [ Result(...) ] where Result acts like a dict with "rec_texts"

    We walk whatever we got and keep every readable string, in reading order.
    """
    lines: list[str] = []

    def add(value):
        if isinstance(value, str) and value.strip():
            lines.append(value.strip())

    def walk(node):
        if node is None:
            return
        if isinstance(node, dict):
            for key in ("rec_texts", "texts", "rec_text"):
                if key in node and isinstance(node[key], (list, tuple)):
                    for item in node[key]:
                        add(item)
            for value in node.values():
                if isinstance(value, (dict, list, tuple)):
                    walk(value)
            return
        if isinstance(node, (list, tuple)):
            # Line detection entry: [box_coords, ("text", confidence)]
            if (
                len(node) == 2
                and isinstance(node[1], (list, tuple))
                and len(node[1]) == 2
                and isinstance(node[1][0], str)
            ):
                add(node[1][0])
                return
            # Plain ("text", confidence) tuple
            if (
                len(node) == 2
                and isinstance(node[0], str)
                and isinstance(node[1], (int, float))
            ):
                add(node[0])
                return
            for item in node:
                walk(item)
            return
        # Result-style objects in paddleocr 3.x expose .json / dict-like access
        if hasattr(node, "get") and callable(getattr(node, "get", None)):
            walk(node.get("rec_texts") or node.get("texts"))
            return

    walk(result)
    return lines


def _ocr_paddle(image_path: str) -> Optional[str]:
    """Run PaddleOCR (optional dependency) and return joined text lines."""
    try:
        import numpy as np
        from paddleocr import PaddleOCR

        os.environ.setdefault("ppocr.LOG_LEVEL", "ERROR")
        # v2.x signature; unknown kwargs are ignored if the API differs.
        ocr = PaddleOCR(use_angle_cls=True, lang="en", show_log=False)
        image = Image.open(image_path).convert("RGB")
        try:
            result = ocr.ocr(np.array(image), cls=True)
        except TypeError:
            result = ocr.predict(image_path)
        lines = _flatten_paddle_text(result)
        return "\n".join(lines)
    except Exception as exc:
        logger.warning("PaddleOCR run failed (%s); falling back to Tesseract.", exc)
        return None


# ---------------- Tesseract ----------------

def _ocr_tesseract(image_path: str) -> str:
    """
    Run pytesseract and merge unique, non-empty lines so dense paragraphs and
    sparse text both appear.

    Speed strategy: run PSM 3 first (the general-purpose mode). If it already
    reads a solid amount of text, return immediately - the extra sparse/block
    passes typically triple the OCR time for marginal gains on clean labels.
    """
    image = _prepare_image(image_path)
    seen: set = set()
    merged: list[str] = []
    for idx, config in enumerate(_TESSERACT_CONFIGS):
        try:
            text = pytesseract.image_to_string(image, config=config)
        except Exception as exc:
            logger.warning("Tesseract config %r failed: %s", config, exc)
            continue
        for line in text.splitlines():
            cleaned = " ".join(line.split())
            if cleaned and cleaned not in seen:
                seen.add(cleaned)
                merged.append(cleaned)
        # Fast path: the first pass on a decent photo already captures the label.
        if idx == 0 and len("\n".join(merged)) >= _GOOD_ENOUGH_CHARS and len(merged) >= _GOOD_ENOUGH_LINES:
            break
    return "\n".join(merged)


# ---------------- Public API ----------------

def run_ocr(image_path: str) -> str:
    """Plain Tesseract OCR (single pass) -> raw text. Kept for back-compat."""
    return pytesseract.image_to_string(_prepare_image(image_path))


def run_ocr_engine(image_path: str, engine: Optional[str] = None) -> dict:
    """
    Extract as much text as possible from an image using the configured
    engine (default: OCR_ENGINE / auto).

    Returns {"text": str, "engine": "paddle"|"tesseract"}.
    PaddleOCR failures and empty results automatically fall back to
    Tesseract so a bad OCR day never yields an empty scan.
    """
    engine = engine or resolve_ocr_engine()

    if engine == "paddle":
        text = _ocr_paddle(image_path)
        if text and text.strip():
            return {"text": text.strip(), "engine": "paddle"}
        # fall through to Tesseract
        text = _ocr_tesseract(image_path)
        return {"text": text.strip(), "engine": "tesseract"}

    text = _ocr_tesseract(image_path)
    return {"text": text.strip(), "engine": "tesseract"}


def parse_declarations(raw_text: str) -> dict:
    """
    Parse raw OCR text into the mandatory Legal Metrology declarations.
    Returns a dict with keys matching the Scan model fields, plus
    'ocr_raw_text' and a naive 'overall_confidence' score.
    """
    text = (raw_text or "").replace("\n", " ")

    # --- MRP ---
    mrp = _first_match(r"(?:MRP|M\.R\.P|Maximum Retail Price)[^\d₹Rs]{0,10}(?:Rs\.?|₹|INR)?\s*([0-9]+(?:[.,][0-9]{1,2})?)", text)

    # --- Net Quantity (number + unit e.g. g, kg, ml, l, N) ---
    net_quantity = _first_match(
        r"(?:Net\s*Qty|Net\s*Quantity|Net\s*Wt|Net\s*Weight|Contents)[:\s]*([0-9]+(?:\.[0-9]+)?\s?(?:g|gm|gram|kg|ml|l|litre|litres|N|pcs|pieces))",
        text,
    )
    if not net_quantity:
        net_quantity = _first_match(r"\b([0-9]+(?:\.[0-9]+)?\s?(?:g|gm|kg|ml|l))\b", text)

    # --- Manufacturer / Packer / Importer ---
    manufacturer = _first_match(
        r"(?:Mfd\.?\s*by|Manufactured\s*by|Marketed\s*by|Packed\s*by|Packer|Importer)[:\s]*([A-Za-z0-9&.,\-\s]{4,60}?)(?:,|\.|$)",
        text,
    )

    # --- Mfg / Pkg date (month + year) ---
    mfg_date = _first_match(
        r"(?:Mfg\.?\s*Date|Mfd\.?|Pkd\.?|Packing\s*Date|Date\s*of\s*Manufacture)[:\s]*"
        r"([0-3]?[0-9]?[\/\-\\.\s]?(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)?[a-z]*[\/\-\\.\s]?[0-9]{2,4})",
        text,
    )
    if not mfg_date:
        mfg_date = _first_match(r"\b(0[1-9]|1[0-2])[\/\-]([0-9]{4})\b", text)

    # --- Consumer care (phone / toll-free / email) ---
    consumer_care = _first_match(r"(1800[\-\s]?[0-9]{3}[\-\s]?[0-9]{4})", text)
    if not consumer_care:
        consumer_care = _first_match(r"([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})", text)

    # --- Country of origin ---
    country_of_origin = _first_match(r"(?:Country\s*of\s*Origin|Made\s*in|Origin)[:\s]*([A-Za-z\s]{3,30}?)(?:,|\.|$)", text)

    # --- Unit sale price (for multi-piece packs) ---
    unit_sale_price = _first_match(r"(?:Unit\s*Sale\s*Price|USP)[:\s]*(?:Rs\.?|₹)?\s*([0-9]+(?:\.[0-9]{1,2})?)", text)

    fields = {
        "mrp": mrp,
        "net_quantity": net_quantity,
        "manufacturer": manufacturer,
        "mfg_date": mfg_date,
        "consumer_care": consumer_care,
        "country_of_origin": country_of_origin,
        "unit_sale_price": unit_sale_price,
    }

    found = sum(1 for v in fields.values() if v)
    overall_confidence = round((found / len(fields)) * 100, 1)

    fields["ocr_raw_text"] = raw_text or ""
    fields["overall_confidence"] = overall_confidence
    return fields


def extract_declarations(image_path: str) -> dict:
    """
    Backwards-compatible single-call helper: run the configured OCR engine
    on the image, then parse declarations from the extracted text.
    """
    ocr = run_ocr_engine(image_path)
    fields = parse_declarations(ocr["text"])
    fields["ocr_engine"] = ocr["engine"]
    return fields


def _first_match(pattern: str, text: str, flags=re.IGNORECASE) -> Optional[str]:
    m = re.search(pattern, text, flags)
    if m:
        return m.group(1).strip() if m.groups() else m.group(0).strip()
    return None
