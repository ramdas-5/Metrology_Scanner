"""
Tiny, idempotent migration helper for SQLite.

There is no Alembic in this project; tables are created with
`Base.metadata.create_all()`, which never adds *new* columns to an existing
database. When the Scan model gains columns (e.g. the AI extraction fields),
existing `metrology.db` files would break at runtime, so we ALTER TABLE any
missing column on startup. No-op on non-SQLite URLs.
"""

import logging

from sqlalchemy import inspect, text

logger = logging.getLogger(__name__)

# (column name -> SQL type fragment). SQLite ALTER TABLE ADD COLUMN only
# supports constant defaults, which is all we need here.
SCAN_COLUMNS = {
    "ocr_engine": "VARCHAR",
    "ai_used": "BOOLEAN DEFAULT 0",
    "ai_model": "VARCHAR",
    "ai_report": "TEXT",
    "ai_extracted_json": "TEXT",
}


def run_migrations(engine) -> None:
    if not str(engine.url).startswith("sqlite"):
        return

    inspector = inspect(engine)
    if "scans" not in inspector.get_table_names():
        return

    existing = {col["name"] for col in inspector.get_columns("scans")}
    missing = {col: ddl for col, ddl in SCAN_COLUMNS.items() if col not in existing}
    if not missing:
        return

    with engine.begin() as conn:
        for col, ddl in missing.items():
            logger.info("Migrating: adding scans.%s column", col)
            conn.execute(text(f'ALTER TABLE scans ADD COLUMN "{col}" {ddl}'))
