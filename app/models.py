"""
Domain constants and document helpers for the MongoDB-backed API.

There is no ORM any more: a scan is one BSON document with its violations
embedded, and a user is one document in the `users` collection. The helpers
here do two jobs:

1. `gen_id()` / `utcnow()` - the defaults MongoDB itself does not provide.
2. `Doc` + `user_doc()` / `scan_doc()` / `violation_doc()` - normalize a raw
   BSON document into an object with *attribute access* and *every field
   present*. That keeps the Pydantic response models (`from_attributes=True`)
   and the PDF service working exactly as they did with SQLAlchemy rows, and
   makes a scan saved before a field existed behave like one saved after.
"""

import enum
import uuid
from datetime import datetime, timezone
from typing import Any, Optional


def gen_id() -> str:
    """Primary key for a document (also used as `_id`)."""
    return uuid.uuid4().hex


def utcnow() -> datetime:
    """Naive UTC timestamp (what MongoDB stores and returns by default)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    INSPECTOR = "inspector"
    VIEWER = "viewer"


class ScanStatus(str, enum.Enum):
    PASSED = "Passed"
    FAILED = "Failed"
    PENDING_REVIEW = "Pending Review"


class Doc(dict):
    """A dict whose keys are also readable/writable as attributes."""

    def __getattr__(self, name: str) -> Any:
        try:
            return self[name]
        except KeyError as exc:  # pragma: no cover - defensive
            raise AttributeError(name) from exc

    def __setattr__(self, name: str, value: Any) -> None:
        self[name] = value


# ---- Field defaults: every document is normalized to the full shape --------

USER_DEFAULTS = {
    "id": None,
    "name": "",
    "email": "",
    "hashed_password": "",
    "role": UserRole.INSPECTOR.value,
    "is_active": True,
    "created_at": None,
}

VIOLATION_DEFAULTS = {
    "id": None,
    "code": "",
    "label": "",
    "severity": "major",
    "rule_reference": None,
    "description": None,
}

SCAN_DEFAULTS = {
    "id": None,
    "inspector_id": None,
    "inspector_name": None,
    "inspector_email": None,
    "product_name": None,
    "image_path": None,
    # OCR extracted declarations (mandatory fields under LM(PC) Rules 2011)
    "mrp": None,
    "net_quantity": None,
    "manufacturer": None,
    "mfg_date": None,
    "consumer_care": None,
    "country_of_origin": None,
    "unit_sale_price": None,
    # OCR / model confidence
    "ocr_raw_text": None,
    "overall_confidence": 0.0,
    "label_classifier_result": None,
    "label_classifier_confidence": 0.0,
    # AI extraction pipeline (OCR -> OpenRouter -> fixed JSON verdict/report)
    "ocr_engine": None,
    "ai_used": False,
    "ai_model": None,
    "ai_report": None,
    "ai_extracted_json": None,
    # Compliance result
    "status": ScanStatus.PENDING_REVIEW.value,
    "compliance_score": 0.0,
    "created_at": None,
    # Embedded violations
    "violations": [],
}

AUDIT_DEFAULTS = {
    "id": None,
    "user_id": None,
    "action": "",
    "details": None,
    "created_at": None,
}


def _to_doc(raw: Any, defaults: dict) -> Doc:
    data = dict(defaults)
    if raw:
        data.update({k: v for k, v in dict(raw).items() if k != "_id"})
    return Doc(data)


def user_doc(raw: Any) -> Doc:
    """Normalize a users document (never exposes `_id` to the API layer)."""
    doc = _to_doc(raw, USER_DEFAULTS)
    # Roles are stored as plain strings; tolerate legacy enum values.
    doc["role"] = doc["role"].value if isinstance(doc["role"], enum.Enum) else str(doc["role"])
    return doc


def violation_doc(raw: Any) -> Doc:
    return _to_doc(raw, VIOLATION_DEFAULTS)


def scan_doc(raw: Any) -> Doc:
    """Normalize a scans document, including its embedded violations."""
    doc = _to_doc(raw, SCAN_DEFAULTS)
    doc["status"] = doc["status"].value if isinstance(doc["status"], enum.Enum) else str(doc["status"])
    doc["violations"] = [violation_doc(v) for v in (doc.get("violations") or [])]
    doc["overall_confidence"] = doc["overall_confidence"] or 0.0
    doc["compliance_score"] = doc["compliance_score"] or 0.0
    doc["label_classifier_confidence"] = doc["label_classifier_confidence"] or 0.0
    return doc


def audit_doc(raw: Any) -> Doc:
    return _to_doc(raw, AUDIT_DEFAULTS)


def new_audit_log(
    action: str,
    user_id: Optional[str] = None,
    details: Optional[str] = None,
) -> dict:
    return {
        "_id": gen_id(),
        "id": gen_id(),
        "user_id": user_id,
        "action": action,
        "details": details,
        "created_at": utcnow(),
    }
