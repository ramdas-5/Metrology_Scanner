from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query

from app import crud, models, schemas
from app import auth as auth_utils

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


def _parse_date(value: Optional[str]) -> Optional[datetime]:
    """Accept 'YYYY-MM-DD' (and 'YYYY-MM-DD HH:MM') date filters."""
    if not value:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(value.strip(), fmt)
        except ValueError:
            continue
    return None


def _resolve_window(
    period: str, from_date: Optional[str], to_date: Optional[str]
) -> tuple[Optional[datetime], Optional[datetime]]:
    """from_date/to_date override the Daily/Weekly/Monthly preset when given."""
    start = None if (from_date or to_date) else _period_start(period)
    return start, _parse_date(to_date)


@router.get("/stats", response_model=schemas.DashboardStats)
def get_dashboard_stats(
    period: str = Query("Daily", description="Daily | Weekly | Monthly | All"),
    from_date: Optional[str] = Query(None, description="YYYY-MM-DD (inclusive)"),
    to_date: Optional[str] = Query(None, description="YYYY-MM-DD (inclusive)"),
    status: Optional[str] = Query(None, description="Passed | Failed | Pending Review"),
    current_user: models.Doc = Depends(auth_utils.get_current_user),
):
    """
    Backs both the main Dashboard and the Reports summary cards.

    period is a quick preset (Daily/Weekly/Monthly); when from_date/to_date are
    supplied they override the preset so the Reports screen filters really work.
    """
    period_start, to_dt = _resolve_window(period, from_date, to_date)
    match = crud.build_scan_match(
        status=status,
        from_date=period_start or _parse_date(from_date),
        to_date=to_dt,
    )

    total = crud.count_scans(match)
    compliant = crud.count_scans({**match, "status": models.ScanStatus.PASSED.value})
    violations_count = crud.count_violations(match)
    compliance_rate = round((compliant / total) * 100, 1) if total else 0.0

    # Top violation labels across every violation row in the same window.
    violation_rows = crud.top_violations(match, limit=5)
    total_violations_for_pct = sum(c for _, c in violation_rows) or 1
    top_violations = [
        {
            "label": label,
            "value": count,
            "percentage": f"{round((count / total_violations_for_pct) * 100, 1)}%",
        }
        for label, count in violation_rows
    ]

    return schemas.DashboardStats(
        total_inspections=total,
        compliant=compliant,
        violations=violations_count,
        compliance_rate=compliance_rate,
        top_violations=top_violations,
    )


@router.get("/recent-activity")
def recent_activity(
    limit: int = 10,
    current_user: models.Doc = Depends(auth_utils.get_current_user),
):
    """Latest audit-log events for the notification bell (with actor names)."""
    return crud.recent_activity(limit)
