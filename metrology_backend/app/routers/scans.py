import json
import logging
import os
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session, joinedload

from app import models, schemas, auth as auth_utils
from app.database import get_db
from app.config import settings
from app.services import (
    ocr_service,
    classifier_service,
    compliance_engine,
    pdf_service,
    ai_service,
    dedupe_service,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/scans", tags=["Scans"])

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

DECLARATION_FIELDS = [
    "mrp",
    "net_quantity",
    "manufacturer",
    "mfg_date",
    "consumer_care",
    "country_of_origin",
    "unit_sale_price",
]


def _save_upload(file: UploadFile) -> str:
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        ext = ".jpg"
    filename = f"{uuid.uuid4().hex}{ext}"
    path = os.path.join(settings.UPLOAD_DIR, filename)
    with open(path, "wb") as f:
        f.write(file.file.read())
    return path


def _run_classifier(image_path: str):
    """Best-effort label classifier; never fails the scan when unavailable.

    A missing/unloaded model raises before running, so an unloaded TF model
    never blocks the scan (important for keeping scans fast).
    """
    try:
        return classifier_service.classify_image(image_path)
    except Exception as exc:
        logger.warning("Label classifier unavailable (%s); continuing without it.", exc)
        return None


def _merge_multi_side_text(texts: list[str]) -> str:
    """Combine the OCR text of several sides of the same package into one
    document with clear side markers so the AI/parser treats them as one label."""
    parts = []
    for i, t in enumerate(texts, start=1):
        t = (t or "").strip()
        if not t:
            continue
        parts.append(f"=== Side {i} ===\n{t}")
    return "\n\n".join(parts).strip()


@router.post("", response_model=schemas.ScanOut, status_code=201)
def create_scan(
    image: UploadFile = File(...),
    product_name: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_utils.get_current_user),
):
    """
    Main scanning endpoint used by the "New Scan" screen. Accepts *any*
    image and runs the full pipeline:

      1. OCR - extract as much text as possible (PaddleOCR if installed,
         otherwise Tesseract; engine chosen via OCR_ENGINE in .env).
      2. Dedupe / cache - if the extracted text is >= SIMILARITY_THRESHOLD%
         (default 80) similar to a previously saved scan, return that saved
         result straight from the DB - no AI call, no duplicate row.
      3. AI extraction - when OPENROUTER_API_KEY is set, one OpenRouter call
         converts the raw text into the fixed JSON (declarations + compliance
         score/status/violations + narrative report) which is stored as-is.
      4. Fallback - when no API key is set (or the AI call fails), the
         deterministic regex parser + Legal Metrology rule engine runs
         instead, so the app keeps working offline.
    """
    image_path = _save_upload(image)

    # ---- 1. OCR: any image -> as much text as possible ----
    try:
        ocr = ocr_service.run_ocr_engine(image_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR processing failed: {e}")
    raw_text = ocr["text"] or ""
    ocr_engine = ocr["engine"]

    # ---- 2. Dedupe / cache: return the saved value when >= 80% similar ----
    if raw_text.strip():
        match_id, score, _ = dedupe_service.find_similar_scan(db, raw_text)
        if match_id:
            cached_scan = (
                db.query(models.Scan)
                .options(joinedload(models.Scan.violations), joinedload(models.Scan.inspector))
                .filter(models.Scan.id == match_id)
                .first()
            )
            if cached_scan:
                db.add(models.AuditLog(
                    user_id=current_user.id,
                    action="SCAN_CACHE_HIT",
                    details=(
                        f"OCR text {score}% similar to saved scan {cached_scan.id}; "
                        "returned saved result and skipped the AI call."
                    ),
                ))
                db.commit()
                out = schemas.ScanOut.model_validate(cached_scan)
                out.cached = True
                out.similarity = score
                return out

    classifier_result = _run_classifier(image_path)

    # ---- 3. AI extraction (OpenRouter) when configured ----
    ai_payload = None
    ai_used = False
    ai_model = None
    report = None

    if ai_service.is_ai_configured():
        try:
            ai_payload = ai_service.extract_label_data(raw_text, product_name=product_name)
            ai_used = True
            ai_model = ai_payload.get("model")
        except ai_service.AIExtractionError as exc:
            logger.warning("AI extraction failed; falling back to rule engine: %s", exc)
            ai_payload = None

    if ai_payload:
        # The AI computed the declarations AND the metrics/report - store them.
        fields = {key: ai_payload.get(key) for key in DECLARATION_FIELDS}
        fields["ocr_raw_text"] = raw_text

        compliance_result = {
            "status": ai_payload["status"],
            "compliance_score": ai_payload["compliance_score"],
            "violations": ai_payload["violations"],
        }
        overall_confidence = ai_payload.get("overall_confidence")
        if overall_confidence is None:
            found = sum(1 for key in DECLARATION_FIELDS if fields.get(key))
            overall_confidence = round(found / len(DECLARATION_FIELDS) * 100, 1)
        report = ai_payload.get("summary") or ""
        resolved_product = (product_name or "").strip() or ai_payload.get("product_name")
    else:
        # ---- 4. Fallback: regex parser + deterministic rule engine ----
        fields = ocr_service.parse_declarations(raw_text)  # includes ocr_raw_text + overall_confidence
        compliance_result = compliance_engine.run_compliance_check(fields, classifier_result)
        overall_confidence = fields["overall_confidence"]
        report = compliance_engine.summarize_result(compliance_result, fields)
        resolved_product = product_name

    scan = models.Scan(
        inspector_id=current_user.id,
        product_name=resolved_product,
        image_path=image_path,
        mrp=fields.get("mrp"),
        net_quantity=fields.get("net_quantity"),
        manufacturer=fields.get("manufacturer"),
        mfg_date=fields.get("mfg_date"),
        consumer_care=fields.get("consumer_care"),
        country_of_origin=fields.get("country_of_origin"),
        unit_sale_price=fields.get("unit_sale_price"),
        ocr_raw_text=raw_text,
        overall_confidence=overall_confidence,
        label_classifier_result=classifier_result["label"] if classifier_result else None,
        label_classifier_confidence=classifier_result["confidence"] if classifier_result else 0.0,
        status=compliance_result["status"],
        compliance_score=compliance_result["compliance_score"],
        ocr_engine=ocr_engine,
        ai_used=ai_used,
        ai_model=ai_model,
        ai_report=report or None,
        ai_extracted_json=json.dumps(ai_payload) if ai_payload else None,
    )
    db.add(scan)
    db.flush()

    for v in compliance_result["violations"]:
        db.add(models.Violation(
            scan_id=scan.id,
            code=v["code"],
            label=v["label"],
            severity=v["severity"],
            rule_reference=v.get("rule_reference"),
            description=v.get("description"),
        ))

    source = f"OpenRouter ({ai_model})" if ai_used else "rule engine"
    db.add(models.AuditLog(
        user_id=current_user.id,
        action="SCAN_CREATED",
        details=f"Scan {scan.id} created with status {compliance_result['status']} via {source}",
    ))

    db.commit()
    db.refresh(scan)
    return scan


@router.post("/multi", response_model=schemas.ScanOut, status_code=201)
def create_multi_side_scan(
    images: list[UploadFile] = File(..., description="One or more sides of the same package"),
    product_name: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_utils.get_current_user),
):
    """
    Multi-side scan: the operator captures/uploads EVERY side of a package
    first, then hits one SCAN button. All sides are OCR-ed, the text is merged
    with '=== Side N ===' markers, and the whole package is graded in ONE
    pass - so a field printed on the back (e.g. MRP) satisfies a check even
    when it is missing from the front.
    """
    if not images:
        raise HTTPException(status_code=400, detail="At least one image is required")
    if len(images) > 6:
        raise HTTPException(status_code=400, detail="A multi-side scan accepts at most 6 images")

    saved_paths: list[str] = []
    texts: list[str] = []
    engines = set()
    for image in images:
        path = _save_upload(image)
        saved_paths.append(path)
        try:
            ocr = ocr_service.run_ocr_engine(path)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"OCR processing failed: {e}")
        texts.append(ocr["text"] or "")
        engines.add(ocr["engine"])

    raw_text = _merge_multi_side_text(texts)
    ocr_engine = "+".join(sorted(engines))

    # Cache check on the combined text (skipped for multi-side: combined text
    # is unique to this capture session, similarity would rarely match anyway).
    classifier_result = None
    for path in saved_paths[:1]:  # classify the first side only - keeps it fast
        classifier_result = _run_classifier(path)

    ai_payload = None
    ai_used = False
    ai_model = None
    report = None

    if ai_service.is_ai_configured() and raw_text.strip():
        try:
            ai_payload = ai_service.extract_label_data(raw_text, product_name=product_name)
            ai_used = True
            ai_model = ai_payload.get("model")
        except ai_service.AIExtractionError as exc:
            logger.warning("AI extraction failed; falling back to rule engine: %s", exc)
            ai_payload = None

    if ai_payload:
        fields = {key: ai_payload.get(key) for key in DECLARATION_FIELDS}
        fields["ocr_raw_text"] = raw_text

        compliance_result = {
            "status": ai_payload["status"],
            "compliance_score": ai_payload["compliance_score"],
            "violations": ai_payload["violations"],
        }
        overall_confidence = ai_payload.get("overall_confidence")
        if overall_confidence is None:
            found = sum(1 for key in DECLARATION_FIELDS if fields.get(key))
            overall_confidence = round(found / len(DECLARATION_FIELDS) * 100, 1)
        report = ai_payload.get("summary") or ""
        resolved_product = (product_name or "").strip() or ai_payload.get("product_name")
    else:
        fields = ocr_service.parse_declarations(raw_text)
        compliance_result = compliance_engine.run_compliance_check(fields, classifier_result)
        overall_confidence = fields["overall_confidence"]
        report = compliance_engine.summarize_result(compliance_result, fields)
        resolved_product = product_name

    scan = models.Scan(
        inspector_id=current_user.id,
        product_name=resolved_product,
        # Keep every side's file path so the full capture set is auditable.
        image_path=json.dumps(saved_paths) if len(saved_paths) > 1 else saved_paths[0],
        mrp=fields.get("mrp"),
        net_quantity=fields.get("net_quantity"),
        manufacturer=fields.get("manufacturer"),
        mfg_date=fields.get("mfg_date"),
        consumer_care=fields.get("consumer_care"),
        country_of_origin=fields.get("country_of_origin"),
        unit_sale_price=fields.get("unit_sale_price"),
        ocr_raw_text=raw_text,
        overall_confidence=overall_confidence,
        label_classifier_result=classifier_result["label"] if classifier_result else None,
        label_classifier_confidence=classifier_result["confidence"] if classifier_result else 0.0,
        status=compliance_result["status"],
        compliance_score=compliance_result["compliance_score"],
        ocr_engine=ocr_engine,
        ai_used=ai_used,
        ai_model=ai_model,
        ai_report=report or None,
        ai_extracted_json=json.dumps(ai_payload) if ai_payload else None,
    )
    db.add(scan)
    db.flush()

    for v in compliance_result["violations"]:
        db.add(models.Violation(
            scan_id=scan.id,
            code=v["code"],
            label=v["label"],
            severity=v["severity"],
            rule_reference=v.get("rule_reference"),
            description=v.get("description"),
        ))

    sides = len(saved_paths)
    db.add(models.AuditLog(
        user_id=current_user.id,
        action="SCAN_CREATED",
        details=(
            f"Multi-side scan {scan.id} created from {sides} sides with status "
            f"{compliance_result['status']} via "
            f"{('OpenRouter (' + ai_model + ')') if ai_used else 'rule engine'}"
        ),
    ))

    db.commit()
    db.refresh(scan)
    return scan


@router.get("", response_model=list[schemas.ScanListItem])
def list_scans(
    status_filter: Optional[str] = Query(None, alias="status"),
    search: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_utils.get_current_user),
):
    q = db.query(models.Scan).options(joinedload(models.Scan.inspector))

    if status_filter and status_filter != "All":
        q = q.filter(models.Scan.status == status_filter)
    if search:
        like = f"%{search}%"
        q = q.outerjoin(models.User, models.Scan.inspector_id == models.User.id).filter(
            (models.Scan.product_name.ilike(like))
            | (models.Scan.mrp.ilike(like))
            | (models.User.name.ilike(like))
        )
    if from_date:
        q = q.filter(models.Scan.created_at >= from_date)
    if to_date:
        q = q.filter(models.Scan.created_at <= to_date)

    q = q.order_by(models.Scan.created_at.desc())
    items = q.offset((page - 1) * page_size).limit(page_size).all()
    return items


@router.get("/{scan_id}", response_model=schemas.ScanOut)
def get_scan(
    scan_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_utils.get_current_user),
):
    scan = db.query(models.Scan).options(joinedload(models.Scan.violations), joinedload(models.Scan.inspector)).filter(models.Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    return scan


@router.patch("/{scan_id}", response_model=schemas.ScanOut)
def update_scan(
    scan_id: str,
    payload: schemas.ScanUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_utils.require_roles("admin", "inspector")),
):
    """Allow an inspector to manually correct OCR-extracted fields, then re-run compliance."""
    scan = db.query(models.Scan).filter(models.Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(scan, field, value)

    fields = {
        "mrp": scan.mrp, "net_quantity": scan.net_quantity, "manufacturer": scan.manufacturer,
        "mfg_date": scan.mfg_date, "consumer_care": scan.consumer_care,
        "country_of_origin": scan.country_of_origin, "unit_sale_price": scan.unit_sale_price,
    }
    classifier_result = None
    if scan.label_classifier_result:
        classifier_result = {"label": scan.label_classifier_result, "confidence": scan.label_classifier_confidence}

    result = compliance_engine.run_compliance_check(fields, classifier_result)
    scan.status = result["status"]
    scan.compliance_score = result["compliance_score"]

    db.query(models.Violation).filter(models.Violation.scan_id == scan.id).delete()
    for v in result["violations"]:
        db.add(models.Violation(
            scan_id=scan.id, code=v["code"], label=v["label"], severity=v["severity"],
            rule_reference=v.get("rule_reference"), description=v.get("description"),
        ))

    db.commit()
    db.refresh(scan)
    return scan


@router.delete("/{scan_id}", status_code=204)
def delete_scan(
    scan_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_utils.require_roles("admin")),
):
    scan = db.query(models.Scan).filter(models.Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    db.delete(scan)
    db.commit()
    return


@router.get("/{scan_id}/report")
def download_scan_report(
    scan_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_utils.get_current_user),
):
    """Generate (or regenerate) and stream a PDF compliance report for a single scan."""
    scan = db.query(models.Scan).options(joinedload(models.Scan.violations), joinedload(models.Scan.inspector)).filter(models.Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    pdf_path = pdf_service.generate_scan_report(scan)
    return FileResponse(pdf_path, media_type="application/pdf", filename=os.path.basename(pdf_path))
