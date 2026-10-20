"""Final go/no-go review readiness checks (Phase 038)."""

from __future__ import annotations

from typing import Any


def build_final_go_no_go_lab_readiness_checks() -> list[dict[str, Any]]:
    def _check(name: str, status: str, detail: str, *, blocker: bool = True) -> dict:
        return {"name": name, "status": status, "detail": detail, "blocker": blocker}

    return [
        _check(
            "final_go_no_go_lab_only",
            "DESIGN_ONLY",
            "Final go/no-go exists only as FINAL_REVIEW_LAB_ONLY non-production review.",
        ),
        _check(
            "final_decision_blocked",
            "BLOCKED",
            "Final decision remains FINAL_DECISION_BLOCKED.",
        ),
        _check(
            "final_human_review_not_completed",
            "MANUAL_REQUIRED",
            "Final human review of pre-certification gates is not completed.",
        ),
        _check(
            "final_security_owner_approval_missing",
            "MANUAL_REQUIRED",
            "Final security owner approval is missing.",
        ),
        _check(
            "final_tax_compliance_approval_missing",
            "MANUAL_REQUIRED",
            "Final tax/compliance owner approval is missing.",
        ),
        _check(
            "final_dgii_authorization_missing",
            "MANUAL_REQUIRED",
            "Final DGII authorization gate sign-off is missing.",
        ),
        _check(
            "final_public_endpoint_activation_forbidden",
            "BLOCKED",
            "Public endpoint activation remains forbidden.",
        ),
        _check(
            "final_portal_submission_forbidden",
            "BLOCKED",
            "Portal submission remains forbidden.",
        ),
        _check(
            "final_dgii_submission_forbidden",
            "BLOCKED",
            "DGII submission remains forbidden.",
        ),
        _check(
            "final_production_signing_not_approved",
            "BLOCKED",
            "Production signing architecture is not approved.",
        ),
        _check(
            "final_production_signature_verification_not_ready",
            "NOT_IMPLEMENTED",
            "Production signature verification is not ready.",
        ),
        _check(
            "final_staging_evidence_not_approved",
            "MANUAL_REQUIRED",
            "Staging evidence package is not approved.",
        ),
        _check(
            "final_certification_package_blocked",
            "BLOCKED",
            "Certification package remains PACKAGE_BLOCKED.",
        ),
    ]
