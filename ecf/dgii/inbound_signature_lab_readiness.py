"""Inbound signature lab readiness checks for dgii_readiness_report (Phase 030)."""

from __future__ import annotations

from typing import Any


def build_inbound_signature_lab_readiness_checks() -> list[dict[str, Any]]:
    def _check(name: str, status: str, detail: str, *, blocker: bool = True) -> dict:
        return {"name": name, "status": status, "detail": detail, "blocker": blocker}

    return [
        _check(
            "local_inbound_signature_lab_only",
            "DESIGN_ONLY",
            "XMLDSig inspection exists only as a non-production inbound signature lab.",
        ),
        _check(
            "signature_presence_not_signature_validity",
            "NOT_CLAIMED",
            "Signature element presence is not XMLDSig validity or DGII acceptance.",
        ),
        _check(
            "production_signature_verification_not_implemented",
            "NOT_IMPLEMENTED",
            "Cryptographic XMLDSig verification is not implemented; placeholders are PLACEHOLDER_ONLY.",
        ),
        _check(
            "certificate_trust_chain_validation_not_implemented",
            "NOT_IMPLEMENTED",
            "No production trust-chain validation; no real certificates used.",
        ),
        _check(
            "revocation_check_not_implemented",
            "NOT_IMPLEMENTED",
            "CRL/OCSP/revocation checks are not implemented and must not use the network.",
        ),
        _check(
            "official_certificate_policy_not_approved",
            "MANUAL_REQUIRED",
            "Official certificate policy and production signer backend are not approved.",
        ),
        _check(
            "inbound_signature_results_not_certification_evidence",
            "DESIGN_ONLY",
            "Signature lab output is not certification evidence; compliance remains NOT_DGII_COMPLIANT.",
        ),
    ]
