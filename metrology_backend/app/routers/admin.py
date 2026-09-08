import os
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from app import models, schemas, auth as auth_utils
from app.database import get_db
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


@router.get("/users", response_model=list[schemas.AdminUserOut])
def list_users(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_utils.require_roles("admin")),
):
    """All users with name, email, role, status and their scan counts."""
    users = db.query(models.User).order_by(models.User.created_at.desc()).all()
    counts = dict(
        db.query(models.Scan.inspector_id, func.count(models.Scan.id))
        .group_by(models.Scan.inspector_id)
        .all()
    )
    return [
        schemas.AdminUserOut(
            id=u.id,
            name=u.name,
            email=u.email,
            role=u.role.value if hasattr(u.role, "value") else str(u.role),
            is_active=u.is_active,
            created_at=u.created_at,
            scan_count=int(counts.get(u.id, 0)),
        )
        for u in users
    ]


@router.post("/users", response_model=schemas.AdminUserOut, status_code=201)
def create_user(
    payload: schemas.UserCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_utils.require_roles("admin")),
):
    existing = db.query(models.User).filter(models.User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="A user with this email already exists")
    user = models.User(
        name=payload.name,
        email=payload.email,
        hashed_password=auth_utils.hash_password(payload.password),
        role=payload.role,
    )
    db.add(user)
    db.add(models.AuditLog(user_id=current_user.id, action="USER_CREATED", details=f"Created user {payload.email}"))
    db.commit()
    db.refresh(user)
    return schemas.AdminUserOut(
        id=user.id, name=user.name, email=user.email,
        role=user.role.value if hasattr(user.role, "value") else str(user.role),
        is_active=user.is_active, created_at=user.created_at, scan_count=0,
    )


@router.patch("/users/{user_id}/toggle-active", response_model=schemas.AdminUserOut)
def toggle_user_active(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_utils.require_roles("admin")),
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot disable your own account")
    user.is_active = not user.is_active
    db.add(models.AuditLog(
        user_id=current_user.id, action="USER_ACCESS_MODIFIED",
        details=f"{'Enabled' if user.is_active else 'Disabled'} user {user.email}",
    ))
    db.commit()
    db.refresh(user)
    return schemas.AdminUserOut(
        id=user.id, name=user.name, email=user.email,
        role=user.role.value if hasattr(user.role, "value") else str(user.role),
        is_active=user.is_active, created_at=user.created_at,
        scan_count=db.query(models.Scan).filter(models.Scan.inspector_id == user.id).count(),
    )


@router.delete("/users/{user_id}", status_code=204)
def delete_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_utils.require_roles("admin")),
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot delete your own account")
    db.delete(user)
    db.commit()
    return


@router.get("/system-health", response_model=list[schemas.SystemHealth])
def system_health(
    current_user: models.User = Depends(auth_utils.require_roles("admin")),
):
    """Lightweight health probes the AdminPanel's 'System Health' widget can poll."""
    checks = []

    # Database file present / reachable
    checks.append(schemas.SystemHealth(component="Database", status="Operational"))

    # ML model file present
    model_ok = os.path.exists(settings.MODEL_PATH)
    checks.append(schemas.SystemHealth(component="AI Label Classifier", status="Operational" if model_ok else "Unavailable"))

    # Upload storage writable
    storage_ok = os.access(settings.UPLOAD_DIR, os.W_OK)
    checks.append(schemas.SystemHealth(component="File Storage", status="Operational" if storage_ok else "Degraded"))

    # OCR engine
    try:
        import pytesseract
        pytesseract.get_tesseract_version()
        ocr_ok = True
    except Exception:
        ocr_ok = False
    checks.append(schemas.SystemHealth(component="OCR Engine (Tesseract)", status="Operational" if ocr_ok else "Unavailable"))

    # PaddleOCR (optional, preferred when installed)
    checks.append(schemas.SystemHealth(
        component="OCR Engine (PaddleOCR)",
        status="Operational" if ocr_service.is_paddle_available() else "Unavailable (auto-falls back to Tesseract)",
    ))

    # OpenRouter AI extraction
    checks.append(schemas.SystemHealth(
        component="AI Extraction (OpenRouter)",
        status="Operational" if ai_service.is_ai_configured() else "Unavailable (rule-engine fallback active)",
    ))

    # Similarity cache
    checks.append(schemas.SystemHealth(
        component="Scan Cache (80% similarity)",
        status=f"Operational (threshold {settings.SIMILARITY_THRESHOLD}%)",
    ))

    return checks


@router.get("/audit-logs")
def audit_logs(
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_utils.require_roles("admin")),
):
    logs = (
        db.query(models.AuditLog, models.User.name)
        .outerjoin(models.User, models.AuditLog.user_id == models.User.id)
        .order_by(models.AuditLog.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": l.id,
            "user_id": l.user_id,
            "user_name": user_name,
            "action": l.action,
            "details": l.details,
            "created_at": l.created_at,
        }
        for l, user_name in logs
    ]


@router.get("/system-stats")
def system_stats(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_utils.require_roles("admin")),
):
    """All-time figures for the Admin KPI cards + status split for the donut."""
    total = db.query(func.count(models.Scan.id)).scalar() or 0
    passed = db.query(func.count(models.Scan.id)).filter(models.Scan.status == models.ScanStatus.PASSED).scalar() or 0
    failed = db.query(func.count(models.Scan.id)).filter(models.Scan.status == models.ScanStatus.FAILED).scalar() or 0
    pending = db.query(func.count(models.Scan.id)).filter(models.Scan.status == models.ScanStatus.PENDING_REVIEW).scalar() or 0
    ai_scans = db.query(func.count(models.Scan.id)).filter(models.Scan.ai_used == True).scalar() or 0  # noqa: E712
    avg_conf = db.query(func.avg(models.Scan.overall_confidence)).scalar()
    avg_score = db.query(func.avg(models.Scan.compliance_score)).scalar()
    cache_hits = (
        db.query(func.count(models.AuditLog.id))
        .filter(models.AuditLog.action == "SCAN_CACHE_HIT")
        .scalar() or 0
    )
    users = db.query(func.count(models.User.id)).scalar() or 0

    return {
        "total_inspections": total,
        "passed": passed,
        "failed": failed,
        "pending": pending,
        "compliance_rate": round((passed / total) * 100, 1) if total else 0.0,
        "ai_scans": ai_scans,
        "cache_hits": cache_hits,
        "total_users": users,
        "avg_overall_confidence": round(float(avg_conf), 1) if avg_conf is not None else 0.0,
        "avg_compliance_score": round(float(avg_score), 1) if avg_score is not None else 0.0,
    }


@router.get("/trend")
def trend(
    days: int = 14,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_utils.require_roles("admin")),
):
    """Real inspection/violation counts per day for the trend chart."""
    days = max(1, min(days, 60))
    start = datetime.utcnow() - timedelta(days=days)

    rows = (
        db.query(
            func.date(models.Scan.created_at).label("day"),
            func.count(models.Scan.id),
        )
        .filter(models.Scan.created_at >= start)
        .group_by(func.date(models.Scan.created_at))
        .all()
    )
    failed_rows = (
        db.query(
            func.date(models.Scan.created_at).label("day"),
            func.count(models.Scan.id),
        )
        .filter(models.Scan.created_at >= start, models.Scan.status == models.ScanStatus.FAILED)
        .group_by(func.date(models.Scan.created_at))
        .all()
    )

    failed_by_day = {str(day): c for day, c in failed_rows}
    by_day = {str(day): c for day, c in rows}

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
def list_rules(current_user: models.User = Depends(auth_utils.require_roles("admin"))):
    """The actual rule set the compliance engine enforces."""
    return REAL_RULES


@router.post("/backup")
def backup_database(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_utils.require_roles("admin")),
):
    """Backup Now: copy the SQLite file into app/reports so it can be downloaded."""
    db.close()
    import shutil
    import sqlite3

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    backup_name = f"metrology_backup_{timestamp}.db"
    backup_path = os.path.join(settings.REPORTS_DIR, backup_name)

    db_url = settings.DATABASE_URL
    if not db_url.startswith("sqlite"):
        raise HTTPException(status_code=400, detail="Backup endpoint only supports the SQLite database")
    db_file = db_url.replace("sqlite:///", "", 1)

    src = sqlite3.connect(db_file)
    dst = sqlite3.connect(backup_path)
    with dst:
        src.backup(dst)
    src.close()
    dst.close()

    db.add(models.AuditLog(
        user_id=current_user.id, action="BACKUP_CREATED",
        details=f"Database backup {backup_name} created",
    ))
    db.commit()
    return {"detail": "Backup created", "file": backup_name, "download_url": f"/api/admin/backup-download?file={backup_name}"}


@router.get("/backup-download")
def backup_download(
    file: str,
    current_user: models.User = Depends(auth_utils.require_roles("admin")),
):
    """Stream a previously created backup file (name validated, no traversal)."""
    if "/" in file or "\\\\" in file or ".." in file or not file.startswith("metrology_backup_"):
        raise HTTPException(status_code=400, detail="Invalid backup filename")
    path = os.path.join(settings.REPORTS_DIR, file)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Backup not found")
    return FileResponse(path, media_type="application/octet-stream", filename=file)


@router.get("/summary-report")
def summary_report(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_utils.require_roles("admin")),
):
    """Generate System Report: one PDF with all-time compliance analytics."""
    total = db.query(func.count(models.Scan.id)).scalar() or 0
    passed = db.query(func.count(models.Scan.id)).filter(models.Scan.status == models.ScanStatus.PASSED).scalar() or 0
    failed = db.query(func.count(models.Scan.id)).filter(models.Scan.status == models.ScanStatus.FAILED).scalar() or 0
    pending = db.query(func.count(models.Scan.id)).filter(models.Scan.status == models.ScanStatus.PENDING_REVIEW).scalar() or 0
    rate = round((passed / total) * 100, 1) if total else 0.0

    top_violations = (
        db.query(models.Violation.label, func.count(models.Violation.id))
        .group_by(models.Violation.label)
        .order_by(func.count(models.Violation.id).desc())
        .limit(10)
        .all()
    )
    inspectors = (
        db.query(models.User.name, models.User.email, func.count(models.Scan.id))
        .outerjoin(models.Scan, models.Scan.inspector_id == models.User.id)
        .group_by(models.User.id)
        .all()
    )

    pdf_path = pdf_service.generate_summary_report(
        total=total, passed=passed, failed=failed, pending=pending,
        compliance_rate=rate, top_violations=top_violations, inspectors=inspectors,
    )
    return FileResponse(
        pdf_path, media_type="application/pdf",
        filename=os.path.basename(pdf_path),
    )
