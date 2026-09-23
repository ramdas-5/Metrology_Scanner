import json
import logging
import os
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, Query
from fastapi.responses import FileResponse

from app import crud, models, schemas
from app import auth as auth_utils
from app.config import settings
from app.models import gen_id, utcnow
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


def _ocr_all_parallel(paths: list[str]) -> list[dict]:
    """Run the OCR engine over several images in parallel.

    Multi-side scans used to OCR side-by-side sequentially, so 6 sides took
    6x the single-side time. The native OCR code releases the GIL, so a
    thread pool gives a near-linear speedup while producing IDENTICAL text
    per side (same engine, same prep - no accuracy trade-off).
    """
    if len(paths) <= 1:
        return [ocr_service.run_ocr_engine(p) for p in paths]
    workers = min(len(paths), 4)
    with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="ocr") as pool:
        return list(pool.map(ocr_service.run_ocr_engine, paths))


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


def _embedded_violations(violations: list) -> list[dict]:
    """Violations live inside the scan document; each one gets its own id so
    the API keeps returning stable identifiers to the UI."""
    return [
        {
            "id": gen_id(),
            "code": v["code"],
            "label": v["label"],
            "severity": v.get("severity", "major"),
            "rule_reference": v.get("rule_reference"),
            "description": v.get("description"),
        }
        for v in violations
    ]


def _resolve_fields_and_verdict(
    raw_text: str,
    product_name: Optional[str],
    classifier_result: Optional[dict],
) -> dict:
    """
    Step 3+4 of the pipeline: AI extraction when OpenRouter is configured,
    otherwise the deterministic regex parser + Legal Metrology rule engine.

    Returns the declaration fields, the compliance verdict, the report text,
    the resolved product name and the AI bookkeeping values.
    """
    ai_payload = None
    ai_used = False
    ai_model = None

    if ai_service.is_ai_configured() and (raw_text or "").strip():
        try:
            ai_payload = ai_service.extract_label_data(raw_text, product_name=product_name)
            ai_used = True
            ai_model = ai_payload.get("model")
        except ai_service.AIExtractionError as exc:
            logger.warning("AI extraction failed; falling back to rule engine: %s", exc)
            ai_payload = None

    if ai_payload:
        # The AI computed the declarations AND the violations; the score/status
        # are ALWAYS recomputed deterministically from those violations so the
        # number displayed can never disagree with the list shown next to it.
        fields = {key: ai_payload.get(key) for key in DECLARATION_FIELDS}
        fields["ocr_raw_text"] = raw_text

        compliance_result = {
            "status": ai_payload["status"],
            "compliance_score": ai_payload["compliance_score"],
            "violations": ai_payload["violations"],
        }
        compliance_result.update(compliance_engine.score_from_violations(compliance_result["violations"]))
        overall_confidence = ai_payload.get("overall_confidence")
        if overall_confidence is None:
            found = sum(1 for key in DECLARATION_FIELDS if fields.get(key))
            overall_confidence = round(found / len(DECLARATION_FIELDS) * 100, 1)
        report = ai_payload.get("summary") or ""
        resolved_product = (product_name or "").strip() or ai_payload.get("product_name")
    else:
        # Fallback: regex parser + deterministic rule engine.
        fields = ocr_service.parse_declarations(raw_text)
        compliance_result = compliance_engine.run_compliance_check(fields, classifier_result)
        overall_confidence = fields["overall_confidence"]
        report = compliance_engine.summarize_result(compliance_result, fields)
        resolved_product = product_name

    return {
        "fields": fields,
        "compliance_result": compliance_result,
        "overall_confidence": overall_confidence,
        "report": report,
        "resolved_product": resolved_product,
        "ai_payload": ai_payload,
        "ai_used": ai_used,
        "ai_model": ai_model,
    }


def _cache_lookup(raw_text: str, current_user) -> Optional[schemas.ScanOut]:
    """Return the previously saved scan when the OCR text is >= threshold
    similar, so no AI call is made and no duplicate document is written."""
    if not (raw_text or "").strip():
        return None
    match_id, score, _ = dedupe_service.find_similar_scan(raw_text)
    if not match_id:
        return None
    cached_scan = crud.get_scan(match_id)
    if not cached_scan:
        return None
    crud.add_audit_log(
        current_user.id,
        "SCAN_CACHE_HIT",
        f"OCR text {score}% similar to saved scan {cached_scan.id}; "
        "returned saved result and skipped the AI call.",
    )
    out = schemas.ScanOut.model_validate(cached_scan)
    out.cached = True
    out.similarity = score
    return out


@router.post("", response_model=schemas.ScanOut, status_code=201)
def create_scan(
    image: UploadFile = File(...),
    product_name: Optional[str] = Form(None),
    current_user: models.Doc = Depends(auth_utils.get_current_user),
):
    """
    Main scanning endpoint used by the "New Scan" screen. Accepts *any*
    image and runs the full pipeline:

      1. OCR - extract as much text as possible (PaddleOCR if installed,
         otherwise Tesseract; engine chosen via OCR_ENGINE in .env).
      2. Dedupe / cache - if the extracted text is >= SIMILARITY_THRESHOLD%
         (default 80) similar to a previously saved scan, return that saved
         result straight from the DB - no AI call, no duplicate document.
      3. AI extraction - when OPENROUTER_API_KEY is set, one OpenRouter call
         converts the raw text into the fixed JSON (declarations + compliance
         score/status/violations + narrative report) which is stored as-is.
      4. Fallback - when no API key is set (or the AI call fails), the
         deterministic regex parser + Legal Metrology rule engine runs
         instead, so the app keeps working offline.
    """
    scan_started = time.perf_counter()
    image_path = _save_upload(image)

    # ---- 1. OCR: any image -> as much text as possible ----
    try:
        ocr = ocr_service.run_ocr_engine(image_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR processing failed: {e}")
    raw_text = ocr["text"] or ""
    ocr_engine = ocr["engine"]

    # ---- 2. Dedupe / cache: return the saved value when >= 80% similar ----
    cached_out = _cache_lookup(raw_text, current_user)
    if cached_out is not None:
        return cached_out

    classifier_result = _run_classifier(image_path)

    # ---- 3. AI extraction (OpenRouter) / 4. rule-engine fallback ----
    resolved = _resolve_fields_and_verdict(raw_text, product_name, classifier_result)
    fields = resolved["fields"]
    compliance_result = resolved["compliance_result"]
    ai_payload = resolved["ai_payload"]
    ai_used = resolved["ai_used"]
    ai_model = resolved["ai_model"]

    scan_id = gen_id()
    scan = crud.insert_scan({
        "_id": scan_id,
        "id": scan_id,
        "inspector_id": current_user.id,
        "inspector_name": current_user.name,
        "inspector_email": current_user.email,
        "product_name": resolved["resolved_product"],
        "image_path": image_path,
        "mrp": fields.get("mrp"),
        "net_quantity": fields.get("net_quantity"),
        "manufacturer": fields.get("manufacturer"),
        "mfg_date": fields.get("mfg_date"),
        "consumer_care": fields.get("consumer_care"),
        "country_of_origin": fields.get("country_of_origin"),
        "unit_sale_price": fields.get("unit_sale_price"),
        "ocr_raw_text": raw_text,
        "overall_confidence": resolved["overall_confidence"],
        "label_classifier_result": classifier_result["label"] if classifier_result else None,
        "label_classifier_confidence": classifier_result["confidence"] if classifier_result else 0.0,
        "status": compliance_result["status"],
        "compliance_score": compliance_result["compliance_score"],
        "ocr_engine": ocr_engine,
        "ai_used": ai_used,
        "ai_model": ai_model,
        "ai_report": resolved["report"] or None,
        "ai_extracted_json": json.dumps(ai_payload) if ai_payload else None,
        "violations": _embedded_violations(compliance_result["violations"]),
    })

    processing_ms = int((time.perf_counter() - scan_started) * 1000)
    source = f"OpenRouter ({ai_model})" if ai_used else "rule engine"
    crud.add_audit_log(
        current_user.id,
        "SCAN_CREATED",
        f"Scan {scan.id} created with status {compliance_result['status']} via {source} "
        f"in {processing_ms / 1000:.1f}s",
    )

    out = schemas.ScanOut.model_validate(scan)
    out.processing_ms = processing_ms
    return out


@router.post("/multi", response_model=schemas.ScanOut, status_code=201)
def create_multi_side_scan(
    images: list[UploadFile] = File(..., description="One or more sides of the same package"),
    product_name: Optional[str] = Form(None),
    current_user: models.Doc = Depends(auth_utils.get_current_user),
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

    scan_started = time.perf_counter()
    saved_paths: list[str] = []
    for image in images:
        saved_paths.append(_save_upload(image))

    # OCR all sides in parallel - the biggest multi-side latency win.
    try:
        ocr_results = _ocr_all_parallel(saved_paths)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR processing failed: {e}")
    texts = [r["text"] or "" for r in ocr_results]
    engines = {r["engine"] for r in ocr_results}

    raw_text = _merge_multi_side_text(texts)
    ocr_engine = "+".join(sorted(engines))

    # Cache lookup is skipped for multi-side scans: the combined text is unique
    # to this capture session, so a similarity match would be misleading.
    classifier_result = _run_classifier(saved_paths[0])  # first side only - keeps it fast

    resolved = _resolve_fields_and_verdict(raw_text, product_name, classifier_result)
    fields = resolved["fields"]
    compliance_result = resolved["compliance_result"]
    ai_payload = resolved["ai_payload"]
    ai_used = resolved["ai_used"]
    ai_model = resolved["ai_model"]

    scan_id = gen_id()
    scan = crud.insert_scan({
        "_id": scan_id,
        "id": scan_id,
        "inspector_id": current_user.id,
        "inspector_name": current_user.name,
        "inspector_email": current_user.email,
        "product_name": resolved["resolved_product"],
        # Keep every side's file path so the full capture set is auditable.
        "image_path": json.dumps(saved_paths) if len(saved_paths) > 1 else saved_paths[0],
        "mrp": fields.get("mrp"),
        "net_quantity": fields.get("net_quantity"),
        "manufacturer": fields.get("manufacturer"),
        "mfg_date": fields.get("mfg_date"),
        "consumer_care": fields.get("consumer_care"),
        "country_of_origin": fields.get("country_of_origin"),
        "unit_sale_price": fields.get("unit_sale_price"),
        "ocr_raw_text": raw_text,
        "overall_confidence": resolved["overall_confidence"],
        "label_classifier_result": classifier_result["label"] if classifier_result else None,
        "label_classifier_confidence": classifier_result["confidence"] if classifier_result else 0.0,
        "status": compliance_result["status"],
        "compliance_score": compliance_result["compliance_score"],
        "ocr_engine": ocr_engine,
        "ai_used": ai_used,
        "ai_model": ai_model,
        "ai_report": resolved["report"] or None,
        "ai_extracted_json": json.dumps(ai_payload) if ai_payload else None,
        "violations": _embedded_violations(compliance_result["violations"]),
    })

    processing_ms = int((time.perf_counter() - scan_started) * 1000)
    sides = len(saved_paths)
    crud.add_audit_log(
        current_user.id,
        "SCAN_CREATED",
        f"Multi-side scan {scan.id} created from {sides} sides with status "
        f"{compliance_result['status']} via "
        f"{('OpenRouter (' + ai_model + ')') if ai_used else 'rule engine'} "
        f"in {processing_ms / 1000:.1f}s",
    )

    out = schemas.ScanOut.model_validate(scan)
    out.processing_ms = processing_ms
    return out


@router.get("", response_model=schemas.PaginatedScans)
def list_scans(
    status_filter: Optional[str] = Query(None, alias="status"),
    search: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    current_user: models.Doc = Depends(auth_utils.get_current_user),
):
    items, total = crud.list_scans(
        status=status_filter,
        search=search,
        from_date=_parse_date(from_date),
        to_date=_parse_date(to_date),
        page=page,
        page_size=page_size,
    )
    return {"items": items, "total": total, "page": max(1, page), "page_size": page_size}


@router.get("/{scan_id}", response_model=schemas.ScanOut)
def get_scan(
    scan_id: str,
    current_user: models.Doc = Depends(auth_utils.get_current_user),
):
    scan = crud.get_scan(scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    return scan


@router.patch("/{scan_id}", response_model=schemas.ScanOut)
def update_scan(
    scan_id: str,
    payload: schemas.ScanUpdate,
    current_user: models.Doc = Depends(auth_utils.require_roles("admin", "inspector")),
):
    """Allow an inspector to manually correct OCR-extracted fields, then re-run compliance."""
    scan = crud.get_scan(scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    updates = {
        field: value
        for field, value in payload.model_dump(exclude_unset=True).items()
        # Never let the client write arbitrary keys into the document.
        if field in DECLARATION_FIELDS or field == "product_name"
    }
    for field, value in updates.items():
        scan[field] = value

    fields = {key: scan.get(key) for key in DECLARATION_FIELDS}
    classifier_result = None
    if scan.label_classifier_result:
        classifier_result = {
            "label": scan.label_classifier_result,
            "confidence": scan.label_classifier_confidence,
        }

    result = compliance_engine.run_compliance_check(fields, classifier_result)
    updates["status"] = result["status"]
    updates["compliance_score"] = result["compliance_score"]
    updates["violations"] = _embedded_violations(result["violations"])

    updated = crud.update_scan_fields(scan_id, updates)
    crud.add_audit_log(
        current_user.id, "SCAN_UPDATED", f"Scan {scan_id} declarations corrected manually"
    )
    return updated


@router.delete("/{scan_id}", status_code=204)
def delete_scan(
    scan_id: str,
    current_user: models.Doc = Depends(auth_utils.require_roles("admin")),
):
    if not crud.delete_scan(scan_id):
        raise HTTPException(status_code=404, detail="Scan not found")
    crud.add_audit_log(current_user.id, "SCAN_DELETED", f"Scan {scan_id} deleted")
    return


@router.get("/{scan_id}/report")
def download_scan_report(
    scan_id: str,
    current_user: models.Doc = Depends(auth_utils.get_current_user),
):
    """Generate (or regenerate) and stream a PDF compliance report for a single scan."""
    scan = crud.get_scan(scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    pdf_path = pdf_service.generate_scan_report(scan)
    return FileResponse(pdf_path, media_type="application/pdf", filename=os.path.basename(pdf_path))
