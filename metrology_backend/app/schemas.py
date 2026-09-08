from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, EmailStr, ConfigDict


# ---------------- Auth ----------------

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str = "inspector"   # admin | inspector | viewer


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    email: str
    role: str
    is_active: bool
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class AdminUserOut(BaseModel):
    """User row for the Admin Panel: includes email and per-inspector scan count."""
    id: str
    name: str
    email: str
    role: str
    is_active: bool
    created_at: datetime
    scan_count: int = 0


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


# ---------------- Scans ----------------

class ViolationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    code: str
    label: str
    severity: str
    rule_reference: Optional[str] = None
    description: Optional[str] = None


class ScanOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    product_name: Optional[str]
    image_path: Optional[str]
    mrp: Optional[str]
    net_quantity: Optional[str]
    manufacturer: Optional[str]
    mfg_date: Optional[str]
    consumer_care: Optional[str]
    country_of_origin: Optional[str]
    unit_sale_price: Optional[str]
    overall_confidence: float
    label_classifier_result: Optional[str]
    label_classifier_confidence: float
    status: str
    compliance_score: float
    created_at: datetime
    violations: List[ViolationOut] = []

    # Inspector who performed the scan (joined from users table)
    inspector_name: Optional[str] = None
    inspector_email: Optional[str] = None

    # AI extraction pipeline metadata (columns on Scan)
    ocr_engine: Optional[str] = None
    ai_used: bool = False
    ai_model: Optional[str] = None
    ai_report: Optional[str] = None

    # Response-only flags, set by the API when a scan was served from the
    # 80% similarity cache instead of being re-processed.
    cached: bool = False
    similarity: Optional[float] = None


class ScanUpdate(BaseModel):
    product_name: Optional[str] = None
    mrp: Optional[str] = None
    net_quantity: Optional[str] = None
    manufacturer: Optional[str] = None
    mfg_date: Optional[str] = None
    consumer_care: Optional[str] = None
    country_of_origin: Optional[str] = None
    unit_sale_price: Optional[str] = None


class ScanListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    product_name: Optional[str]
    mrp: Optional[str]
    mfg_date: Optional[str]
    status: str
    compliance_score: float
    created_at: datetime
    inspector_name: Optional[str] = None
    inspector_email: Optional[str] = None


# ---------------- Dashboard ----------------

class DashboardStats(BaseModel):
    total_inspections: int
    compliant: int
    violations: int
    compliance_rate: float
    top_violations: List[dict]


# ---------------- Admin ----------------

class SystemHealth(BaseModel):
    component: str
    status: str
