"""Inbound reporting lab readiness checks (Phase 035)."""

from __future__ import annotations

from typing import Any


def build_inbound_reporting_lab_readiness_checks() -> list[dict[str, Any]]:
    def _check(name: str, status: str, detail: str, *, blocker: bool = True) -> dict:
        return {"name": name, "status": status, "detail": detail, "blocker": blocker}

    return [
        _check(
            "inbound_reporting_lab_only",
            "DESIGN_ONLY",
            "Inbound reporting exists only as NON_PRODUCTION_LAB_ONLY metadata exports.",
        ),
        _check(
            "reports_not_certification_evidence",
            "NOT_CLAIMED",
            "Lab report bundles are not DGII certification evidence.",
        ),
        _check(
            "reports_metadata_only",
            "DESIGN_ONLY",
            "Exports are metadata-only; raw XML is not included by default.",
        ),
        _check(
            "production_dashboard_not_implemented",
            "NOT_IMPLEMENTED",
            "Production inbound dashboard is not implemented.",
        ),
        _check(
            "public_endpoint_reporting_disabled",
            "DISABLED",
            "Public /fe/... routes remain 503 DISABLED and must not generate reports.",
        ),
        _check(
            "report_review_not_human_approved",
            "MANUAL_REQUIRED",
            "Human security/compliance review of inbound lab report packages is not approved.",
        ),
        _check(
            "raw_xml_reporting_policy_not_approved",
            "MANUAL_REQUIRED",
            "Policy for any future raw XML reporting/export remains unapproved.",
        ),
    ]
