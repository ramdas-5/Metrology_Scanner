"""
MongoDB connection layer (PyMongo).

The whole application stores its data in three collections:

  users       - one document per user (admin / inspector / viewer)
  scans       - one document per inspection, with its violations EMBEDDED as
                an array (violations are never queried on their own, so this
                keeps every scan read a single-document lookup)
  audit_logs  - append-only activity log

The MongoClient is created once per process and is lazy: importing this module
never blocks, so the API can start (and report its health) even while Atlas is
briefly unreachable.
"""

import logging

from pymongo import ASCENDING, DESCENDING, MongoClient
from pymongo.errors import PyMongoError

from app.config import settings

logger = logging.getLogger(__name__)

client = MongoClient(
    settings.MONGODB_URI,
    serverSelectionTimeoutMS=settings.MONGODB_TIMEOUT_MS,
    connectTimeoutMS=settings.MONGODB_TIMEOUT_MS,
    appname="metrology-compliance-api",
)

db = client[settings.MONGODB_DB]

users = db["users"]
scans = db["scans"]
audit_logs = db["audit_logs"]


def init_db() -> bool:
    """Create the indexes the API relies on. Safe to call on every startup.

    Returns True when MongoDB answered, False when it did not - a failed
    startup connection must not take the process down (Atlas IP allow-list
    mistakes, cold network, etc. are reported through /api/health instead).
    """
    try:
        client.admin.command("ping")
        users.create_index([("email", ASCENDING)], unique=True, name="uniq_email")
        users.create_index([("created_at", DESCENDING)], name="users_created_at")
        scans.create_index([("created_at", DESCENDING)], name="scans_created_at")
        scans.create_index([("inspector_id", ASCENDING)], name="scans_inspector")
        scans.create_index([("status", ASCENDING)], name="scans_status")
        scans.create_index([("id", ASCENDING)], unique=True, name="uniq_scan_id")
        audit_logs.create_index([("created_at", DESCENDING)], name="audit_created_at")
        audit_logs.create_index([("action", ASCENDING)], name="audit_action")
        logger.info("MongoDB ready: %s / %s", settings.MONGODB_URI.split("@")[-1], settings.MONGODB_DB)
        return True
    except PyMongoError as exc:
        logger.error("MongoDB is not reachable (%s). The API will start but "
                     "database-backed endpoints will fail until it is.", exc)
        return False


def ping() -> bool:
    """Cheap liveness probe used by /api/health and the admin System Health page."""
    try:
        client.admin.command("ping")
        return True
    except PyMongoError:
        return False


def get_db():
    """FastAPI dependency yielding the MongoDB database handle.

    Kept so routers keep the familiar `db=Depends(get_db)` shape; route code
    normally goes through `app.crud` instead of touching collections directly.
    """
    yield db


def close() -> None:
    client.close()
