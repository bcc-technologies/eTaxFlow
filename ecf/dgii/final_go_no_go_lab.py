"""Final non-production pre-cert go/no-go review lab (Phase 038)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from django.conf import settings

REVIEW_SCOPE = "FINAL_REVIEW_LAB_ONLY"
LAB_MODE = "NON_PRODUCTION_LAB_ONLY"
POLICY_VERSION = "phase-038-v1"
EXPORT_ROOT = Path("runtime/dgii_final_reviews")

FINAL_DECISION_BLOCKED = "FINAL_DECISION_BLOCKED"
FINAL_DECISION_LAB_ONLY_COMPLETE = "FINAL_DECISION_LAB_ONLY_COMPLETE"
FINAL_DECISION_READY_FOR_HUMAN_REVIEW = "FINAL_DECISION_READY_FOR_HUMAN_REVIEW"

FORBIDDEN_DECISIONS = (
    "READY_FOR_DGII_SUBMISSION",
    "READY_FOR_PRODUCTION",
    "DGII_APPROVED",
    "CERTIFIED",
)

HUMAN_DECISIONS_REQUIRED = (
    "Confirm Phase 024 DGII authorization gate sign-off.",
    "Obtain legal/tax owner approval for pre-certification path.",
    "Obtain security owner approval for inbound controls and staging evidence.",
    "Approve production signing architecture and key custody model.",
    "Confirm certificate custody decision (never store secrets in git).",
    "Approve trust-chain and revocation validation policy.",
    "Review staging DNS/TLS external evidence package.",
    "Explicit decision on public endpoint activation (currently forbidden).",
    "Confirm portal credentials custody.",
    "Explicit decision on DGII certification portal submission (currently forbidden).",
    "Approve incident response and retention policy.",
)

PHASE_038_BLOCKERS = (
    "final_go_no_go_lab_only",
    "final_decision_blocked",
    "final_human_review_not_completed",
    "final_security_owner_approval_missing",
    "final_tax_compliance_approval_missing",
    "final_dgii_authorization_missing",
    "final_public_endpoint_activation_forbidden",
    "final_portal_submission_forbidden",
    "final_dgii_submission_forbidden",
    "final_production_signing_not_approved",
    "final_production_signature_verification_not_ready",
    "final_staging_evidence_not_approved",
    "final_certification_package_blocked",
)


def get_final_decision_vocabulary() -> dict[str, Any]:
    """Allowed final decision values (and explicit forbidden labels)."""
    return {
        "allowed": [
            FINAL_DECISION_BLOCKED,
            FINAL_DECISION_LAB_ONLY_COMPLETE,
            FINAL_DECISION_READY_FOR_HUMAN_REVIEW,
        ],
        "forbidden": list(FORBIDDEN_DECISIONS),
        "current_expected": FINAL_DECISION_BLOCKED,
    }


def collect_final_review_inputs() -> dict[str, Any]:
    """Safely collect prior lab/plan summaries. No network, no DB writes."""
    components: dict[str, Any] = {}

    def _safe(name: str, fn):
        try:
            components[name] = fn()
        except Exception as exc:  # pragma: no cover - defensive
            components[name] = {"error": f"{name}_unavailable:{exc}"}

    def _endpoint():
        from ecf.dgii.endpoints import get_software_registration_metadata

        meta = get_software_registration_metadata()
        return {
            "readiness_status": meta.get("readiness_status"),
            "url_status": meta.get("url_status"),
            "endpoints_enabled": meta.get("endpoints_enabled"),
            "deployment_readiness_status": meta.get("deployment_readiness_status"),
            "staging_evidence_decision": meta.get("staging_evidence_decision"),
            "certification_package_status": meta.get("certification_package_status"),
            "portal_submission_allowed": meta.get("portal_submission_allowed"),
            "production_staging_ready": meta.get("production_staging_ready"),
            "compliance_status": meta.get("compliance_status"),
            "dgii_submission_allowed": meta.get("dgii_submission_allowed"),
        }

    def _receiver():
        from ecf.dgii.receiver import get_receiver_contract_metadata

        meta = get_receiver_contract_metadata()
        return {
            "readiness_status": meta.get("readiness_status"),
            "compliance_status": meta.get("compliance_status"),
            "dgii_submission_allowed": meta.get("dgii_submission_allowed"),
            "portal_submission_allowed": meta.get("portal_submission_allowed"),
            "production_security_ready": meta.get("production_security_ready"),
            "production_staging_ready": meta.get("production_staging_ready"),
            "certification_package_status": meta.get("certification_package_status"),
            "security_policy_decision": meta.get("security_policy_decision"),
        }

    def _readiness():
        from ecf.management.commands.dgii_readiness_report import build_readiness_report

        report = build_readiness_report()
        return {
            "overall_status": report.get("overall_status"),
            "compliance_status": report.get("compliance_status"),
            "dgii_submission_allowed": report.get("dgii_submission_allowed"),
            "portal_submission_allowed": report.get("portal_submission_allowed"),
            "production_signature_ready": report.get("production_signature_ready"),
            "production_security_ready": report.get("production_security_ready"),
            "production_staging_ready": report.get("production_staging_ready"),
            "blocker_count": len(report.get("blockers") or []),
            "blockers": report.get("blockers") or [],
            "not_certification_evidence": report.get("not_certification_evidence", True),
        }

    def _security():
        from ecf.dgii.inbound_security_policy_lab import build_security_policy_report

        report = build_security_policy_report()
        return {
            "policy_decision": report.get("policy_decision"),
            "production_security_ready": report.get("production_security_ready"),
            "blocker_count": len(report.get("blockers") or []),
            "compliance_status": report.get("compliance_status"),
        }

    def _staging():
        from ecf.dgii.staging_evidence_lab import (
            build_evidence_template,
            summarize_evidence,
            validate_evidence_payload,
        )

        return summarize_evidence(validate_evidence_payload(build_evidence_template()))

    def _cert_package():
        from ecf.dgii.certification_package_lab import build_certification_package_draft

        draft = build_certification_package_draft()
        return {
            "package_scope": draft.get("package_scope"),
            "package_status": draft.get("package_status"),
            "submission_allowed": draft.get("submission_allowed"),
            "portal_submission_allowed": draft.get("portal_submission_allowed"),
            "blocker_count": draft.get("blocker_count"),
            "compliance_status": draft.get("compliance_status"),
        }

    def _reporting():
        from ecf.dgii.inbound_reporting_lab import build_inbound_lab_summary

        summary = build_inbound_lab_summary()
        return {
            "report_scope": summary.get("report_scope"),
            "record_count": summary.get("record_count"),
            "blocker_count": summary.get("blocker_count"),
            "compliance_status": summary.get("compliance_status"),
            "includes_raw_xml": summary.get("includes_raw_xml"),
        }

    def _xml_lab():
        return {
            "lab": "dgii_inbound_xml_lab",
            "scope": "NON_PRODUCTION_LAB_ONLY",
            "certification_evidence": False,
        }

    def _schema_lab():
        return {
            "lab": "dgii_inbound_schema_lab",
            "scope": "LOCAL_OFFLINE_ONLY",
            "certification_evidence": False,
        }

    def _signature_lab():
        return {
            "lab": "dgii_inbound_signature_lab",
            "scope": "LOCAL_OFFLINE_TEST_ONLY",
            "cryptographic_verification": "NOT_IMPLEMENTED",
            "certification_evidence": False,
        }

    def _persistence_lab():
        return {
            "lab": "dgii_inbound_persistence_lab",
            "scope": "NON_PRODUCTION_LAB_ONLY",
            "certification_evidence": False,
        }

    def _workflow_lab():
        return {
            "lab": "dgii_inbound_workflow_lab",
            "scope": "NON_PRODUCTION_LAB_ONLY",
            "certification_evidence": False,
        }

    def _audit_lab():
        return {
            "lab": "dgii_inbound_audit_retention_lab",
            "scope": "NON_PRODUCTION_LAB_ONLY",
            "certification_evidence": False,
        }

    _safe("endpoint_plan", _endpoint)
    _safe("receiver_contract", _receiver)
    _safe("readiness", _readiness)
    _safe("security_policy", _security)
    _safe("staging_evidence", _staging)
    _safe("certification_package", _cert_package)
    _safe("inbound_reporting", _reporting)
    _safe("inbound_xml_lab", _xml_lab)
    _safe("inbound_schema_lab", _schema_lab)
    _safe("inbound_signature_lab", _signature_lab)
    _safe("inbound_persistence_lab", _persistence_lab)
    _safe("inbound_workflow_lab", _workflow_lab)
    _safe("inbound_audit_retention_lab", _audit_lab)
    return components


def evaluate_final_go_no_go(
    inputs: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Evaluate final go/no-go. Current project state always BLOCKED."""
    components = inputs if inputs is not None else collect_final_review_inputs()
    readiness = components.get("readiness") or {}
    security = components.get("security_policy") or {}
    staging = components.get("staging_evidence") or {}
    package = components.get("certification_package") or {}
    endpoint = components.get("endpoint_plan") or {}

    public_enabled = bool(
        getattr(settings, "ETAXFLOW_ENABLE_PUBLIC_DGII_ENDPOINTS", False)
    )

    reasons: list[str] = []
    if readiness.get("overall_status") == "BLOCKED" or readiness.get("blockers"):
        reasons.append("Readiness report remains BLOCKED.")
    if security.get("policy_decision") == "SECURITY_POLICY_BLOCKED":
        reasons.append("Security policy decision is SECURITY_POLICY_BLOCKED.")
    if staging.get("staging_evidence_decision") in {
        None,
        "STAGING_EVIDENCE_BLOCKED",
        "STAGING_EVIDENCE_LAB_ONLY",
    }:
        reasons.append("Staging evidence remains blocked or lab-only.")
    if package.get("package_status") == "PACKAGE_BLOCKED":
        reasons.append("Certification package remains PACKAGE_BLOCKED.")
    if not public_enabled:
        reasons.append("Public DGII endpoints remain disabled.")
    if endpoint.get("dgii_submission_allowed") is False:
        reasons.append("Endpoint plan forbids DGII submission.")
    reasons.append("Production signing is not approved.")
    reasons.append("Production signature verification is NOT_IMPLEMENTED.")
    reasons.append("Portal submission remains forbidden.")

    readiness_blockers = list(readiness.get("blockers") or [])
    blockers: list[str] = []
    seen: set[str] = set()
    for name in list(PHASE_038_BLOCKERS) + readiness_blockers:
        if name not in seen:
            seen.add(name)
            blockers.append(name)

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "policy_version": POLICY_VERSION,
        "lab_mode": LAB_MODE,
        "review_scope": REVIEW_SCOPE,
        "final_decision": FINAL_DECISION_BLOCKED,
        "decision_reason": " ".join(reasons),
        "decision_reasons": reasons,
        "decision_vocabulary": get_final_decision_vocabulary(),
        "compliance_status": "NOT_DGII_COMPLIANT",
        "dgii_submission_allowed": False,
        "portal_submission_allowed": False,
        "certification_evidence": False,
        "not_certification_evidence": True,
        "public_endpoints_enabled": public_enabled,
        "endpoint_activation_allowed": False,
        "production_staging_ready": False,
        "production_security_ready": False,
        "production_signature_ready": False,
        "production_signature_verification_ready": False,
        "track_id": None,
        "dgii_call_made": False,
        "network_checks_performed": False,
        "signing_performed": False,
        "portal_upload_performed": False,
        "readiness_status": readiness.get("overall_status") or "BLOCKED",
        "blocker_count": len(blockers),
        "blockers": blockers,
        "human_decisions_required": list(HUMAN_DECISIONS_REQUIRED),
        "component_summaries": components,
        "final_go_no_go_lab_available": True,
        "final_go_no_go_command": "dgii_final_go_no_go_lab",
        "warnings": [
            "FINAL_REVIEW_LAB_ONLY. Final decision is BLOCKED.",
            "Does not authorize portal submission or DGII calls.",
            "Does not authorize public endpoint activation.",
            "Not certification evidence.",
        ],
    }


def build_final_go_no_go_markdown(result: dict[str, Any] | None = None) -> str:
    """Markdown review with explicit FINAL_DECISION_BLOCKED boundary."""
    review = result if result is not None else evaluate_final_go_no_go()
    lines = [
        "# Final non-production pre-cert go/no-go review",
        "",
        "**FINAL_DECISION_BLOCKED** — **NOT_DGII_COMPLIANT** — **FINAL_REVIEW_LAB_ONLY**",
        "",
        "This review does **not** authorize DGII submission, portal upload, endpoint activation, or production signing.",
        "",
        f"- review_scope: `{review.get('review_scope')}`",
        f"- final_decision: `{review.get('final_decision')}`",
        f"- readiness_status: `{review.get('readiness_status')}`",
        f"- dgii_submission_allowed: `{review.get('dgii_submission_allowed')}`",
        f"- portal_submission_allowed: `{review.get('portal_submission_allowed')}`",
        f"- certification_evidence: `{review.get('certification_evidence')}`",
        f"- public_endpoints_enabled: `{review.get('public_endpoints_enabled')}`",
        f"- production_staging_ready: `{review.get('production_staging_ready')}`",
        f"- production_security_ready: `{review.get('production_security_ready')}`",
        f"- production_signature_ready: `{review.get('production_signature_ready')}`",
        f"- production_signature_verification_ready: `{review.get('production_signature_verification_ready')}`",
        f"- track_id: `null`",
        f"- dgii_call_made: `{review.get('dgii_call_made')}`",
        f"- blocker_count: `{review.get('blocker_count')}`",
        "",
        "## Decision reason",
        "",
        review.get("decision_reason") or "Blocked by unresolved pre-certification gates.",
        "",
        "## Human decisions required",
        "",
    ]
    for item in review.get("human_decisions_required") or []:
        lines.append(f"- {item}")
    lines.extend(["", "## Blockers (sample)", ""])
    for blocker in (review.get("blockers") or [])[:25]:
        lines.append(f"- `{blocker}`")
    lines.extend(
        [
            "",
            "No portal submission. No endpoint activation. No signing. No DGII call.",
            "",
        ]
    )
    return "\n".join(lines)


def resolve_output_dir(output_dir: str | Path | None = None) -> Path:
    """Resolve directory under runtime/dgii_final_reviews/; reject traversal."""
    root = EXPORT_ROOT.resolve()
    if output_dir is None:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        candidate = root / f"final_go_no_go_{stamp}"
    else:
        candidate = Path(output_dir)
        if not candidate.is_absolute():
            candidate = (Path.cwd() / candidate).resolve()
        else:
            candidate = candidate.resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise ValueError(
            f"Output path must be under {EXPORT_ROOT}/ (got {candidate})"
        ) from exc
    return candidate


def write_final_go_no_go_review(
    output_dir: str | Path | None = None,
    result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Write JSON/Markdown/manifest under allowed export directory."""
    target = resolve_output_dir(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    review = result if result is not None else evaluate_final_go_no_go()
    md = build_final_go_no_go_markdown(review)
    files = {
        "final_go_no_go_review.json": json.dumps(
            review, indent=2, sort_keys=True, default=str
        )
        + "\n",
        "final_go_no_go_review.md": md if md.endswith("\n") else md + "\n",
    }
    written: list[str] = []
    for name, content in files.items():
        path = target / name
        path.write_text(content, encoding="utf-8")
        written.append(str(path))

    manifest = {
        "generated_at": review["generated_at"],
        "review_scope": REVIEW_SCOPE,
        "final_decision": FINAL_DECISION_BLOCKED,
        "policy_version": POLICY_VERSION,
        "compliance_status": "NOT_DGII_COMPLIANT",
        "dgii_submission_allowed": False,
        "portal_submission_allowed": False,
        "certification_evidence": False,
        "track_id": None,
        "dgii_call_made": False,
        "signing_performed": False,
        "portal_upload_performed": False,
        "files": [Path(p).name for p in written] + ["manifest.json"],
        "output_dir": str(target),
    }
    manifest_path = target / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    written.append(str(manifest_path))
    return {
        **review,
        "files_exported": written,
        "output_dir": str(target),
        "final_go_no_go_status": "RUN",
        "final_inbound_audit_lab_available": True,
        "final_inbound_audit_command": "dgii_final_inbound_audit_lab",
        "final_inbound_audit_status": "NOT_RUN_BY_DEFAULT",
    }
