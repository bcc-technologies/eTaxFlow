"""Inbound audit/retention lab readiness checks (Phase 033)."""

from __future__ import annotations

from typing import Any


def build_inbound_audit_retention_lab_readiness_checks() -> list[dict[str, Any]]:
    def _check(name: str, status: str, detail: str, *, blocker: bool = True) -> dict:
        return {"name": name, "status": status, "detail": detail, "blocker": blocker}

    return [
        _check(
            "inbound_audit_retention_lab_only",
            "DESIGN_ONLY",
            "Inbound audit/retention exists only as NON_PRODUCTION_LAB_ONLY lab events.",
        ),
        _check(
            "production_audit_trail_not_implemented",
            "NOT_IMPLEMENTED",
            "Production inbound fiscal audit trail is not implemented.",
        ),
        _check(
            "production_retention_policy_not_approved",
            "MANUAL_REQUIRED",
            "Production retention/legal retention policy is not approved.",
        ),
        _check(
            "public_route_audit_disabled",
            "DISABLED",
            "Public /fe/... routes remain 503 DISABLED and must not write audit events.",
        ),
        _check(
            "destructive_retention_actions_disabled",
            "DISABLED",
            "Phase 033 does not delete or purge lab records; purge candidates are dry-run only.",
        ),
        _check(
            "metadata_export_not_certification_evidence",
            "NOT_CLAIMED",
            "Lab metadata export manifests are not DGII certification evidence.",
        ),
        _check(
            "raw_xml_retention_policy_not_approved",
            "MANUAL_REQUIRED",
            "Raw XML lab storage retention policy is not approved.",
        ),
        _check(
            "audit_retention_policy_not_legal_reviewed",
            "MANUAL_REQUIRED",
            "Lab audit/retention policy has not received legal/compliance review.",
        ),
    ]
