"""Final inbound audit lab readiness checks (Phase 039)."""

from __future__ import annotations

from typing import Any


def build_final_inbound_audit_lab_readiness_checks() -> list[dict[str, Any]]:
    def _check(name: str, status: str, detail: str, *, blocker: bool = True) -> dict:
        return {"name": name, "status": status, "detail": detail, "blocker": blocker}

    return [
        _check(
            "final_audit_report_lab_only",
            "DESIGN_ONLY",
            "Final inbound audit report exists only as FINAL_AUDIT_LAB_ONLY output.",
        ),
        _check(
            "final_audit_not_certification_evidence",
            "NOT_CLAIMED",
            "Final audit report is not DGII certification evidence.",
        ),
        _check(
            "remaining_human_decisions_open",
            "MANUAL_REQUIRED",
            "Human legal/security/DGII decisions remain open after audit.",
        ),
        _check(
            "production_cutover_not_allowed",
            "BLOCKED",
            "Production cutover is not allowed from lab artifacts alone.",
        ),
        _check(
            "dgii_submission_not_allowed",
            "BLOCKED",
            "DGII submission remains forbidden.",
        ),
        _check(
            "portal_submission_not_allowed",
            "BLOCKED",
            "Portal submission remains forbidden.",
        ),
        _check(
            "endpoint_activation_not_allowed",
            "BLOCKED",
            "Public endpoint activation remains forbidden.",
        ),
        _check(
            "final_decision_blocked_after_audit",
            "BLOCKED",
            "Final decision remains FINAL_DECISION_BLOCKED after audit consolidation.",
        ),
    ]
