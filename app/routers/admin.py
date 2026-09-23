import json
import os
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from app import crud, database, models, schemas
from app import auth as auth_utils
from app.config import settings
from app.services import ocr_service, ai_service, pdf_service

router = APIRouter(prefix="/api/admin", tags=["Admin"])

# The compliance rules the rule engine actually enforces - shown in Rule
# Management so the table reflects reality, not hardcoded sample rows.
REAL_RULES = [
    {"code": "MISSING_MRP", "name": "MRP Declaration Rule", "category": "ProductInfo", "severity": "major", "rule_reference": "Rule 6(1)(e)"},
    {"code": "MISSING_NET_QUANTITY", "name": "Quantity Declaration Rule", "category": "Packaging", "severity": "major", "rule_reference": "Rule 6(1)(b) / Rule 8"},
    {"code": "MISSING_MANUFACTURER", "name": "Manufacturer Details Rule", "category": "ProductInfo", "severity": "major", "rule_reference": "Rule 6(1)(a)"},
    {"code": "MISSING_MFG_DATE", "name": "Date Declaration Rule", "category": "Date", "severity": "major", "rule_reference": "Rule 6(1)(f)"},
    {"code": "MISSING_CONSUMER_CARE", "name": "Consumer Care Details Rule", "category": "Contact", "severity": "minor", "rule_reference": "Rule 6(1)(d)"},
    {"code": "INVALID_MRP_FORMAT", "name": "MRP Format Validation", "category": "ProductInfo", "severity": "minor", "rule_reference": "Rule 6(1)(e)"},
    {"code": "INVALID_MRP_VALUE", "name": "MRP Positive Value Check", "category": "ProductInfo", "severity": "major", "rule_reference": "Rule 6(1)(e)"},
    {"code": "NON_STANDARD_UNIT", "name": "Standard Metric Unit Check", "category": "Packaging", "severity": "minor", "rule_reference": "Rule 8"},
    {"code": "AI_FLAGGED_LABEL", "name": "AI Label Quality Check", "category": "AI Vision", "severity": "major", "rule_reference": "Rule 5"},
]

BACKUP_PREFIX = "metrology_backup_"


def _role_value(role) -> str:
    return role.value if hasattr(role, "value") else str(role)


def _admin_user(user: models.Doc, scan_count: int = 0) -> schemas.AdminUserOut:
    return schemas.AdminUserOut(
        id=user.id,
        name=user.name,
        email=user.email,
        role=_role_value(user.role),
        is_active=user.is_active,
        created_at=user.created_at,
        scan_count=int(scan_count),
    )


@router.get("/users", response_model=list[schemas.AdminUserOut])
def list_users(current_user: models.Doc = Depends(auth_utils.require_roles("admin"))):
    """All users with name, email, role, status and their scan counts."""
    counts = crud.scan_counts_by_inspector()
    return [_admin_user(u, counts.get(u.id, 0)) for u in crud.list_users()]


@router.post("/users", response_model=schemas.AdminUserOut, status_code=201)
def create_user(
    payload: schemas.UserCreate,
    current_user: models.Doc = Depends(auth_utils.require_roles("admin")),
):
    if crud.get_user_by_email(payload.email):
        raise HTTPException(status_code=400, detail="A user with this email already exists")
    if payload.role not in [r.value for r in models.UserRole]:
        raise HTTPException(status_code=400, detail="Invalid role")

    user = crud.create_user(
        name=payload.name,
        email=payload.email,
        hashed_password=auth_utils.hash_password(payload.password),
        role=payload.role,
    )
    crud.add_audit_log(
        current_user.id, "USER_CREATED", f"Created user {payload.email} with role {payload.role}"
    )
    return _admin_user(user, 0)


@router.patch("/users/{user_id}/toggle-active", response_model=schemas.AdminUserOut)
def toggle_user_active(
    user_id: str,
    current_user: models.Doc = Depends(auth_utils.require_roles("admin")),
):
    user = crud.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot disable your own account")

    updated = crud.set_user_active(user_id, not user.is_active)
    crud.add_audit_log(
        current_user.id,
        "USER_ACCESS_MODIFIED",
        f"{'Enabled' if updated.is_active else 'Disabled'} user {updated.email}",
    )
    counts = crud.scan_counts_by_inspector()
    return _admin_user(updated, counts.get(updated.id, 0))


@router.delete("/users/{user_id}", status_code=204)
def delete_user(
    user_id: str,
    current_user: models.Doc = Depends(auth_utils.require_roles("admin")),
):
    user = crud.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot delete your own account")
    crud.delete_user(user_id)
    crud.add_audit_log(current_user.id, "USER_DELETED", f"Deleted user {user.email}")
    return


@router.get("/system-health", response_model=list[schemas.SystemHealth])
def system_health(current_user: models.Doc = Depends(auth_utils.require_roles("admin"))):
    """Lightweight health probes the AdminPanel's 'System Health' widget can poll."""
    checks = []

    checks.append(schemas.SystemHealth(
        component="Database (MongoDB)",
        status="Operational" if database.ping() else "Unreachable",
    ))

    model_ok = settings.CLASSIFIER_ENABLED and os.path.exists(settings.MODEL_PATH)
    checks.append(schemas.SystemHealth(
        component="AI Label Classifier",
        status="Operational" if model_ok else (
            "Disabled" if not settings.CLASSIFIER_ENABLED else "Unavailable"
        ),
    ))

    try:
        storage_ok = os.access(settings.UPLOAD_DIR, os.W_OK)
    except OSError:
        storage_ok = False
    checks.append(schemas.SystemHealth(
        component="File Storage", status="Operational" if storage_ok else "Degraded"
    ))

    try:
        import pytesseract
        pytesseract.get_tesseract_version()
        ocr_ok = True
    except Exception:
        ocr_ok = False
    checks.append(schemas.SystemHealth(
        component="OCR Engine (Tesseract)", status="Operational" if ocr_ok else "Unavailable"
    ))

    checks.append(schemas.SystemHealth(
        component="OCR Engine (PaddleOCR)",
        status="Operational" if ocr_service.is_paddle_available() else "Unavailable (auto-falls back to Tesseract)",
    ))

    checks.append(schemas.SystemHealth(
        component="AI Extraction (OpenRouter)",
        status="Operational" if ai_service.is_ai_configured() else "Unavailable (rule-engine fallback active)",
    ))

    checks.append(schemas.SystemHealth(
        component="Scan Cache (80% similarity)",
        status=f"Operational (threshold {settings.SIMILARITY_THRESHOLD}%)",
    ))

    return checks


@router.get("/audit-logs")
def audit_logs(
    limit: int = 50,
    current_user: models.Doc = Depends(auth_utils.require_roles("admin")),
):
    return crud.list_audit_logs(limit)


@router.get("/system-stats")
def system_stats(current_user: models.Doc = Depends(auth_utils.require_roles("admin"))):
    """All-time figures for the Admin KPI cards + status split for the donut."""
    total = crud.count_scans()
    by_status = crud.count_by_status()
    passed = by_status.get(models.ScanStatus.PASSED.value, 0)
    failed = by_status.get(models.ScanStatus.FAILED.value, 0)
    pending = by_status.get(models.ScanStatus.PENDING_REVIEW.value, 0)
    ai_scans = crud.count_ai_scans()
    avg_conf, avg_score = crud.avg_metrics()
    cache_hits = crud.count_audit_logs("SCAN_CACHE_HIT")
    users = crud.count_users()

    return {
        "total_inspections": total,
        "passed": passed,
        "failed": failed,
        "pending": pending,
        "compliance_rate": round((passed / total) * 100, 1) if total else 0.0,
        "ai_scans": ai_scans,
        "cache_hits": cache_hits,
        "total_users": users,
        "avg_overall_confidence": round(avg_conf, 1),
        "avg_compliance_score": round(avg_score, 1),
    }


@router.get("/trend")
def trend(
    days: int = 14,
    current_user: models.Doc = Depends(auth_utils.require_roles("admin")),
):
    """Real inspection/violation counts per day for the trend chart."""
    days = max(1, min(days, 60))
    start = datetime.utcnow() - timedelta(days=days)

    by_day = crud.daily_counts(start)
    failed_by_day = crud.daily_counts(start, status=models.ScanStatus.FAILED.value)

    series = []
    for i in range(days):
        d = (datetime.utcnow() - timedelta(days=days - 1 - i)).date()
        key = d.isoformat()
        series.append({
            "date": key,
            "inspections": by_day.get(key, 0),
            "violations": failed_by_day.get(key, 0),
        })
    return series


@router.get("/rules")
def list_rules(current_user: models.Doc = Depends(auth_utils.require_roles("admin"))):
    """The actual rule set the compliance engine enforces."""
    return REAL_RULES


@router.post("/backup")
def backup_database(current_user: models.Doc = Depends(auth_utils.require_roles("admin"))):
    """Backup Now: export every collection to a JSON file that can be downloaded.

    MongoDB (Atlas) also keeps its own snapshots; this export is a portable
    copy the operator can keep on their machine, and it is the file the
    Admin Panel's download button streams.
    """
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{BACKUP_PREFIX}{timestamp}.json"
    backup_path = os.path.join(settings.REPORTS_DIR, backup_name)

    payload = crud.export_all()
    with open(backup_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    crud.add_audit_log(
        current_user.id, "BACKUP_CREATED", f"Database export {backup_name} created"
    )
    return {
        "detail": "Backup created",
        "file": backup_name,
        "download_url": f"/api/admin/backup-download?file={backup_name}",
    }


@router.get("/backup-download")
def backup_download(
    file: str,
    current_user: models.Doc = Depends(auth_utils.require_roles("admin")),
):
    """Stream a previously created backup file (name validated, no traversal)."""
    if "/" in file or "\\" in file or ".." in file or not file.startswith(BACKUP_PREFIX):
        raise HTTPException(status_code=400, detail="Invalid backup filename")
    path = os.path.join(settings.REPORTS_DIR, file)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Backup not found")
    return FileResponse(path, media_type="application/json", filename=file)


@router.get("/summary-report")
def summary_report(current_user: models.Doc = Depends(auth_utils.get_current_user)):
    """Generate System Report: one PDF with all-time compliance analytics.

    Any authenticated user can generate it (the Reports screen is available to
    inspectors too); the Admin Panel Quick Action calls the same endpoint.
    """
    total = crud.count_scans()
    by_status = crud.count_by_status()
    passed = by_status.get(models.ScanStatus.PASSED.value, 0)
    failed = by_status.get(models.ScanStatus.FAILED.value, 0)
    pending = by_status.get(models.ScanStatus.PENDING_REVIEW.value, 0)
    rate = round((passed / total) * 100, 1) if total else 0.0

    top_violations = crud.top_violations(limit=10)
    inspectors = crud.inspector_activity()

    pdf_path = pdf_service.generate_summary_report(
        total=total, passed=passed, failed=failed, pending=pending,
        compliance_rate=rate, top_violations=top_violations, inspectors=inspectors,
    )
    return FileResponse(
        pdf_path, media_type="application/pdf",
        filename=os.path.basename(pdf_path),
    )
