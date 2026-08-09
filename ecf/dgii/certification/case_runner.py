"""Run imported certification cases locally without submission."""

from __future__ import annotations

from typing import Any

from ecf.dgii.xsd.tipo31_signed_sandbox_validation import validate_tipo31_signed_sandbox
from ecf.dgii.xsd.tipo31_unsigned_validation import validate_tipo31_unsigned_draft
from ecf.services.signing_placeholder import prepare_signing_placeholder

from .test_set_importer import import_case_rows


def run_certification_harness(
    payload: dict[str, Any],
    *,
    mode: str = "unsigned",
    no_submit: bool = False,
) -> dict[str, Any]:
    """Import and locally evaluate cases; submission is intentionally impossible."""
    if not no_submit:
        raise ValueError("Certification harness requires explicit no_submit=True.")
    if mode not in {"unsigned", "sandbox-signed"}:
        raise ValueError("mode must be unsigned or sandbox-signed.")

    imported = import_case_rows(payload)
    case_reports: list[dict[str, Any]] = []
    for item in imported:
        invoice = item.invoice
        prepare_signing_placeholder(
            invoice,
            actor=invoice.created_by,
            note="Certification harness local placeholder; no real signature",
        )
        if mode == "sandbox-signed":
            validation = validate_tipo31_signed_sandbox(
                invoice,
                allow_demo_encf=True,
                test_only=True,
            )
            local_passed = validation.signed_sandbox_valid
            expected_limitation = False
            validation_payload = validation.to_dict()
        else:
            validation = validate_tipo31_unsigned_draft(
                invoice,
                allow_demo_encf=True,
            )
            local_passed = False
            expected_limitation = validation.expected_invalid_unsigned_draft
            validation_payload = validation.to_dict()
        case_reports.append(
            {
                "case_id": item.case_id,
                "source_kind": item.source_kind,
                "invoice_id": invoice.pk,
                "invoice_internal_code": invoice.internal_code,
                "mode": mode,
                "local_validation_passed": local_passed,
                "expected_unsigned_limitation": expected_limitation,
                "validation": validation_payload,
            }
        )

    return {
        "harness_status": (
            "PASS" if mode == "sandbox-signed" and all(c["local_validation_passed"] for c in case_reports)
            else "EXPECTED_UNSIGNED_LIMITATION" if mode == "unsigned"
            else "FAIL"
        ),
        "fixture_kind": payload["fixture_kind"],
        "official_fixture": bool(payload.get("official")),
        "mode": mode,
        "no_submit": True,
        "submitted": False,
        "dgii_call_made": False,
        "track_ids": [],
        "cases": case_reports,
        "compliance_status": "NOT_DGII_COMPLIANT",
        "not_certification_evidence": True,
        "notes": [
            "Local harness only; no DGII submission occurred.",
            "Synthetic/sanitized rows are not official certification evidence.",
        ],
    }
