"""
End-to-end smoke test for the MongoDB-backed API.

It runs the real FastAPI app (routes, auth, rule engine, PDF generation)
against an in-memory MongoDB (mongomock), so it needs no Atlas connection and
no Tesseract install: the OCR engine is stubbed with realistic label text.

    pip install pytest "httpx<0.28" mongomock
    python -m pytest tests -q
"""

import io
import os

import pytest

# --- Environment must be set BEFORE the app packages are imported ----------
os.environ["MONGODB_URI"] = "mongodb://localhost:27017"
os.environ["MONGODB_DB"] = "metrology_test"
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["ADMIN_EMAIL"] = "admin@metrology.gov.in"
os.environ["ADMIN_PASSWORD"] = "admin123"
os.environ["CLASSIFIER_ENABLED"] = "false"
os.environ["OPENROUTER_API_KEY"] = ""          # force the deterministic path
os.environ["CORS_ORIGINS"] = "http://localhost:5173"

import mongomock  # noqa: E402
import pymongo  # noqa: E402

# The app creates its MongoClient at import time, so swap the class first.
pymongo.MongoClient = mongomock.MongoClient

from fastapi.testclient import TestClient  # noqa: E402
from PIL import Image  # noqa: E402

from app import database  # noqa: E402
from app.main import app  # noqa: E402
from app.services import classifier_service, ocr_service  # noqa: E402

COMPLIANT_LABEL_TEXT = """
Delicious Biscuits
MRP Rs. 30.00 (Inclusive of all taxes)
Net Quantity: 200 g
Manufactured by: Sunshine Foods Pvt Ltd, Pune
Mfg Date: 06/2026
Consumer Care: 1800-123-4567
Country of Origin: India
"""

INCOMPLETE_LABEL_TEXT = """
Mystery Snack
Net Wt: 50 g
Consumer Care: care@example.com
"""


@pytest.fixture(scope="module")
def client():
    original_ocr = ocr_service.run_ocr_engine
    original_classify = classifier_service.classify_image

    # OCR + the optional label classifier are external dependencies; stub them
    # so the test exercises OUR code (DB writes, rule engine, reports) only.
    ocr_service.run_ocr_engine = lambda path, engine=None: {
        "text": COMPLIANT_LABEL_TEXT,
        "engine": "tesseract",
    }

    def _no_classifier(*_args, **_kwargs):
        raise RuntimeError("classifier disabled in tests")

    classifier_service.classify_image = _no_classifier
    classifier_service.warmup_async = lambda: None

    with TestClient(app) as test_client:
        yield test_client

    ocr_service.run_ocr_engine = original_ocr
    classifier_service.classify_image = original_classify


@pytest.fixture(scope="module")
def token(client):
    res = client.post(
        "/api/auth/login",
        json={"email": "admin@metrology.gov.in", "password": "admin123"},
    )
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _jpeg_bytes() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (64, 64), "white").save(buffer, format="JPEG")
    return buffer.getvalue()


def test_health_reports_database(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["database"] == "connected"


def test_bootstrap_admin_and_me(client, token):
    res = client.get("/api/auth/me", headers=_auth(token))
    assert res.status_code == 200
    assert res.json()["role"] == "admin"


def test_login_rejects_bad_password(client):
    res = client.post(
        "/api/auth/login",
        json={"email": "admin@metrology.gov.in", "password": "wrong"},
    )
    assert res.status_code == 401


def test_create_scan_runs_rule_engine(client, token):
    res = client.post(
        "/api/scans",
        headers=_auth(token),
        files={"image": ("label.jpg", _jpeg_bytes(), "image/jpeg")},
        data={"product_name": "Biscuits"},
    )
    assert res.status_code == 201, res.text
    body = res.json()
    assert body["status"] == "Passed"
    assert body["mrp"] == "30.00"
    assert body["net_quantity"] == "200 g"
    assert body["violations"] == []
    assert body["inspector_name"] == "System Administrator"
    assert body["cached"] is False
    assert body["processing_ms"] is not None

    # Cached within the module fixture: the same OCR text must short-circuit.
    again = client.post(
        "/api/scans",
        headers=_auth(token),
        files={"image": ("label.jpg", _jpeg_bytes(), "image/jpeg")},
    )
    assert again.status_code == 201, again.text
    assert again.json()["cached"] is True
    assert again.json()["id"] == body["id"]


def test_scan_list_search_and_pagination(client, token):
    res = client.get("/api/scans", headers=_auth(token), params={"search": "Bisc"})
    assert res.status_code == 200
    body = res.json()
    assert body["total"] >= 1
    assert body["page"] == 1
    assert body["items"][0]["inspector_email"] == "admin@metrology.gov.in"


def test_scan_update_recomputes_violations(client, token):
    created = client.post(
        "/api/scans",
        headers=_auth(token),
        files={"image": ("label2.jpg", _jpeg_bytes(), "image/jpeg")},
        data={"product_name": "Mystery"},
    ).json()

    ocr_service.run_ocr_engine = lambda path, engine=None: {
        "text": INCOMPLETE_LABEL_TEXT,
        "engine": "tesseract",
    }
    incomplete = client.post(
        "/api/scans",
        headers=_auth(token),
        files={"image": ("label3.jpg", _jpeg_bytes(), "image/jpeg")},
    ).json()
    ocr_service.run_ocr_engine = lambda path, engine=None: {
        "text": COMPLIANT_LABEL_TEXT,
        "engine": "tesseract",
    }
    assert incomplete["status"] == "Failed"
    codes = {v["code"] for v in incomplete["violations"]}
    assert {"MISSING_MRP", "MISSING_MANUFACTURER", "MISSING_MFG_DATE"} <= codes

    res = client.patch(
        f"/api/scans/{incomplete['id']}",
        headers=_auth(token),
        json={"mrp": "10.00", "manufacturer": "ACME", "mfg_date": "01/2026"},
    )
    assert res.status_code == 200, res.text
    assert res.json()["status"] == "Passed"
    assert res.json()["violations"] == []

    assert client.get(f"/api/scans/{created['id']}", headers=_auth(token)).status_code == 200
    assert client.get("/api/scans/does-not-exist", headers=_auth(token)).status_code == 404


def test_dashboard_stats_and_activity(client, token):
    stats = client.get("/api/dashboard/stats", headers=_auth(token), params={"period": "All"})
    assert stats.status_code == 200
    body = stats.json()
    assert body["total_inspections"] >= 2
    assert body["compliant"] >= 1
    assert 0 <= body["compliance_rate"] <= 100

    activity = client.get("/api/dashboard/recent-activity", headers=_auth(token))
    assert activity.status_code == 200
    assert any(item["action"] == "SCAN_CREATED" for item in activity.json())


def test_admin_endpoints(client, token):
    users = client.get("/api/admin/users", headers=_auth(token))
    assert users.status_code == 200
    assert users.json()[0]["scan_count"] >= 1

    stats = client.get("/api/admin/system-stats", headers=_auth(token)).json()
    assert stats["total_inspections"] >= 2
    assert stats["total_users"] == 1
    assert stats["cache_hits"] >= 1

    trend = client.get("/api/admin/trend", headers=_auth(token), params={"days": 7})
    assert trend.status_code == 200
    assert len(trend.json()) == 7

    rules = client.get("/api/admin/rules", headers=_auth(token))
    assert rules.status_code == 200 and rules.json()

    health = client.get("/api/admin/system-health", headers=_auth(token)).json()
    assert any(check["component"].startswith("Database") for check in health)

    logs = client.get("/api/admin/audit-logs", headers=_auth(token)).json()
    assert any(log["action"] == "SCAN_CREATED" for log in logs)

    backup = client.post("/api/admin/backup", headers=_auth(token))
    assert backup.status_code == 200
    download = client.get(backup.json()["download_url"], headers=_auth(token))
    assert download.status_code == 200
    assert "scans" in download.json()


def test_new_user_flow(client, token):
    created = client.post(
        "/api/admin/users",
        headers=_auth(token),
        json={"name": "Inspector One", "email": "inspector@metrology.gov.in",
              "password": "secret123", "role": "inspector"},
    )
    assert created.status_code == 201, created.text
    user_id = created.json()["id"]

    login = client.post(
        "/api/auth/login",
        json={"email": "inspector@metrology.gov.in", "password": "secret123"},
    )
    assert login.status_code == 200
    inspector_token = login.json()["access_token"]

    # An inspector may NOT list users.
    assert client.get("/api/admin/users", headers=_auth(inspector_token)).status_code == 403

    toggled = client.patch(
        f"/api/admin/users/{user_id}/toggle-active", headers=_auth(token)
    )
    assert toggled.status_code == 200 and toggled.json()["is_active"] is False

    assert client.delete(f"/api/admin/users/{user_id}", headers=_auth(token)).status_code == 204


def test_pdf_reports(client, token):
    scan_id = client.get("/api/scans", headers=_auth(token)).json()["items"][0]["id"]

    report = client.get(f"/api/scans/{scan_id}/report", headers=_auth(token))
    assert report.status_code == 200
    assert report.headers["content-type"] == "application/pdf"
    assert report.content[:4] == b"%PDF"

    summary = client.get("/api/admin/summary-report", headers=_auth(token))
    assert summary.status_code == 200
    assert summary.content[:4] == b"%PDF"


def test_delete_scan_requires_admin(client, token):
    scan_id = client.post(
        "/api/scans",
        headers=_auth(token),
        files={"image": ("later.jpg", _jpeg_bytes(), "image/jpeg")},
    ).json()["id"]
    assert client.delete(f"/api/scans/{scan_id}", headers=_auth(token)).status_code == 204
    assert client.get(f"/api/scans/{scan_id}", headers=_auth(token)).status_code == 404


def test_indexes_created(client):
    names = set(database.scans.index_information())
    assert "uniq_scan_id" in names
    assert "uniq_email" in set(database.users.index_information())
