"""Inbound schema lab readiness checks for dgii_readiness_report (Phase 029)."""

from __future__ import annotations

from typing import Any


def build_inbound_schema_lab_readiness_checks() -> list[dict[str, Any]]:
    def _check(name: str, status: str, detail: str, *, blocker: bool = True) -> dict:
        return {"name": name, "status": status, "detail": detail, "blocker": blocker}

    return [
        _check(
            "local_inbound_schema_validation_lab_only",
            "DESIGN_ONLY",
            "Local XSD validation exists only as a non-production inbound schema lab.",
        ),
        _check(
            "local_xsd_validation_not_dgii_acceptance",
            "NOT_CLAIMED",
            "A local XSD pass does not equal DGII acceptance, certification, or compliance.",
        ),
        _check(
            "official_certification_fixtures_not_loaded",
            "NOT_LOADED",
            "Official DGII certification test-set fixtures are not loaded; lab uses synthetic samples.",
        ),
        _check(
            "inbound_xsd_errors_not_resolved",
            "BLOCKED",
            "Synthetic inbound fixtures are expected to report local XSD errors; not resolved for production.",
        ),
        _check(
            "inbound_schema_mapping_not_human_reviewed",
            "MANUAL_REQUIRED",
            "ECF maps to e-CF_31_v1.0.xsd only; ARECF/ACECF mapping is not human-reviewed for all tipos.",
        ),
        _check(
            "inbound_signature_validation_still_not_implemented",
            "NOT_IMPLEMENTED",
            "Placeholder Signature presence is not XMLDSig verification.",
        ),
        _check(
            "inbound_public_processing_still_disabled",
            "DISABLED",
            "Public /fe/... routes remain 503 DISABLED; schema lab is an internal command only.",
        ),
        _check(
            "inbound_persistence_still_not_implemented",
            "NOT_IMPLEMENTED",
            "Inbound schema lab does not persist XML or validation results.",
        ),
    ]
