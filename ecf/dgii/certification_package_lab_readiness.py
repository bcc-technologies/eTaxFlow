"""Certification portal package draft readiness checks (Phase 037)."""

from __future__ import annotations

from typing import Any


def build_certification_package_lab_readiness_checks() -> list[dict[str, Any]]:
    def _check(name: str, status: str, detail: str, *, blocker: bool = True) -> dict:
        return {"name": name, "status": status, "detail": detail, "blocker": blocker}

    return [
        _check(
            "certification_package_draft_only",
            "DESIGN_ONLY",
            "Certification portal package exists only as DRAFT_ONLY lab output.",
        ),
        _check(
            "portal_submission_not_allowed",
            "BLOCKED",
            "Portal submission is not allowed; package must not be uploaded to DGII.",
        ),
        _check(
            "portal_submission_ready_false",
            "BLOCKED",
            "Portal submission readiness remains false.",
        ),
        _check(
            "public_base_url_not_verified",
            "MISSING",
            "Public base URL is not externally verified for portal postulation.",
        ),
        _check(
            "endpoint_external_evidence_missing",
            "MISSING",
            "External endpoint/disabled-route evidence is missing for portal package.",
        ),
        _check(
            "security_owner_review_missing",
            "MANUAL_REQUIRED",
            "Security owner review is missing for certification package draft.",
        ),
        _check(
            "tax_compliance_owner_review_missing",
            "MANUAL_REQUIRED",
            "Tax/compliance owner review is missing for certification package draft.",
        ),
        _check(
            "phase_024_gate_not_signed_off",
            "MANUAL_REQUIRED",
            "Phase 024 authorization gate is not signed off for portal package.",
        ),
        _check(
            "production_signing_architecture_not_approved",
            "BLOCKED",
            "Production signing architecture is not approved.",
        ),
        _check(
            "production_signature_verification_not_implemented",
            "NOT_IMPLEMENTED",
            "Production signature verification remains NOT_IMPLEMENTED.",
        ),
        _check(
            "certification_portal_credentials_not_confirmed",
            "MANUAL_REQUIRED",
            "Certification portal credentials custody is not confirmed.",
        ),
        _check(
            "certification_package_not_human_approved",
            "MANUAL_REQUIRED",
            "Certification package draft has not been human-approved.",
        ),
    ]
