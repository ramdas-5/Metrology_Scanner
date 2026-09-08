"""
AI structured-extraction service (OpenRouter).

Takes the raw OCR text of *any* image and asks an LLM behind OpenRouter to
turn it into one canonical, fixed-shape JSON document:

    {
      "product_name": str | null,
      "mrp": str | null, "net_quantity": str | null, "manufacturer": str | null,
      "mfg_date": str | null, "consumer_care": str | null,
      "country_of_origin": str | null, "unit_sale_price": str | null,

      "status": "Passed" | "Failed" | "Pending Review",
      "compliance_score": int 0-100,
      "violations": [{code, label, severity, rule_reference, description}, ...],
      "overall_confidence": int 0-100,
      "summary": str
    }

Every key is *always* present (null when the text doesn't contain it), so the
backend, database and UI can rely on one format no matter what the image is.
The status/score/violations/summary are the AI's computed metrics + report and
are stored directly on the Scan when the API key is configured. When the key
is missing (or the call fails) the caller falls back to the deterministic
regex + rule engine.
"""

import json
import logging
import re
from typing import Optional

from app.config import settings

logger = logging.getLogger(__name__)

_OPENAI_CLIENT = None

# Canonical output keys, always present, in this order.
OUTPUT_KEYS = [
    "product_name",
    "mrp",
    "net_quantity",
    "manufacturer",
    "mfg_date",
    "consumer_care",
    "country_of_origin",
    "unit_sale_price",
]

CANONICAL_STATUS = {
    "passed": "Passed",
    "failed": "Failed",
    "pending review": "Pending Review",
}
VALID_SEVERITIES = {"major", "minor"}

SYSTEM_PROMPT = """You are an OCR post-processor + Legal Metrology compliance analyst for packaged consumer products (India's Legal Metrology (Packaged Commodities) Rules, 2011).

You receive the raw OCR text of a product-label image. Do two things:

1) Extract the declared values and 2) grade the label for compliance.

Reply with ONLY one valid JSON object and nothing else (no markdown, no commentary). The JSON must always contain EXACTLY these keys (use null when a value is not present in the text):

{
  "product_name": <string|null>,        # product/brand name visible on the label
  "mrp": <string|null>,                 # MRP incl. of all taxes, e.g. "14.00" or "Rs. 14.00" -> "14.00"
  "net_quantity": <string|null>,        # e.g. "70 g", "500 ml", "1 kg", "10 pcs"
  "manufacturer": <string|null>,        # name+address of mfd/packed/marketed by/importer
  "mfg_date": <string|null>,            # month & year of manufacture/packing/import, e.g. "Jun 2024" or "06/2024"
  "consumer_care": <string|null>,       # consumer-care phone/toll-free/email/website
  "country_of_origin": <string|null>,   # e.g. "India"
  "unit_sale_price": <string|null>,     # unit sale price for multi-piece packs if present

  "status": "Passed" | "Failed" | "Pending Review",
  "compliance_score": <int 0-100>,
  "violations": [
    {
      "code": <string>,                 # e.g. "MISSING_MRP", "MISSING_NET_QUANTITY", "MISSING_MFG_DATE", "INVALID_MRP"
      "label": <string>,                # short human-readable title
      "severity": "major" | "minor",
      "rule_reference": <string|null>,  # e.g. "Rule 6(1)(e)"
      "description": <string>
    }
  ],
  "overall_confidence": <int 0-100>,    # your confidence that the extraction is complete/correct
  "summary": <string>                   # 2-4 sentence plain-English inspection report for an officer
}

Compliance grading rules of thumb (based on the LM(PC) Rules 2011):
- Missing MRP, net quantity, manufacturer/packer/importer details, month+year of manufacture/packing/import, or country of origin are MAJOR violations.
- Missing/blank consumer-care contact is a MINOR violation.
- If no declared fields are found at all, status is "Failed" and the violations list explains why.
- Values must be read literally from the OCR text; never invent numbers. When OCR text is clearly noise, prefer null over guessing.
- "Pending Review" only for ambiguous cases (e.g. partially readable values).
- The compliance_score must be consistent with the violations (100 with no violations, lower as majors stack up)."""


class AIExtractionError(Exception):
    """Raised when OpenRouter cannot be reached or its output cannot be parsed."""


def is_ai_configured() -> bool:
    return bool((settings.OPENROUTER_API_KEY or "").strip())


def _get_client():
    global _OPENAI_CLIENT
    if _OPENAI_CLIENT is None:
        try:
            from openai import OpenAI
        except ImportError as exc:  # openai package not installed
            raise AIExtractionError(
                "The 'openai' package is not installed. Run: pip install openai"
            ) from exc
        _OPENAI_CLIENT = OpenAI(
            api_key=settings.OPENROUTER_API_KEY,
            base_url=settings.OPENROUTER_BASE_URL,
            timeout=settings.AI_TIMEOUT_SECONDS,
        )
    return _OPENAI_CLIENT


def _chat_json(messages, json_mode: bool):
    client = _get_client()
    kwargs = {
        "model": settings.OPENROUTER_MODEL,
        "messages": messages,
        "temperature": 0,
        # Keep the answer short and bounded - a fixed-shape JSON never needs
        # thousands of tokens, and capping it prevents runaway generations.
        "max_tokens": 900,
    }
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}
    response = client.chat.completions.create(**kwargs)
    content = response.choices[0].message.content or ""
    return content


def _parse_json_content(content: str) -> dict:
    """Strip markdown fences and pull the first balanced JSON object out."""
    if not content or not content.strip():
        raise AIExtractionError("OpenRouter returned an empty response")
    cleaned = content.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-zA-Z]*\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    # Last resort: slice from first '{' to matching final '}'.
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end > start:
        try:
            return json.loads(cleaned[start : end + 1])
        except json.JSONDecodeError:
            pass
    raise AIExtractionError("OpenRouter output was not valid JSON")


def _clean(value) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        return None
    text = str(value).strip()
    if not text or text.lower() in {"null", "none", "n/a", "na", "-", "--"}:
        return None
    return text


def _coerce_status(value) -> str:
    """Map any casing the model returns to the canonical Scan status values."""
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in CANONICAL_STATUS:
            return CANONICAL_STATUS[normalized]
    return "Pending Review"


def _coerce_int(value, default: Optional[int] = None) -> Optional[int]:
    if isinstance(value, bool):
        return default
    try:
        num = float(value)
        return int(round(num))
    except (TypeError, ValueError):
        return default


def _normalize_violation(raw) -> dict:
    if not isinstance(raw, dict):
        raw = {}
    label = _clean(raw.get("label")) or "Compliance issue detected"
    severity = str(raw.get("severity", "major") or "major").strip().lower()
    if severity not in VALID_SEVERITIES:
        severity = "major"
    return {
        "code": _clean(raw.get("code")) or "AI_FLAG",
        "label": label,
        "severity": severity,
        "rule_reference": _clean(raw.get("rule_reference")),
        "description": _clean(raw.get("description")) or label,
    }


def _normalize_payload(raw: dict) -> dict:
    """Guarantee the fixed output shape regardless of what the model returned."""
    payload = {
        "status": _coerce_status(raw.get("status")),
        "compliance_score": _coerce_int(raw.get("compliance_score"), default=0) or 0,
        "violations": [_normalize_violation(v) for v in (raw.get("violations") or []) if isinstance(v, dict)],
        "summary": _clean(raw.get("summary")) or "",
        "overall_confidence": _coerce_int(raw.get("overall_confidence")),
    }
    payload["compliance_score"] = max(0, min(100, payload["compliance_score"]))
    if payload["overall_confidence"] is not None:
        payload["overall_confidence"] = max(0, min(100, payload["overall_confidence"]))
    for key in OUTPUT_KEYS:
        payload[key] = _clean(raw.get(key))
    return payload


def extract_label_data(raw_text: str, product_name: Optional[str] = None) -> dict:
    """
    Send raw OCR text to OpenRouter and get back the canonical, fixed-shape
    dict described above (all keys always present, nulls allowed).

    Raises AIExtractionError when the API key is unset, the request fails, or
    the model output cannot be parsed - callers should treat that as "fall
    back to the deterministic engine".
    """
    if not is_ai_configured():
        raise AIExtractionError("OPENROUTER_API_KEY is not configured")
    if not (raw_text or "").strip():
        raise AIExtractionError("No OCR text to extract from")

    user_hint = ""
    if product_name and str(product_name).strip():
        user_hint = f"\n\n(The operator provided the product name '{product_name}' - use it for product_name if plausible.)"
    user_prompt = (
        "Here is the raw OCR text extracted from a product-label image. "
        "If the text contains '=== Side N ===' markers, it was captured from "
        "several sides of the same package: merge them and treat them as ONE "
        "product label. "
        "Convert it into the required JSON:\n\n"
        f"```\n{raw_text}\n```"
        f"{user_hint}"
    )

    content = None
    last_error = None
    # First attempt with native JSON mode. Some OpenRouter models reject
    # response_format - retry once WITHOUT it, but only for errors that look
    # like a format/parameter problem. Retrying a timeout would double the
    # user-visible latency for nothing.
    for json_mode in (True, False):
        try:
            content = _chat_json(
                [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                json_mode=json_mode,
            )
            break
        except AIExtractionError:
            raise
        except Exception as exc:
            last_error = exc
            msg = str(exc).lower()
            transient = any(
                token in msg
                for token in ("timeout", "timed out", "connection", "rate limit", "429", "5")
            )
            if transient:
                logger.warning("OpenRouter call failed with a transient error; not retrying: %s", exc)
                break
            logger.warning("OpenRouter call (json_mode=%s) failed: %s", json_mode, exc)

    if content is None:
        raise AIExtractionError(f"OpenRouter request failed: {last_error}")

    try:
        raw_payload = _parse_json_content(content)
    except AIExtractionError:
        logger.warning("Could not parse OpenRouter output; raw content: %.400s", content)
        raise

    payload = _normalize_payload(raw_payload)
    payload["model"] = settings.OPENROUTER_MODEL
    return payload
