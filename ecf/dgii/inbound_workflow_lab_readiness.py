"""Inbound workflow lab readiness checks (Phase 032)."""

from __future__ import annotations

from typing import Any


def build_inbound_workflow_lab_readiness_checks() -> list[dict[str, Any]]:
    def _check(name: str, status: str, detail: str, *, blocker: bool = True) -> dict:
        return {"name": name, "status": status, "detail": detail, "blocker": blocker}

    return [
        _check(
            "inbound_workflow_lab_only",
            "DESIGN_ONLY",
            "Inbound workflow routing exists only as NON_PRODUCTION_LAB_ONLY lab events.",
        ),
        _check(
            "production_inbound_workflow_not_implemented",
            "NOT_IMPLEMENTED",
            "Production inbound fiscal workflow, acuse, and aprobación are not implemented.",
        ),
        _check(
            "public_route_workflow_disabled",
            "DISABLED",
            "Public /fe/... routes remain 503 DISABLED and must not run workflow routing.",
        ),
        _check(
            "fiscal_acceptance_workflow_not_implemented",
            "NOT_IMPLEMENTED",
            "Lab workflow routes do not imply fiscal acceptance or DGII approval.",
        ),
        _check(
            "acuse_generation_not_implemented",
            "NOT_IMPLEMENTED",
            "Signed ARECF/acuse generation is not implemented.",
        ),
        _check(
            "aprobacion_comercial_generation_not_implemented",
            "NOT_IMPLEMENTED",
            "Signed ACECF/aprobación comercial generation is not implemented.",
        ),
        _check(
            "workflow_policy_not_approved",
            "MANUAL_REQUIRED",
            "Operational workflow routing policy for production inbound is not approved.",
        ),
        _check(
            "inbound_workflow_not_certification_evidence",
            "DESIGN_ONLY",
            "Lab workflow routing is not DGII certification evidence.",
        ),
    ]
