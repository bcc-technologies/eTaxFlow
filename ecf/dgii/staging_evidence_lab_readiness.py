"""Staging evidence lab readiness checks (Phase 036)."""

from __future__ import annotations

from typing import Any


def build_staging_evidence_lab_readiness_checks() -> list[dict[str, Any]]:
    def _check(name: str, status: str, detail: str, *, blocker: bool = True) -> dict:
        return {"name": name, "status": status, "detail": detail, "blocker": blocker}

    return [
        _check(
            "staging_evidence_lab_only",
            "DESIGN_ONLY",
            "Staging evidence exists only as NON_PRODUCTION_LAB_ONLY offline/manual collector.",
        ),
        _check(
            "dns_tls_evidence_not_uploaded",
            "MISSING",
            "DNS/TLS staging evidence has not been uploaded/reviewed in the evidence lab.",
        ),
        _check(
            "external_disabled_endpoint_evidence_not_uploaded",
            "MISSING",
            "External disabled-endpoint verification evidence is not uploaded.",
        ),
        _check(
            "external_post_disabled_evidence_not_uploaded",
            "MISSING",
            "External disabled POST (503 / no parse / no DB write) evidence is not uploaded.",
        ),
        _check(
            "staging_environment_evidence_not_reviewed",
            "MANUAL_REQUIRED",
            "Staging environment variable review evidence is not complete.",
        ),
        _check(
            "staging_db_separation_not_verified",
            "MANUAL_REQUIRED",
            "Staging database separation evidence is not verified.",
        ),
        _check(
            "secrets_policy_not_reviewed",
            "MANUAL_REQUIRED",
            "Staging secrets policy evidence is not reviewed.",
        ),
        _check(
            "public_base_url_not_verified",
            "MISSING",
            "Public base URL staging evidence is not verified.",
        ),
        _check(
            "logging_redaction_evidence_not_reviewed",
            "MANUAL_REQUIRED",
            "Staging logging redaction evidence is not reviewed.",
        ),
        _check(
            "security_owner_staging_review_not_completed",
            "MANUAL_REQUIRED",
            "Security owner staging review is not completed.",
        ),
        _check(
            "tax_compliance_staging_review_not_completed",
            "MANUAL_REQUIRED",
            "Tax/compliance owner staging review is not completed.",
        ),
        _check(
            "phase_024_authorization_gate_not_signed_off_for_staging",
            "MANUAL_REQUIRED",
            "Phase 024 authorization gate is not signed off for staging.",
        ),
    ]
