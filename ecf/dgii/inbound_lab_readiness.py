"""Inbound XML lab readiness checks for dgii_readiness_report (Phase 028)."""

from __future__ import annotations

from typing import Any


def build_inbound_lab_readiness_checks() -> list[dict[str, Any]]:
    def _check(name: str, status: str, detail: str, *, blocker: bool = True) -> dict:
        return {"name": name, "status": status, "detail": detail, "blocker": blocker}

    return [
        _check(
            "inbound_lab_synthetic_only",
            "DESIGN_ONLY",
            "Inbound XML lab uses NON_OFFICIAL_SYNTHETIC_SAMPLE fixtures only; not DGII test-set.",
        ),
        _check(
            "inbound_schema_validation_not_claimed",
            "NOT_CLAIMED",
            "Lab does not claim XSD/schema compliance; local schema validation is a future phase.",
        ),
        _check(
            "inbound_signature_verification_not_implemented",
            "NOT_IMPLEMENTED",
            "Lab detects signature presence only; production verification not implemented.",
        ),
        _check(
            "inbound_persistence_not_implemented",
            "NOT_IMPLEMENTED",
            "Inbound lab does not persist XML or results to database.",
        ),
        _check(
            "inbound_public_processing_disabled",
            "DISABLED",
            "Public /fe/... routes remain 503 DISABLED; lab is internal command only.",
        ),
        _check(
            "inbound_official_test_set_not_loaded",
            "NOT_LOADED",
            "Official DGII certification test-set fixtures are not loaded in repo.",
        ),
        _check(
            "inbound_lab_not_certification_evidence",
            "DESIGN_ONLY",
            "Lab output is not certification evidence; compliance remains NOT_DGII_COMPLIANT.",
        ),
    ]
