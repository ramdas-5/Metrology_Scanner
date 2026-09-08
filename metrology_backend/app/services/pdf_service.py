"""
Generates a per-scan compliance report PDF using reportlab.
"""

import os
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
)

from app.config import settings


def generate_scan_report(scan) -> str:
    """
    scan: models.Scan ORM instance (with .violations loaded)
    Returns the path to the generated PDF file.
    """
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("TitleStyle", parent=styles["Title"], textColor=colors.HexColor("#07539a"))
    heading_style = ParagraphStyle("Heading", parent=styles["Heading2"], textColor=colors.HexColor("#07539a"))

    filename = f"report_{scan.id}.pdf"
    out_path = os.path.join(settings.REPORTS_DIR, filename)

    doc = SimpleDocTemplate(out_path, pagesize=A4, topMargin=20 * mm, bottomMargin=20 * mm)
    story = []

    story.append(Paragraph("Legal Metrology Compliance Report", title_style))
    story.append(Paragraph("Department of Consumer Affairs — Packaged Commodities Rules, 2011", styles["Normal"]))
    story.append(Spacer(1, 10))

    meta = [
        ["Scan ID", scan.id],
        ["Product", scan.product_name or "Unidentified Product"],
        ["Inspected By", (scan.inspector.name if scan.inspector else None) or "-"],
        ["Inspector Email", (scan.inspector.email if scan.inspector else None) or "-"],
        ["Date Generated", datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")],
        ["Inspection Timestamp", scan.created_at.strftime("%Y-%m-%d %H:%M UTC")],
        ["Status", scan.status.value if hasattr(scan.status, "value") else scan.status],
        ["Compliance Score", f"{scan.compliance_score}%"],
        ["OCR Engine", (scan.ocr_engine or "-").capitalize()],
        ["Result Source", f"AI ({scan.ai_model})" if scan.ai_used else "Rule engine / regex"],
    ]
    t = Table(meta, colWidths=[150, 320])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#eef3fa")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#c9d6e3")),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(t)
    story.append(Spacer(1, 16))

    if scan.image_path and os.path.exists(scan.image_path):
        try:
            story.append(Paragraph("Captured Product Image", heading_style))
            story.append(Spacer(1, 6))
            story.append(RLImage(scan.image_path, width=160, height=160))
            story.append(Spacer(1, 16))
        except Exception:
            pass

    story.append(Paragraph("Extracted Mandatory Declarations", heading_style))
    story.append(Spacer(1, 6))
    decl_rows = [["Field", "Detected Value"]]
    decl_rows += [
        ["MRP (₹)", scan.mrp or "Not detected"],
        ["Net Quantity", scan.net_quantity or "Not detected"],
        ["Manufacturer / Packer / Importer", scan.manufacturer or "Not detected"],
        ["Mfg. / Pkg. Date", scan.mfg_date or "Not detected"],
        ["Consumer Care Details", scan.consumer_care or "Not detected"],
        ["Country of Origin", scan.country_of_origin or "Not detected"],
        ["Unit Sale Price", scan.unit_sale_price or "Not applicable / not detected"],
    ]
    dt = Table(decl_rows, colWidths=[200, 270])
    dt.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#07539a")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#c9d6e3")),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
    ]))
    story.append(dt)
    story.append(Spacer(1, 16))

    story.append(Paragraph("Violations / Non-Compliances Identified", heading_style))
    story.append(Spacer(1, 6))
    if scan.violations:
        v_rows = [["Code", "Description", "Severity", "Rule Ref."]]
        for v in scan.violations:
            v_rows.append([v.code, v.label, v.severity.upper(), v.rule_reference or "-"])
        vt = Table(v_rows, colWidths=[90, 220, 60, 100])
        vt.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#b3261e")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e0c2c0")),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
        ]))
        story.append(vt)
    else:
        story.append(Paragraph("No violations detected. Product appears compliant.", styles["Normal"]))

    if scan.ai_report:
        story.append(Spacer(1, 12))
        story.append(Paragraph("Analysis Report", heading_style))
        story.append(Spacer(1, 6))
        story.append(Paragraph(scan.ai_report, styles["Normal"]))

    story.append(Spacer(1, 20))
    story.append(Paragraph(
        "This report was generated automatically by an AI-assisted compliance scanning system and "
        "is intended to support, not replace, manual verification by an authorized Legal Metrology officer.",
        styles["Italic"],
    ))

    doc.build(story)
    return out_path


def generate_summary_report(
    total: int,
    passed: int,
    failed: int,
    pending: int,
    compliance_rate: float,
    top_violations,
    inspectors,
) -> str:
    """All-time analytics PDF for the Admin 'Generate System Report' action."""
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("TitleStyle", parent=styles["Title"], textColor=colors.HexColor("#07539a"))
    heading_style = ParagraphStyle("Heading", parent=styles["Heading2"], textColor=colors.HexColor("#07539a"))

    out_path = os.path.join(
        settings.REPORTS_DIR,
        f"summary_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf",
    )

    doc = SimpleDocTemplate(out_path, pagesize=A4, topMargin=20 * mm, bottomMargin=20 * mm)
    story = []

    story.append(Paragraph("System Compliance Summary Report", title_style))
    story.append(Paragraph(
        f"All-time analytics - generated {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
        styles["Normal"],
    ))
    story.append(Spacer(1, 12))

    overview = [
        ["Total Inspections", str(total)],
        ["Passed", str(passed)],
        ["Failed", str(failed)],
        ["Pending Review", str(pending)],
        ["Compliance Rate", f"{compliance_rate}%"],
    ]
    t = Table(overview, colWidths=[220, 200])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#eef3fa")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#c9d6e3")),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
    ]))
    story.append(t)
    story.append(Spacer(1, 16))

    story.append(Paragraph("Top Violations (All Time)", heading_style))
    story.append(Spacer(1, 6))
    if top_violations:
        rows = [["Violation", "Count"]]
        for label, count in top_violations:
            rows.append([str(label), str(count)])
        vt = Table(rows, colWidths=[340, 120])
        vt.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#b3261e")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e0c2c0")),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
        ]))
        story.append(vt)
    else:
        story.append(Paragraph("No violations recorded.", styles["Normal"]))

    story.append(Spacer(1, 16))
    story.append(Paragraph("Inspector Activity", heading_style))
    story.append(Spacer(1, 6))
    rows = [["Inspector", "Email", "Scans"]]
    for name, email, count in inspectors:
        rows.append([name or "-", email or "-", str(count)])
    it = Table(rows, colWidths=[170, 230, 60])
    it.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#07539a")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#c9d6e3")),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
    ]))
    story.append(it)

    doc.build(story)
    return out_path
