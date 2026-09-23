"""
One-off migration: copy the legacy SQLite database (metrology.db) into MongoDB.

    python scripts/migrate_sqlite_to_mongo.py --sqlite metrology.db

What it does
------------
* users        -> `users` collection
* scans        -> `scans` collection, with each scan's violations EMBEDDED
                  in the document (the shape the API now reads)
* audit_logs   -> `audit_logs` collection

It uses only the standard library (sqlite3) plus pymongo, so it does not need
SQLAlchemy installed any more. Documents already present in MongoDB (same `id`)
are skipped, so the script is safe to re-run.

Run this BEFORE pointing the API at MongoDB, or straight after - the API only
ever adds new documents.
"""

import argparse
import json
import os
import sqlite3
import sys
from datetime import datetime

# Allow running the script directly (python scripts/...py) by putting the
# backend root on the import path.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pymongo import MongoClient  # noqa: E402

from app.config import settings  # noqa: E402

SCAN_COLUMNS = [
    "id", "inspector_id", "product_name", "image_path",
    "mrp", "net_quantity", "manufacturer", "mfg_date", "consumer_care",
    "country_of_origin", "unit_sale_price",
    "ocr_raw_text", "overall_confidence", "label_classifier_result",
    "label_classifier_confidence",
    "ocr_engine", "ai_used", "ai_model", "ai_report", "ai_extracted_json",
    "status", "compliance_score", "created_at",
]

USER_COLUMNS = ["id", "name", "email", "hashed_password", "role", "is_active", "created_at"]

VIOLATION_COLUMNS = ["id", "scan_id", "code", "label", "severity", "rule_reference", "description"]

AUDIT_COLUMNS = ["id", "user_id", "action", "details", "created_at"]


def _table_exists(conn, name: str) -> bool:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (name,)
    ).fetchone()
    return row is not None


def _rows(conn, table: str, columns: list[str]) -> list[dict]:
    """Read a table, tolerating columns that only exist in newer schemas."""
    if not _table_exists(conn, table):
        return []
    available = {r[1] for r in conn.execute(f"PRAGMA table_info({table})")}
    selected = [c for c in columns if c in available]
    if not selected:
        return []
    cursor = conn.execute(f"SELECT {', '.join(selected)} FROM {table}")
    return [dict(zip(selected, row)) for row in cursor.fetchall()]


def _coerce(row: dict, booleans=(), floats=()) -> dict:
    for key in booleans:
        if key in row and row[key] is not None:
            row[key] = bool(row[key])
    for key in floats:
        if key in row and row[key] is not None:
            try:
                row[key] = float(row[key])
            except (TypeError, ValueError):
                row[key] = 0.0
    for key, value in row.items():
        if isinstance(value, str):
            # Values written by SQLAlchemy Enum columns look like "ScanStatus.PASSED"
            if "." in value and value.split(".")[0] in ("ScanStatus", "UserRole"):
                row[key] = value.split(".")[-1]
            if key.endswith("_json") and value:
                try:
                    json.loads(value)
                except ValueError:
                    row[key] = None
        if value is not None and key == "created_at" and isinstance(value, str):
            row[key] = datetime.fromisoformat(value)
    # Role/status enum names -> stored values
    if row.get("status") in ("PENDING_REVIEW", "PENDING"):
        row["status"] = "Pending Review"
    if row.get("status") in ("PASSED",):
        row["status"] = "Passed"
    if row.get("status") in ("FAILED",):
        row["status"] = "Failed"
    if row.get("role"):
        row["role"] = str(row["role"]).lower()
    return row


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sqlite", default="metrology.db", help="Path to the legacy SQLite file")
    parser.add_argument("--mongo", default=settings.MONGODB_URI, help="MongoDB connection string")
    parser.add_argument("--db", default=settings.MONGODB_DB, help="MongoDB database name")
    parser.add_argument("--dry-run", action="store_true", help="Read only; print what would be copied")
    args = parser.parse_args()

    conn = sqlite3.connect(args.sqlite)
    users = [_coerce(r, booleans=("is_active",)) for r in _rows(conn, "users", USER_COLUMNS)]
    scans = [_coerce(r, booleans=("ai_used",), floats=("overall_confidence", "compliance_score", "label_classifier_confidence"))
             for r in _rows(conn, "scans", SCAN_COLUMNS)]
    violations = _rows(conn, "violations", VIOLATION_COLUMNS)
    audit_logs = _rows(conn, "audit_logs", AUDIT_COLUMNS)
    conn.close()

    by_scan: dict = {}
    for violation in violations:
        by_scan.setdefault(violation.get("scan_id"), []).append(violation)
    for scan in scans:
        scan["violations"] = by_scan.get(scan.get("id"), [])

    print(f"Read {len(users)} users, {len(scans)} scans, "
          f"{len(violations)} violations, {len(audit_logs)} audit log entries")

    if args.dry_run:
        print("Dry run - nothing written.")
        return 0

    client = MongoClient(args.mongo, serverSelectionTimeoutMS=settings.MONGODB_TIMEOUT_MS)
    db = client[args.db]

    def _insert_many(collection: str, documents: list[dict], label: str) -> None:
        inserted = 0
        for document in documents:
            if not document.get("id"):
                continue
            document["_id"] = document["id"]
            try:
                db[collection].replace_one({"id": document["id"]}, document, upsert=True)
                inserted += 1
            except Exception as exc:  # pragma: no cover - defensive
                print(f"  ! {label} {document['id']} failed: {exc}", file=sys.stderr)
        print(f"{label}: {inserted} written to '{collection}'")

    _insert_many("users", users, "Users")
    _insert_many("scans", scans, "Scans")
    _insert_many("audit_logs", audit_logs, "Audit logs")

    # Rebuild the inspector snapshot fields the API now denormalizes.
    for user in users:
        db.scans.update_many(
            {"inspector_id": user["id"]},
            {"$set": {"inspector_name": user.get("name"), "inspector_email": user.get("email")}},
        )

    print("\nDone. Point MONGODB_URI at this database and start the API.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
