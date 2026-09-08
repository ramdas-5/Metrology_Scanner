import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text, Enum
)
from sqlalchemy.orm import relationship

from app.database import Base


def gen_id():
    return uuid.uuid4().hex


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    INSPECTOR = "inspector"
    VIEWER = "viewer"


class ScanStatus(str, enum.Enum):
    PASSED = "Passed"
    FAILED = "Failed"
    PENDING_REVIEW = "Pending Review"


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=gen_id)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.INSPECTOR, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    scans = relationship("Scan", back_populates="inspector")


class Scan(Base):
    __tablename__ = "scans"

    id = Column(String, primary_key=True, default=gen_id)
    inspector_id = Column(String, ForeignKey("users.id"), nullable=True)

    product_name = Column(String, nullable=True)
    image_path = Column(String, nullable=True)

    # OCR extracted declarations (mandatory fields under LM(PC) Rules 2011)
    mrp = Column(String, nullable=True)
    net_quantity = Column(String, nullable=True)
    manufacturer = Column(String, nullable=True)
    mfg_date = Column(String, nullable=True)
    consumer_care = Column(String, nullable=True)
    country_of_origin = Column(String, nullable=True)
    unit_sale_price = Column(String, nullable=True)

    # OCR / model confidence
    ocr_raw_text = Column(Text, nullable=True)
    overall_confidence = Column(Float, default=0.0)
    label_classifier_result = Column(String, nullable=True)   # e.g. "Compliant Label"
    label_classifier_confidence = Column(Float, default=0.0)

    # AI extraction pipeline (OCR -> OpenRouter -> fixed JSON verdict/report)
    ocr_engine = Column(String, nullable=True)            # engine actually used: paddle | tesseract
    ai_used = Column(Boolean, default=False)              # True when fields/verdict came from the LLM
    ai_model = Column(String, nullable=True)              # OpenRouter model that produced the result
    ai_report = Column(Text, nullable=True)               # AI-written / generated narrative summary
    ai_extracted_json = Column(Text, nullable=True)       # raw structured JSON returned by the AI (audit)

    # Compliance result
    status = Column(Enum(ScanStatus), default=ScanStatus.PENDING_REVIEW)
    compliance_score = Column(Float, default=0.0)

    created_at = Column(DateTime, default=datetime.utcnow)

    inspector = relationship("User", back_populates="scans")
    violations = relationship("Violation", back_populates="scan", cascade="all, delete-orphan")

    # Computed attributes so the API schemas (ScanOut / ScanListItem) can
    # expose the inspector's identity with from_attributes=True.
    @property
    def inspector_name(self):
        return self.inspector.name if self.inspector else None

    @property
    def inspector_email(self):
        return self.inspector.email if self.inspector else None


class Violation(Base):
    __tablename__ = "violations"

    id = Column(String, primary_key=True, default=gen_id)
    scan_id = Column(String, ForeignKey("scans.id"), nullable=False)

    code = Column(String, nullable=False)          # e.g. MISSING_MRP
    label = Column(String, nullable=False)          # human readable
    severity = Column(String, default="major")      # major / minor
    rule_reference = Column(String, nullable=True)  # e.g. "Rule 6(1)(a)"
    description = Column(Text, nullable=True)

    scan = relationship("Scan", back_populates="violations")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True, default=gen_id)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    action = Column(String, nullable=False)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

