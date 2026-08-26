"""Inbound security policy lab readiness checks (Phase 034)."""

from __future__ import annotations

from typing import Any


def build_inbound_security_policy_lab_readiness_checks() -> list[dict[str, Any]]:
    def _check(name: str, status: str, detail: str, *, blocker: bool = True) -> dict:
        return {"name": name, "status": status, "detail": detail, "blocker": blocker}

    return [
        _check(
            "inbound_security_policy_lab_only",
            "DESIGN_ONLY",
            "Inbound security controls exist only as NON_PRODUCTION_LAB_ONLY policy review.",
        ),
        _check(
            "public_endpoint_security_controls_not_enforced",
            "NOT_IMPLEMENTED",
            "Public /fe/... routes remain disabled; body/content-type/rate controls are not enforced.",
        ),
        _check(
            "body_size_limit_not_enforced",
            "NOT_IMPLEMENTED",
            "ETAXFLOW_DGII_INBOUND_MAX_BODY_BYTES is a placeholder; not enforced on public routes.",
        ),
        _check(
            "content_type_allowlist_not_enforced",
            "NOT_IMPLEMENTED",
            "ETAXFLOW_DGII_INBOUND_ALLOWED_CONTENT_TYPES is a placeholder; not enforced on public routes.",
        ),
        _check(
            "rate_limiting_not_implemented",
            "NOT_IMPLEMENTED",
            "Inbound rate limiting / IP throttling is not implemented.",
        ),
        _check(
            "logging_redaction_policy_not_approved",
            "MANUAL_REQUIRED",
            "Operational logging redaction policy for inbound XML is not approved.",
        ),
        _check(
            "certificate_trust_chain_not_implemented",
            "NOT_IMPLEMENTED",
            "Production certificate trust-chain validation is not implemented.",
        ),
        _check(
            "revocation_check_not_implemented",
            "NOT_IMPLEMENTED",
            "CRL/OCSP revocation checking is not implemented.",
        ),
        _check(
            "security_owner_review_not_completed",
            "MANUAL_REQUIRED",
            "Security owner has not signed off inbound receiver security controls.",
        ),
        _check(
            "incident_response_policy_not_approved",
            "MANUAL_REQUIRED",
            "Incident response policy for public inbound receiver is not approved.",
        ),
        _check(
            "environment_separation_not_verified",
            "MANUAL_REQUIRED",
            "Staging/production environment separation for inbound receiver is not verified.",
        ),
        _check(
            "dns_tls_not_verified_for_public_receiver",
            "MANUAL_REQUIRED",
            "Public receiver DNS/TLS verification remains incomplete.",
        ),
        _check(
            "phase_024_human_gate_not_signed_off",
            "MANUAL_REQUIRED",
            "Phase 024 DGII authorization gate is not human-signed.",
        ),
    ]
