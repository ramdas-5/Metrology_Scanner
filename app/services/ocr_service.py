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
import shutil
from typing import Optional

import pytesseract
from PIL import Image, ImageOps, ImageFilter

from app.config import settings

logger = logging.getLogger(__name__)

# Well-known install locations probed when TESSERACT_CMD is unset and the
# binary is not on PATH. The Windows installer does not tick "Add to PATH" by
# default, so a perfectly good Tesseract install otherwise looks like "OCR
# unavailable" and every scan silently comes back with no text.
_TESSERACT_FALLBACK_PATHS = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Programs\Tesseract-OCR\tesseract.exe"),
    "/usr/bin/tesseract",
    "/usr/local/bin/tesseract",
    "/opt/homebrew/bin/tesseract",
)


def _resolve_tesseract_cmd() -> Optional[str]:
    """Locate the tesseract binary, or return None when it cannot be found.

    Resolution order: explicit TESSERACT_CMD -> PATH -> standard install dirs.
    """
    configured = (settings.TESSERACT_CMD or "").strip().strip('"')
    if configured:
        if os.path.exists(configured):
            return configured
        logger.warning(
            "TESSERACT_CMD=%r does not exist; probing PATH and default install locations.",
            configured,
        )

    found = shutil.which("tesseract")
    if found:
        return found

    for candidate in _TESSERACT_FALLBACK_PATHS:
        if candidate and os.path.exists(candidate):
            return candidate
    return None


TESSERACT_CMD_RESOLVED = _resolve_tesseract_cmd()
if TESSERACT_CMD_RESOLVED:
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD_RESOLVED
    logger.info("Tesseract binary resolved to %s", TESSERACT_CMD_RESOLVED)
else:
    logger.warning(
        "No Tesseract binary found. OCR will be unavailable until Tesseract is "
        "installed or TESSERACT_CMD points at it."
    )

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
# frames are usually far larger than OCR needs. 2000px on the long edge keeps
# small print legible while cutting the pixel count dramatically.
_MAX_OCR_SIDE = 2000
# Upscale floor: Tesseract's accuracy collapses on small thumbnails / distant
# crops, so small images are scaled UP until their longest edge is at least
# this many pixels (~300 DPI territory) before OCR runs.
_MIN_OCR_SIDE = 1600

_PADDLE_AVAILABLE = None  # cache the availability probe (import is expensive)
_PADDLE_ENGINE = None     # cache the PaddleOCR engine itself


def _get_paddle_engine():
    """Build the PaddleOCR engine exactly once and reuse it for every scan.

    Constructing PaddleOCR loads the det/cls/rec models from disk; doing that
    per scan adds seconds of pure cold-start latency. A cached engine produces
    identical output (same models, same config) - it is purely a speed fix.
    """
    global _PADDLE_ENGINE
    if _PADDLE_ENGINE is None:
        from paddleocr import PaddleOCR

        os.environ.setdefault("ppocr.LOG_LEVEL", "ERROR")
        # v2.x signature; unknown kwargs are ignored if the API differs.
        _PADDLE_ENGINE = PaddleOCR(use_angle_cls=True, lang="en", show_log=False)
    return _PADDLE_ENGINE


def _prepare_image(image_path: str) -> Image.Image:
    """Load an image once and normalize it for OCR.

    * Oversized camera frames are downscaled (speed, no accuracy loss).
    * Small images are upscaled - Tesseract reads ~300 DPI much better than
      the 72 DPI a small crop gives it.
    * Grayscale + autocontrast handles flash glare / shadows.
    * A light unsharp-mask pass sharpens the edges of small print, which is
      where most OCR misses come from on real photos.
    """
    img = Image.open(image_path).convert("L")
    w, h = img.size
    longest = max(w, h)

    if longest > _MAX_OCR_SIDE:
        scale = _MAX_OCR_SIDE / longest
        img = img.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.LANCZOS)
    elif longest < _MIN_OCR_SIDE:
        scale = _MIN_OCR_SIDE / longest
        img = img.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.LANCZOS)

    img = ImageOps.autocontrast(img, cutoff=1)
    img = img.filter(ImageFilter.UnsharpMask(radius=2, percent=80, threshold=2))
    return img


_TESSERACT_STATUS = None


def tesseract_status() -> tuple[bool, str]:
    """Probe Tesseract: (usable, human-readable detail).

    Mirrors the AdminPanel health widget's "is OCR actually going to run?"
    question and explains *why* when it will not, instead of a bare
    "Unavailable".

    Checks more than the binary being present: a tesseract with no English
    traineddata starts fine and reports a version, but fails every image with
    "Failed loading language 'eng'" - which only ever shows up as a scan that
    detected no text. Both subprocess probes are cached, since the answer
    cannot change while the process runs.
    """
    global _TESSERACT_STATUS
    if _TESSERACT_STATUS is not None:
        return _TESSERACT_STATUS

    if not TESSERACT_CMD_RESOLVED:
        result = (False, "tesseract binary not found - install it or set TESSERACT_CMD")
    else:
        try:
            version = str(pytesseract.get_tesseract_version())
        except Exception as exc:  # binary present but not runnable (missing DLLs, etc.)
            result = (False, f"tesseract found but failed to run: {exc}")
        else:
            try:
                languages = pytesseract.get_languages(config="")
            except Exception:
                languages = []
            if languages and "eng" not in languages:
                result = (
                    False,
                    f"tesseract {version} has no English ('eng') language data - "
                    "install the tesseract-ocr-eng package (or your OS's equivalent)",
                )
            else:
                result = (True, f"tesseract {version}")

    _TESSERACT_STATUS = result
    return result


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

        ocr = _get_paddle_engine()
        image = _prepare_image(image_path).convert("RGB")
        try:
            result = ocr.ocr(np.array(image), cls=True)
        except TypeError:
            result = ocr.predict(np.array(image))
        lines = _flatten_paddle_text(result)
        return "\n".join(lines)
    except Exception as exc:
        logger.warning("PaddleOCR run failed (%s); falling back to Tesseract.", exc)
        return None


# ---------------- Tesseract ----------------

def _is_useful_line(line: str) -> bool:
    """Drop OCR noise: pure punctuation / separator lines and 1-char strays."""
    if len(line) < 2:
        return False
    return bool(re.search(r"[A-Za-z0-9]", line))


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
            if cleaned and _is_useful_line(cleaned) and cleaned not in seen:
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
    tesseract_ok, tesseract_detail = tesseract_status()

    def unavailable_error():
        return RuntimeError(
            f"OCR is unavailable: {tesseract_detail}. "
            "Install Tesseract OCR or point TESSERACT_CMD at the tesseract binary."
        )

    if engine == "paddle":
        text = _ocr_paddle(image_path)
        if text and text.strip():
            return {"text": text.strip(), "engine": "paddle"}
        # PaddleOCR returned nothing; fall back to Tesseract.
        # Never return "" from an engine that cannot run - that surfaces as a
        # silent "no text detected" on the UI, which is impossible to debug.
        if not tesseract_ok:
            raise unavailable_error()
        text = _ocr_tesseract(image_path)
        return {"text": text.strip(), "engine": "tesseract"}

    if not tesseract_ok:
        raise unavailable_error()

    text = _ocr_tesseract(image_path)
    return {"text": text.strip(), "engine": "tesseract"}


# ---------------- Declaration parsing ----------------

# Month names - reused by several date patterns.
_MONTHS = r"Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec"

# MRP. The skip class deliberately allows '&' (Tesseract often reads the rupee
# symbol as '&') and letters like 'R'/'s' (so "MRP (Inclusive of all taxes)
# Rs. 14.00" still matches). The value group is the first price after the
# keyword.
_MRP_RE = re.compile(
    r"(?:MRP|M\.?\s*R\.?\s*P\.?|Max(?:imum)?\s*Retail\s*Price)"
    r"[^\d]{0,40}?"
    r"(?:Rs\.?|₹|INR|&|#)?"   # '#' and '&' are how Tesseract often renders the rupee glyph
    r"\s*([0-9][0-9.,]*)",
    re.IGNORECASE,
)

# MRP fallback when the keyword is unreadable but a price is visible:
# a plain "NN.NN" amount that is NOT part of a dotted date, NOT glued to a
# unit (nutrition facts like "8.50g"), and NOT inside "Rs.0.30".
_MRP_BARE_RE = re.compile(
    r"(?<![.\d₹&])(?:Rs\.?|₹|INR)?\s*([0-9]{1,3}\.[0-9]{2})\b(?![\d./-])(?!\s?[a-zA-Z]\b)",
    re.IGNORECASE,
)

# The optional "space digits" group absorbs OCR noise like "NET WEIGHT: 70 9g"
# so the real value (70g) is still captured; _clean_net_quantity() drops the junk.
_NET_QTY_RE = re.compile(
    r"(?:Net\s*(?:Qty|Quantity|Wt|Weight)|Contents?)[:\s]*"
    r"([0-9]{1,6}(?:\.[0-9]+)?(?:\s+[0-9]{1,6})?\s?(?:g|gm|gram|grams|kg|ml|l|litre|litres|N|pcs|pieces))",
    re.IGNORECASE,
)
# Fallback: a bare quantity like "70g" or "500 ml" (not a 12-digit barcode).
# The lookbehind rejects fragments like the "9g" inside "70 9g".
_NET_QTY_BARE_RE = re.compile(
    r"(?<![0-9]\s)\b([0-9]{1,6}(?:\.[0-9]+)?\s?(?:g|gm|kg|ml|l))\b",
    re.IGNORECASE,
)

# PaddleOCR often joins the keyword with a hyphen ("Marketed-by:"), so the
# separator between keyword and "by" allows spaces and hyphens.
_MANUFACTURER_RE = re.compile(
    r"(?:Mfd\.?[\s\-]*by|Manufactured[\s\-]*by|Marketed[\s\-]*by|Packed[\s\-]*by|Packer|Importer)[:\s]*"
    r"([A-Za-z0-9&.,'\-]+(?:\s+[A-Za-z0-9&.,'\-]+){0,4})",
    re.IGNORECASE,
)
_MANUFACTURER_MS_RE = re.compile(
    r"\bM/s\.?\s*([A-Za-z0-9&.,'\-]+(?:\s+[A-Za-z0-9&.,'\-]+){0,3})",
    re.IGNORECASE,
)

_MFG_DATE_RE = re.compile(
    r"(?:Mfg\.?\s*(?:Date|Dt\.?)?|Mfd\.?\s*(?:Date)?|Manufactur(?:ing|ed)\s*Date|"
    r"Packing\s*(?:Date)?|Pkd\.?\s*(?:Date)?|Packed\s*On|Prod\.?\s*(?:Date)?|"
    r"Date\s*of\s*(?:Manufacture|Mfg|Packing|Production)|D\.?\s*O\.?\s*M\.?)[:\s]*"
    r"("
    r"[0-9]{1,2}[\/\-\.][0-9]{2,4}"                       # 06/2024, 09-03-2027, 03.05.26
    r"|(?:[0-9]{1,2}[\s\/\-\.]?)?(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*[\s\/\-\.]?[0-9]{2,4}"  # Jun 2024 / 24 Jun 24
    r")",
    re.IGNORECASE,
)

_CONSUMER_CARE_KEYWORD_RE = re.compile(
    r"(?:Consumer\s*Care|Toll\s*Free|Helpline|Phone|Tel)[:\s]*([0-9][0-9\s\-]{7,15})",
    re.IGNORECASE,
)
_TOLLFREE_RE = re.compile(r"(1800[\-\s]?[0-9]{3}[\-\s]?[0-9]{4})")
_EMAIL_RE = re.compile(r"([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})")
_MOBILE_RE = re.compile(r"\b([6-9][0-9]{9})\b")
_LANDLINE_RE = re.compile(r"\b(0[0-9]{2,4}[\-\s][0-9]{5,8})\b")

_COUNTRY_RE = re.compile(
    r"(?:Country\s*of\s*Origin|Made\s*in|Origin|Manufactured\s*in|Produced\s*in|Packed\s*in)[:\s]*"
    r"([A-Za-z]{3,30}(?:\s+[A-Za-z]{3,30})?)",
    re.IGNORECASE,
)

_UNIT_PRICE_RE = re.compile(
    r"(?:Unit\s*Sale\s*Price|USP)[:\s]*(?:Rs\.?|₹)?\s*([0-9]+(?:\.[0-9]{1,2})?)",
    re.IGNORECASE,
)
_UNIT_PRICE_PER_RE = re.compile(
    r"(?:Rs\.?|₹|INR)\s*([0-9]+(?:\.[0-9]{1,2})?)\s*per\s*(?:g|gm|gram|kg|ml|piece|pcs)",
    re.IGNORECASE,
)


def _first_match(pattern: str | re.Pattern, text: str) -> Optional[str]:
    m = re.search(pattern, text)
    if m:
        return m.group(1).strip() if m.groups() else m.group(0).strip()
    return None


def _clean_price(value: Optional[str]) -> Optional[str]:
    """Normalize OCR price strings: "1,000.00" -> "1000.00", "10,00" -> "10.00"."""
    if not value:
        return None
    v = value.strip().replace("₹", "")
    # Thousands separator: a comma followed by exactly 3 digits ("1,000.00").
    v = re.sub(r",(\d{3})(?!\d)", r"\1", v)
    # Comma decimal: a comma followed by exactly 2 digits at the end ("10,00").
    v = re.sub(r",(\d{2})$", r".\1", v)
    return v or None


def _looks_like_date(value: Optional[str]) -> bool:
    """Reject false positives like '00' or '05-191' captured from OCR garbage."""
    if not value:
        return False
    v = value.strip()
    # Month-name form: Jun 2024 / 24 Jun 24
    if re.search(_MONTHS, v, re.IGNORECASE):
        return True
    # Numeric form needs a real separator and a 2 or 4 digit year segment
    # ("05-191" has a 3-digit year - that is OCR noise, not a date).
    if re.fullmatch(r"[0-9]{1,2}[\/\-\.][0-9]{2}(?:[0-9]{2})?", v):
        return True
    return False


def parse_declarations(raw_text: str) -> dict:
    """
    Parse raw OCR text into the mandatory Legal Metrology declarations.
    Returns a dict with keys matching the Scan model fields, plus
    'ocr_raw_text' and a naive 'overall_confidence' score.
    """
    text = (raw_text or "").replace("\n", " ")

    # --- MRP ---
    mrp = _clean_price(_first_match(_MRP_RE, text))
    if not mrp:
        # Keyword unreadable: accept a plain 2-decimal amount that looks like
        # a price (>= 1.00) rather than a unit price, date or nutrition fact.
        for candidate in re.finditer(_MRP_BARE_RE, text):
            try:
                value = float(candidate.group(1).replace(",", "."))
            except ValueError:
                continue
            if value >= 1.0:
                mrp = _clean_price(candidate.group(1))
                break

    # --- Net Quantity (number + unit e.g. g, kg, ml, l, N) ---
    net_quantity = _first_match(_NET_QTY_RE, text)
    if net_quantity:
        # "NET WEIGHT: 70 9g" -> "70g" (drop the digit-fragment the OCR inserted)
        net_quantity = re.sub(r"\s+[0-9]+\s*", "", net_quantity)
    if not net_quantity:
        net_quantity = _first_match(_NET_QTY_BARE_RE, text)

    # --- Manufacturer / Packer / Importer ---
    manufacturer = _first_match(_MANUFACTURER_RE, text)
    if not manufacturer:
        manufacturer = _first_match(_MANUFACTURER_MS_RE, text)
    if manufacturer:
        manufacturer = re.sub(r"[\s,.\-]+$", "", manufacturer)

    # --- Mfg / Pkg date (month + year) ---
    mfg_date = _first_match(_MFG_DATE_RE, text)
    if mfg_date and not _looks_like_date(mfg_date):
        mfg_date = None
    if not mfg_date:
        # Bare "06/2024" style. The lookbehind keeps the day part of
        # "10/07/2026" from being misread as a month/year pair.
        mfg_date = _first_match(
            r"(?<![0-9/])\b((?:0[1-9]|1[0-2])[\/\-](?:19|20)[0-9]{2})\b",
            text,
        )

    # --- Consumer care (toll-free / phone / mobile / email) ---
    consumer_care = _first_match(_CONSUMER_CARE_KEYWORD_RE, text)
    if not consumer_care:
        consumer_care = _first_match(_TOLLFREE_RE, text)
    if not consumer_care:
        consumer_care = _first_match(_EMAIL_RE, text)
    if not consumer_care:
        consumer_care = _first_match(_MOBILE_RE, text)
    if not consumer_care:
        consumer_care = _first_match(_LANDLINE_RE, text)

    # --- Country of origin ---
    country_of_origin = _first_match(_COUNTRY_RE, text)
    if country_of_origin:
        words = [w for w in country_of_origin.split()
                 if w.lower() not in ("by", "pvt", "ltd", "co", "company", "industries", "and", "&")]
        country_of_origin = " ".join(words[:2])

    # --- Unit sale price (for multi-piece packs) ---
    unit_sale_price = _clean_price(_first_match(_UNIT_PRICE_RE, text))
    # "USP 09/03/2027"-style false positives: a keyword match without a
    # decimal separator is usually a date fragment, not a unit price.
    if unit_sale_price and not re.search(r"[\.\,]", unit_sale_price):
        unit_sale_price = None
    if not unit_sale_price:
        unit_sale_price = _clean_price(_first_match(_UNIT_PRICE_PER_RE, text))

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