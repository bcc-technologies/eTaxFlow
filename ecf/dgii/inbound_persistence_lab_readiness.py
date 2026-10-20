"""Inbound persistence lab readiness checks (Phase 031)."""

from __future__ import annotations

from typing import Any


def build_inbound_persistence_lab_readiness_checks() -> list[dict[str, Any]]:
    def _check(name: str, status: str, detail: str, *, blocker: bool = True) -> dict:
        return {"name": name, "status": status, "detail": detail, "blocker": blocker}

    return [
        _check(
            "inbound_persistence_lab_only",
            "DESIGN_ONLY",
            "Inbound persistence exists only as NON_PRODUCTION_LAB_ONLY InboundXMLLabRecord rows.",
        ),
        _check(
            "production_inbound_persistence_not_implemented",
            "NOT_IMPLEMENTED",
            "Production inbound document persistence and fiscal lifecycle are not implemented.",
        ),
        _check(
            "public_route_persistence_disabled",
            "DISABLED",
            "Public /fe/... routes remain 503 DISABLED and must not write lab records.",
        ),
        _check(
            "raw_xml_storage_policy_not_approved",
            "MANUAL_REQUIRED",
            "Raw XML storage is disabled by default; policy for lab raw payloads is not approved.",
        ),
        _check(
            "inbound_lab_records_not_fiscal_documents",
            "NOT_CLAIMED",
            "InboundXMLLabRecord is not a received fiscal document and has no Invoice/ECFDocument FK.",
        ),
        _check(
            "inbound_persistence_not_certification_evidence",
            "DESIGN_ONLY",
            "Persisted lab analysis is not DGII certification evidence.",
        ),
        _check(
            "inbound_business_workflow_not_implemented",
            "NOT_IMPLEMENTED",
            "Inbound business routing (ARECF/ACECF/ECF workflows) is not implemented.",
        ),
        _check(
            "inbound_audit_policy_not_approved",
            "MANUAL_REQUIRED",
            "Operational audit/retention policy for inbound lab records is not approved.",
        ),
    ]
