"""
Data access layer for the MongoDB backend.

Every database read/write in the application goes through this module - the
routers stay readable and the Mongo specifics (aggregation pipelines, embedded
violations, index-friendly queries) live in one place.

Conventions:
  * `_id` mirrors `id` (a uuid hex string) and is stripped before returning.
  * Dates are naive UTC datetimes, exactly what PyMongo stores/returns.
  * Violations are embedded inside the scan document, so a scan is always a
    single-document read.
"""

import logging
import re
from datetime import datetime, timedelta
from typing import Optional

from app import models
from app.database import audit_logs, db, scans, users
from app.models import Doc, gen_id, utcnow

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------
# Query helpers
# --------------------------------------------------------------------------

def _escape_regex(value: str) -> str:
    return re.escape(value)


def build_scan_match(
    status: Optional[str] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    search: Optional[str] = None,
) -> dict:
    """Translate the API's filters into one MongoDB match document.

    `to_date` is inclusive: everything up to the END of that day.
    """
    match: dict = {}
    if status and status != "All":
        match["status"] = status
    created = {}
    if from_date:
        created["$gte"] = from_date
    if to_date:
        created["$lt"] = to_date + timedelta(days=1)
    if created:
        match["created_at"] = created
    if search:
        rx = {"$regex": _escape_regex(search.strip()), "$options": "i"}
        match["$or"] = [
            {"product_name": rx},
            {"mrp": rx},
            {"inspector_name": rx},
        ]
    return match


# --------------------------------------------------------------------------
# Users
# --------------------------------------------------------------------------

def get_user(user_id: str) -> Optional[Doc]:
    raw = users.find_one({"id": user_id})
    return models.user_doc(raw) if raw else None


def get_user_by_email(email: str) -> Optional[Doc]:
    raw = users.find_one({"email": (email or "").lower().strip()})
    return models.user_doc(raw) if raw else None


def create_user(name: str, email: str, hashed_password: str, role: str) -> Doc:
    user_id = gen_id()
    doc = {
        "_id": user_id,
        "id": user_id,
        "name": name,
        "email": (email or "").lower().strip(),
        "hashed_password": hashed_password,
        "role": str(role),
        "is_active": True,
        "created_at": utcnow(),
    }
    users.insert_one(doc)
    return models.user_doc(doc)


def list_users() -> list[Doc]:
    return [models.user_doc(u) for u in users.find().sort("created_at", -1)]


def set_user_active(user_id: str, is_active: bool) -> Optional[Doc]:
    users.update_one({"id": user_id}, {"$set": {"is_active": bool(is_active)}})
    return get_user(user_id)


def delete_user(user_id: str) -> bool:
    return users.delete_one({"id": user_id}).deleted_count > 0


def count_users() -> int:
    return users.count_documents({})


def scan_counts_by_inspector() -> dict:
    """{inspector_id: number_of_scans} in one aggregation."""
    pipeline = [{"$group": {"_id": "$inspector_id", "count": {"$sum": 1}}}]
    return {row["_id"]: int(row["count"]) for row in scans.aggregate(pipeline) if row["_id"]}


def inspector_activity() -> list[tuple]:
    """[(name, email, scan_count), ...] for the summary PDF."""
    counts = scan_counts_by_inspector()
    return [
        (u["name"], u["email"], int(counts.get(u["id"], 0)))
        for u in users.find().sort("name", 1)
    ]


def ensure_default_admin() -> bool:
    """Create the bootstrap admin on a brand-new (empty) deployment."""
    from app import auth as auth_utils
    from app.config import settings

    if count_users() > 0:
        return False
    create_user(
        name=settings.ADMIN_NAME,
        email=settings.ADMIN_EMAIL,
        hashed_password=auth_utils.hash_password(settings.ADMIN_PASSWORD),
        role=models.UserRole.ADMIN.value,
    )
    logger.info("Created bootstrap admin account: %s", settings.ADMIN_EMAIL)
    return True


# --------------------------------------------------------------------------
# Scans
# --------------------------------------------------------------------------

def insert_scan(document: dict) -> Doc:
    document.setdefault("_id", document.get("id") or gen_id())
    document.setdefault("id", document["_id"])
    document.setdefault("created_at", utcnow())
    scans.insert_one(document)
    return models.scan_doc(document)


def get_scan(scan_id: str) -> Optional[Doc]:
    raw = scans.find_one({"id": scan_id})
    return models.scan_doc(raw) if raw else None


def delete_scan(scan_id: str) -> bool:
    return scans.delete_one({"id": scan_id}).deleted_count > 0


def find_recent_ocr_texts(limit: int) -> list[tuple]:
    """[(scan_id, ocr_raw_text)] newest first - used by the similarity cache."""
    cursor = (
        scans.find(
            {"ocr_raw_text": {"$nin": [None, ""]}},
            {"_id": 0, "id": 1, "ocr_raw_text": 1},
        )
        .sort("created_at", -1)
        .limit(limit)
    )
    return [(row.get("id"), row.get("ocr_raw_text")) for row in cursor]


def list_scans(
    status: Optional[str] = None,
    search: Optional[str] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Doc], int]:
    match = build_scan_match(status, from_date, to_date, search)
    page = max(1, page)
    page_size = max(1, min(page_size, 200))
    total = scans.count_documents(match)
    cursor = (
        scans.find(match)
        .sort("created_at", -1)
        .skip((page - 1) * page_size)
        .limit(page_size)
    )
    return [models.scan_doc(row) for row in cursor], total


def update_scan_fields(scan_id: str, values: dict) -> Optional[Doc]:
    if values:
        scans.update_one({"id": scan_id}, {"$set": values})
    return get_scan(scan_id)


# ---- Aggregations used by the dashboard / reports / admin screens ----------

def count_scans(match: Optional[dict] = None) -> int:
    return scans.count_documents(match or {})


def count_by_status(match: Optional[dict] = None) -> dict:
    pipeline = [
        {"$match": match or {}},
        {"$group": {"_id": "$status", "count": {"$sum": 1}}},
    ]
    return {row["_id"]: int(row["count"]) for row in scans.aggregate(pipeline)}


def count_ai_scans(match: Optional[dict] = None) -> int:
    query = dict(match or {})
    query["ai_used"] = True
    return scans.count_documents(query)


def avg_metrics(match: Optional[dict] = None) -> tuple[float, float]:
    pipeline = [
        {"$match": match or {}},
        {
            "$group": {
                "_id": None,
                "avg_confidence": {"$avg": "$overall_confidence"},
                "avg_score": {"$avg": "$compliance_score"},
            }
        },
    ]
    rows = list(scans.aggregate(pipeline))
    if not rows:
        return 0.0, 0.0
    return float(rows[0].get("avg_confidence") or 0.0), float(rows[0].get("avg_score") or 0.0)


def count_violations(match: Optional[dict] = None) -> int:
    pipeline = [
        {"$match": match or {}},
        {"$unwind": "$violations"},
        {"$count": "total"},
    ]
    rows = list(scans.aggregate(pipeline))
    return int(rows[0]["total"]) if rows else 0


def top_violations(match: Optional[dict] = None, limit: int = 5) -> list[tuple]:
    """[(label, count)] most frequent violations, highest first."""
    pipeline = [
        {"$match": match or {}},
        {"$unwind": "$violations"},
        {"$group": {"_id": "$violations.label", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": limit},
    ]
    return [(row["_id"], int(row["count"])) for row in scans.aggregate(pipeline)]


def daily_counts(start: datetime, status: Optional[str] = None) -> dict:
    """{'YYYY-MM-DD': count} for scans on/after `start`."""
    match: dict = {"created_at": {"$gte": start}}
    if status and status != "All":
        match["status"] = status
    pipeline = [
        {"$match": match},
        {
            "$group": {
                "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}},
                "count": {"$sum": 1},
            }
        },
    ]
    return {row["_id"]: int(row["count"]) for row in scans.aggregate(pipeline) if row["_id"]}


def export_all() -> dict:
    """Full dump of every collection (used by the admin 'Backup Now' action)."""
    def _clean(document: dict) -> dict:
        out = {k: v for k, v in document.items() if k != "_id"}
        for key, value in out.items():
            if isinstance(value, datetime):
                out[key] = value.isoformat()
        return out

    return {
        "exported_at": utcnow().isoformat(),
        "database": db.name,
        "users": [_clean(u) for u in users.find()],
        "scans": [_clean(s) for s in scans.find()],
        "audit_logs": [_clean(a) for a in audit_logs.find()],
    }


# --------------------------------------------------------------------------
# Audit log
# --------------------------------------------------------------------------

def add_audit_log(user_id: Optional[str], action: str, details: Optional[str] = None) -> None:
    audit_logs.insert_one(models.new_audit_log(action=action, user_id=user_id, details=details))


def _log_with_user(raw: dict, names: dict) -> dict:
    doc = models.audit_doc(raw)
    return {
        "id": doc["id"],
        "user_id": doc["user_id"],
        "user_name": names.get(doc["user_id"]),
        "action": doc["action"],
        "details": doc["details"],
        "created_at": doc["created_at"],
    }


def _user_name_map(user_ids: list) -> dict:
    ids = [uid for uid in set(user_ids or []) if uid]
    if not ids:
        return {}
    return {u["id"]: u.get("name") for u in users.find({"id": {"$in": ids}}, {"_id": 0, "id": 1, "name": 1})}


def recent_activity(limit: int = 10) -> list[dict]:
    logs = list(audit_logs.find().sort("created_at", -1).limit(max(1, min(limit, 50))))
    names = _user_name_map([log.get("user_id") for log in logs])
    return [_log_with_user(log, names) for log in logs]


def list_audit_logs(limit: int = 50) -> list[dict]:
    logs = list(audit_logs.find().sort("created_at", -1).limit(max(1, min(limit, 500))))
    names = _user_name_map([log.get("user_id") for log in logs])
    return [_log_with_user(log, names) for log in logs]


def count_audit_logs(action: str) -> int:
    return audit_logs.count_documents({"action": action})
