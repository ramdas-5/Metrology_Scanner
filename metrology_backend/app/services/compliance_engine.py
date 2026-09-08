"""
Rule-based compliance engine.

Implements a simplified, codified version of the mandatory-declaration
checks under the Legal Metrology (Packaged Commodities) Rules, 2011
(Chapter II, Rule 6 onward). Each rule below maps to a real requirement;
`rule_reference` values are indicative and should be reviewed against the
current gazette text before use in a production enforcement tool.

Given a dict of OCR-extracted fields (and optional label-classifier
result), `run_compliance_check()` returns a list of violations and an
overall compliance score / status.
"""

import re
from typing import Optional

RULES = [
    {
        "code": "MISSING_MANUFACTURER",
        "field": "manufacturer",
        "label": "Missing Manufacturer / Packer / Importer Details",
        "severity": "major",
        "rule_reference": "Rule 6(1)(a)",
        "description": "Name and complete address of the manufacturer, packer, or importer must be declared on every package.",
    },
    {
        "code": "MISSING_NET_QUANTITY",
        "field": "net_quantity",
        "label": "Missing / Invalid Net Quantity Declaration",
        "severity": "major",
        "rule_reference": "Rule 6(1)(b) / Rule 8",
        "description": "The net quantity must be declared in standard units (e.g. g, kg, ml, l) using the prescribed metric system.",
    },
    {
        "code": "MISSING_MRP",
        "field": "mrp",
        "label": "Missing MRP Declaration",
        "severity": "major",
        "rule_reference": "Rule 6(1)(e)",
        "description": "The Maximum Retail Price inclusive of all taxes must be declared as 'MRP Rs. ... (incl. of all taxes)'.",
    },
    {
        "code": "MISSING_MFG_DATE",
        "field": "mfg_date",
        "label": "Missing Month & Year of Manufacture/Packing/Import",
        "severity": "major",
        "rule_reference": "Rule 6(1)(f)",
        "description": "Month and year in which the commodity was manufactured, packed, or imported must be declared.",
    },
    {
        "code": "MISSING_CONSUMER_CARE",
        "field": "consumer_care",
        "label": "Missing Consumer Care / Contact Details",
        "severity": "minor",
        "rule_reference": "Rule 6(1)(d)",
        "description": "Name, address, telephone number and/or email of the person/office who can be contacted for consumer complaints must be declared.",
    },
]


def _is_blank(value: Optional[str]) -> bool:
    return value is None or str(value).strip() == ""


def _check_mrp_format(mrp: Optional[str]) -> Optional[dict]:
    """MRP should be a plausible positive number."""
    if _is_blank(mrp):
        return None
    cleaned = re.sub(r"[^\d.]", "", mrp)
    try:
        value = float(cleaned)
    except ValueError:
        return {
            "code": "INVALID_MRP_FORMAT",
            "label": "MRP Declaration Not in Valid Format",
            "severity": "minor",
            "rule_reference": "Rule 6(1)(e)",
            "description": f"Detected MRP value '{mrp}' could not be parsed as a valid currency amount.",
        }
    if value <= 0:
        return {
            "code": "INVALID_MRP_VALUE",
            "label": "MRP Declaration Has Non-Positive Value",
            "severity": "major",
            "rule_reference": "Rule 6(1)(e)",
            "description": f"Detected MRP value '{mrp}' is not a valid positive price.",
        }
    return None


def _check_net_quantity_format(net_quantity: Optional[str]) -> Optional[dict]:
    """Net quantity should use a standard metric unit."""
    if _is_blank(net_quantity):
        return None
    valid_units = r"(g|gm|gram|grams|kg|ml|l|litre|litres|n|pcs|pieces)"
    if not re.search(valid_units, net_quantity, re.IGNORECASE):
        return {
            "code": "NON_STANDARD_UNIT",
            "label": "Net Quantity Not in Standard Metric Unit",
            "severity": "minor",
            "rule_reference": "Rule 8",
            "description": f"Detected net quantity '{net_quantity}' does not use a standard unit (g/kg/ml/l/N/pieces).",
        }
    return None


def _check_font_readability(label_classifier_result: Optional[dict]) -> Optional[dict]:
    """
    Use the trained label classifier as a proxy for readability / print
    quality / declaration-format compliance. If the model flags the
    label as non-compliant, surface it as a violation.
    """
    if not label_classifier_result:
        return None
    predicted_label = str(label_classifier_result.get("label", "")).lower()
    confidence = label_classifier_result.get("confidence", 0)
    if "non-compliant" in predicted_label or "noncompliant" in predicted_label or "invalid" in predicted_label:
        return {
            "code": "AI_FLAGGED_LABEL",
            "label": "AI Vision Model Flagged Label as Non-Compliant",
            "severity": "major",
            "rule_reference": "Rule 5 (General provisions regarding declarations)",
            "description": (
                f"The trained label-image classifier predicted '{label_classifier_result.get('label')}' "
                f"with {confidence}% confidence, indicating probable font size, placement, or print-quality issues."
            ),
        }
    return None


def run_compliance_check(fields: dict, label_classifier_result: Optional[dict] = None) -> dict:
    """
    fields: dict with keys mrp, net_quantity, manufacturer, mfg_date,
            consumer_care, country_of_origin, unit_sale_price
    label_classifier_result: optional dict from classifier_service.classify_image()

    Returns {"violations": [...], "compliance_score": float, "status": "Passed"|"Failed"|"Pending Review"}
    """
    violations = []

    # 1. Mandatory-field presence checks
    for rule in RULES:
        value = fields.get(rule["field"])
        if _is_blank(value):
            violations.append({
                "code": rule["code"],
                "label": rule["label"],
                "severity": rule["severity"],
                "rule_reference": rule["rule_reference"],
                "description": rule["description"],
            })

    # 2. Format / value sanity checks
    for check in (
        _check_mrp_format(fields.get("mrp")),
        _check_net_quantity_format(fields.get("net_quantity")),
        _check_font_readability(label_classifier_result),
    ):
        if check:
            violations.append(check)

    # 3. Score: 100 minus weighted penalty per violation
    penalty = sum(15 if v["severity"] == "major" else 6 for v in violations)
    compliance_score = max(0, 100 - penalty)

    major_violations = [v for v in violations if v["severity"] == "major"]
    if not violations:
        status = "Passed"
    elif major_violations:
        status = "Failed"
    else:
        status = "Pending Review"

    return {
        "violations": violations,
        "compliance_score": compliance_score,
        "status": status,
    }


def summarize_result(result: dict, fields: dict) -> str:
    """
    Human-readable one/two-line summary used as the Scan.ai_report when the
    result came from the deterministic rule engine (no OpenRouter key set).
    """
    status = result.get("status", "Pending Review")
    score = result.get("compliance_score", 0)
    violations = result.get("violations", [])
    missing = []
    for rule in RULES:
        if _is_blank(fields.get(rule["field"])):
            missing.append(rule["code"])

    lines = [f"Rule-engine result: {status} with a compliance score of {score}%."]
    if missing:
        lines.append("Not detected on the label: " + ", ".join(missing) + ".")
    if violations:
        lines.append(
            "Violations: "
            + "; ".join(
                f"{v['label']} ({v['rule_reference'] or 'no rule ref'})" for v in violations
            )
        )
    else:
        lines.append("No violations found - the label appears compliant.")
    return " ".join(lines)

