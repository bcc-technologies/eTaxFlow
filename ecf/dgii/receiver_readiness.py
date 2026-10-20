"""Receiver readiness checks for dgii_readiness_report (Phase 027)."""

from __future__ import annotations

from typing import Any


def build_receiver_readiness_checks() -> list[dict[str, Any]]:
    def _check(name: str, status: str, detail: str, *, blocker: bool = True) -> dict:
        return {"name": name, "status": status, "detail": detail, "blocker": blocker}

    return [
        _check(
            "receiver_processing_not_implemented",
            "NOT_IMPLEMENTED",
            "Inbound receiver pipeline (intake, validation, storage) is not implemented.",
        ),
        _check(
            "inbound_xml_signature_verification_not_implemented",
            "NOT_IMPLEMENTED",
            "Inbound XMLDSig verification is not implemented; presence detection only in contract.",
        ),
        _check(
            "inbound_persistence_not_implemented",
            "NOT_IMPLEMENTED",
            "Inbound document storage and audit persistence are not implemented.",
        ),
        _check(
            "inbound_duplicate_detection_not_implemented",
            "NOT_IMPLEMENTED",
            "Duplicate detection by hash/eNCF is not implemented.",
        ),
        _check(
            "acuse_receiver_workflow_not_implemented",
            "NOT_IMPLEMENTED",
            "ARECF (Acuse de Recibo) receiver workflow is design-only.",
        ),
        _check(
            "aprobacion_comercial_receiver_workflow_not_implemented",
            "NOT_IMPLEMENTED",
            "ACECF (Aprobación Comercial) receiver workflow is design-only.",
        ),
        _check(
            "ecf_receiver_workflow_not_implemented",
            "NOT_IMPLEMENTED",
            "ECF receiver workflow is design-only.",
        ),
        _check(
            "receiver_security_controls_not_approved",
            "MANUAL_REQUIRED",
            "Receiver security controls (size cap, rate limit, logging redaction) not approved.",
        ),
    ]
