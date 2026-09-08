from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app import models, schemas, auth as auth_utils
from app.database import get_db

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard & Reports"])


def _period_start(period: str) -> Optional[datetime]:
    now = datetime.utcnow()
    if period == "Weekly":
        return now - timedelta(days=7)
    if period == "Monthly":
        return now - timedelta(days=30)
    if period == "Daily":
        return now - timedelta(days=1)
    return None


@router.get("/stats", response_model=schemas.DashboardStats)
def get_dashboard_stats(
    period: str = Query("Daily", description="Daily | Weekly | Monthly | All"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_utils.get_current_user),
):
    """Backs both the main Dashboard and the Reports summary cards."""
    q = db.query(models.Scan)
    start = _period_start(period)
    if start:
        q = q.filter(models.Scan.created_at >= start)

    total = q.count()
    compliant = q.filter(models.Scan.status == models.ScanStatus.PASSED).count()
    failed = q.filter(models.Scan.status == models.ScanStatus.FAILED).count()
    compliance_rate = round((compliant / total) * 100, 1) if total else 0.0

    violation_counts = (
        db.query(models.Violation.label, func.count(models.Violation.id))
        .join(models.Scan, models.Scan.id == models.Violation.scan_id)
        .filter(models.Scan.created_at >= start) if start else
        db.query(models.Violation.label, func.count(models.Violation.id))
    )
    if start:
        violation_rows = violation_counts.group_by(models.Violation.label).order_by(func.count(models.Violation.id).desc()).limit(5).all()
    else:
        violation_rows = violation_counts.group_by(models.Violation.label).order_by(func.count(models.Violation.id).desc()).limit(5).all()

    total_violations_for_pct = sum(c for _, c in violation_rows) or 1
    top_violations = [
        {"label": label, "value": count, "percentage": f"{round((count/total_violations_for_pct)*100, 1)}%"}
        for label, count in violation_rows
    ]

    return schemas.DashboardStats(
        total_inspections=total,
        compliant=compliant,
        violations=failed,
        compliance_rate=compliance_rate,
        top_violations=top_violations,
    )


@router.get("/recent-activity")
def recent_activity(
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_utils.get_current_user),
):
    logs = db.query(models.AuditLog).order_by(models.AuditLog.created_at.desc()).limit(limit).all()
    return [
        {
            "id": log.id,
            "action": log.action,
            "details": log.details,
            "created_at": log.created_at,
            "user_id": log.user_id,
        }
        for log in logs
    ]
