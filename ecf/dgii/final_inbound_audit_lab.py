"""Final inbound lab audit report (Phase 039 — FINAL_AUDIT_LAB_ONLY)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from django.conf import settings

REPORT_SCOPE = "FINAL_AUDIT_LAB_ONLY"
LAB_MODE = "NON_PRODUCTION_LAB_ONLY"
POLICY_VERSION = "phase-039-v1"
EXPORT_ROOT = Path("runtime/dgii_final_audit_reports")
PHASE_RANGE = "024-039"
FINAL_DECISION_BLOCKED = "FINAL_DECISION_BLOCKED"

PHASE_039_BLOCKERS = (
    "final_audit_report_lab_only",
    "final_audit_not_certification_evidence",
    "remaining_human_decisions_open",
    "production_cutover_not_allowed",
    "dgii_submission_not_allowed",
    "portal_submission_not_allowed",
    "endpoint_activation_not_allowed",
    "final_decision_blocked_after_audit",
)

HUMAN_DECISIONS_REQUIRED = (
    "Phase 024 DGII authorization gate sign-off.",
    "Legal/tax owner approval.",
    "Security owner approval.",
    "Production signing architecture approval.",
    "Certificate custody decision (never store secrets in git).",
    "Trust-chain and revocation validation policy approval.",
    "Staging DNS/TLS external evidence review.",
    "Public endpoint activation decision (currently forbidden).",
    "Portal credentials confirmation.",
    "DGII certification portal submission decision (currently forbidden).",
    "Incident response and retention policy approval.",
    "Production data retention policy approval.",
    "Raw XML storage policy approval.",
    "Operational monitoring policy approval.",
)

NEXT_OPERATIONAL_STEPS = (
    "Push and tag Phase 039 after local completion.",
    "Keep revamp/dgii-vault-mvp unmerged until human review is complete.",
    "Perform human review of final inbound lab audit report.",
    "Review remaining readiness blockers with security, tax/compliance, and DGII owners.",
    "Decide whether to collect real staging deployment evidence (offline/manual).",
    "Do not enable public /fe/... endpoints without explicit written approval.",
    "Do not attempt DGII portal submission until all authorization gates are closed.",
    "Do not proceed to production cutover from lab artifacts alone.",
)

_PHASE_INVENTORY: tuple[dict[str, Any], ...] = (
    {
        "phase": "024",
        "title": "Source intake and authorization gate",
        "status": "MANUAL_REQUIRED",
        "expected_artifacts": [
            "docs/dgii/source_intake/",
            "docs/dgii/governance/PHASE_024_DGII_AUTHORIZATION_GATE.md",
        ],
        "boundary": "Human gate; not DGII authorization.",
    },
    {
        "phase": "025",
        "title": "Pre-certification endpoint design",
        "status": "DESIGN_ONLY",
        "expected_artifacts": [
            "docs/dgii/endpoints/PRE_CERTIFICATION_ENDPOINT_DESIGN.md",
            "dgii_endpoint_plan",
        ],
        "boundary": "Design-only URLs; no live endpoints.",
    },
    {
        "phase": "026",
        "title": "Staging DNS/SSL checklist",
        "status": "CHECKLIST_ONLY",
        "expected_artifacts": [
            "docs/deployment/DGII_STAGING_DNS_SSL_CHECKLIST.md",
        ],
        "boundary": "Human checklist; no automatic deployment.",
    },
    {
        "phase": "027",
        "title": "Receiver endpoint contract",
        "status": "DESIGN_ONLY",
        "expected_artifacts": [
            "docs/dgii/endpoints/PRE_CERTIFICATION_RECEIVER_ENDPOINT_CONTRACT.md",
            "dgii_receiver_contract",
        ],
        "boundary": "Contract skeleton; routes disabled.",
    },
    {
        "phase": "028",
        "title": "Non-production inbound XML lab",
        "status": "LAB_ONLY",
        "expected_artifacts": [
            "ecf/dgii/inbound_lab.py",
            "dgii_inbound_xml_lab",
        ],
        "boundary": "Synthetic fixtures only; not certification evidence.",
    },
    {
        "phase": "029",
        "title": "Local inbound schema validation lab",
        "status": "LOCAL_OFFLINE_ONLY",
        "expected_artifacts": [
            "ecf/dgii/inbound_schema_lab.py",
            "dgii_inbound_schema_lab",
        ],
        "boundary": "Local XSD only; not DGII acceptance.",
    },
    {
        "phase": "030",
        "title": "Local inbound signature inspection lab",
        "status": "LOCAL_OFFLINE_TEST_ONLY",
        "expected_artifacts": [
            "ecf/dgii/inbound_signature_lab.py",
            "dgii_inbound_signature_lab",
        ],
        "boundary": "Presence not validity; crypto verify NOT_IMPLEMENTED.",
    },
    {
        "phase": "031",
        "title": "Non-production inbound persistence lab",
        "status": "LAB_ONLY",
        "expected_artifacts": [
            "InboundXMLLabRecord",
            "dgii_inbound_persistence_lab",
        ],
        "boundary": "Lab-only rows; not fiscal documents.",
    },
    {
        "phase": "032",
        "title": "Non-production inbound workflow routing lab",
        "status": "LAB_ONLY",
        "expected_artifacts": [
            "InboundXMLLabWorkflowEvent",
            "dgii_inbound_workflow_lab",
        ],
        "boundary": "Not fiscal acceptance workflow.",
    },
    {
        "phase": "033",
        "title": "Non-production inbound audit retention lab",
        "status": "LAB_ONLY",
        "expected_artifacts": [
            "InboundXMLLabAuditEvent",
            "dgii_inbound_audit_retention_lab",
        ],
        "boundary": "Not DGII audit trail; metadata export only.",
    },
    {
        "phase": "034",
        "title": "Inbound security controls policy review lab",
        "status": "SECURITY_POLICY_BLOCKED",
        "expected_artifacts": [
            "ecf/dgii/inbound_security_policy_lab.py",
            "dgii_inbound_security_policy_lab",
        ],
        "boundary": "Placeholders not enforced controls.",
    },
    {
        "phase": "035",
        "title": "Inbound reporting export lab",
        "status": "METADATA_ONLY",
        "expected_artifacts": [
            "ecf/dgii/inbound_reporting_lab.py",
            "runtime/dgii_lab_reports/",
        ],
        "boundary": "No raw XML export by default.",
    },
    {
        "phase": "036",
        "title": "Staging deployment evidence collector lab",
        "status": "STAGING_EVIDENCE_BLOCKED",
        "expected_artifacts": [
            "ecf/dgii/staging_evidence_lab.py",
            "runtime/dgii_staging_evidence/",
        ],
        "boundary": "Offline/manual evidence; no network checks.",
    },
    {
        "phase": "037",
        "title": "Certification portal package draft lab",
        "status": "PACKAGE_BLOCKED",
        "expected_artifacts": [
            "ecf/dgii/certification_package_lab.py",
            "runtime/dgii_certification_package_drafts/",
        ],
        "boundary": "DRAFT_ONLY; no portal submission.",
    },
    {
        "phase": "038",
        "title": "Final pre-cert go/no-go review lab",
        "status": "FINAL_DECISION_BLOCKED",
        "expected_artifacts": [
            "ecf/dgii/final_go_no_go_lab.py",
            "runtime/dgii_final_reviews/",
        ],
        "boundary": "FINAL_REVIEW_LAB_ONLY; no endpoint activation.",
    },
    {
        "phase": "039",
        "title": "Final inbound lab audit report",
        "status": "FINAL_AUDIT_LAB_ONLY",
        "expected_artifacts": [
            "ecf/dgii/final_inbound_audit_lab.py",
            "runtime/dgii_final_audit_reports/",
        ],
        "boundary": "Consolidated audit; not certification evidence.",
    },
)

_COMMAND_INVENTORY: tuple[dict[str, str], ...] = (
    {"command": "dgii_inbound_xml_lab", "scope": "NON_PRODUCTION_LAB_ONLY"},
    {"command": "dgii_inbound_schema_lab", "scope": "LOCAL_OFFLINE_ONLY"},
    {"command": "dgii_inbound_signature_lab", "scope": "LOCAL_OFFLINE_TEST_ONLY"},
    {"command": "dgii_inbound_persistence_lab", "scope": "NON_PRODUCTION_LAB_ONLY"},
    {"command": "dgii_inbound_workflow_lab", "scope": "NON_PRODUCTION_LAB_ONLY"},
    {"command": "dgii_inbound_audit_retention_lab", "scope": "NON_PRODUCTION_LAB_ONLY"},
    {"command": "dgii_inbound_security_policy_lab", "scope": "NON_PRODUCTION_LAB_ONLY"},
    {"command": "dgii_inbound_reporting_lab", "scope": "NON_PRODUCTION_LAB_ONLY"},
    {"command": "dgii_staging_evidence_lab", "scope": "NON_PRODUCTION_LAB_ONLY"},
    {"command": "dgii_certification_package_lab", "scope": "DRAFT_ONLY"},
    {"command": "dgii_final_go_no_go_lab", "scope": "FINAL_REVIEW_LAB_ONLY"},
    {"command": "dgii_final_inbound_audit_lab", "scope": "FINAL_AUDIT_LAB_ONLY"},
    {"command": "dgii_endpoint_plan", "scope": "DESIGN_ONLY"},
    {"command": "dgii_receiver_contract", "scope": "DESIGN_ONLY"},
    {"command": "dgii_readiness_report", "scope": "BLOCKED"},
)

_MODEL_INVENTORY: tuple[dict[str, str], ...] = (
    {
        "model": "InboundXMLLabRecord",
        "scope": "NON_PRODUCTION_LAB_ONLY",
        "notes": "Lab-only analysis row; not a fiscal document; no TrackId.",
    },
    {
        "model": "InboundXMLLabWorkflowEvent",
        "scope": "NON_PRODUCTION_LAB_ONLY",
        "notes": "Lab workflow routing; not fiscal acceptance.",
    },
    {
        "model": "InboundXMLLabAuditEvent",
        "scope": "NON_PRODUCTION_LAB_ONLY",
        "notes": "Lab audit/retention; not DGII audit trail.",
    },
)


def get_phase_inventory() -> list[dict[str, Any]]:
    return [dict(item) for item in _PHASE_INVENTORY]


def get_command_inventory() -> list[dict[str, str]]:
    return [dict(item) for item in _COMMAND_INVENTORY]


def get_model_inventory() -> list[dict[str, str]]:
    return [dict(item) for item in _MODEL_INVENTORY]


def collect_final_inbound_audit_inputs() -> dict[str, Any]:
    """Safely collect summaries from prior labs. No network, no DB writes."""
    components: dict[str, Any] = {}

    def _safe(name: str, fn):
        try:
            components[name] = fn()
        except Exception as exc:  # pragma: no cover
            components[name] = {"error": f"{name}_unavailable:{exc}"}

    def _final_go_no_go():
        from ecf.dgii.final_go_no_go_lab import evaluate_final_go_no_go

        r = evaluate_final_go_no_go()
        return {
            "final_decision": r.get("final_decision"),
            "review_scope": r.get("review_scope"),
            "blocker_count": r.get("blocker_count"),
            "compliance_status": r.get("compliance_status"),
        }

    def _cert_package():
        from ecf.dgii.certification_package_lab import build_certification_package_draft

        d = build_certification_package_draft()
        return {
            "package_status": d.get("package_status"),
            "package_scope": d.get("package_scope"),
            "submission_allowed": d.get("submission_allowed"),
        }

    def _staging():
        from ecf.dgii.staging_evidence_lab import (
            build_evidence_template,
            summarize_evidence,
            validate_evidence_payload,
        )

        return summarize_evidence(validate_evidence_payload(build_evidence_template()))

    def _reporting():
        from ecf.dgii.inbound_reporting_lab import build_inbound_lab_summary

        s = build_inbound_lab_summary()
        return {
            "report_scope": s.get("report_scope"),
            "record_count": s.get("record_count"),
            "includes_raw_xml": s.get("includes_raw_xml"),
        }

    def _security():
        from ecf.dgii.inbound_security_policy_lab import build_security_policy_report

        r = build_security_policy_report()
        return {
            "policy_decision": r.get("policy_decision"),
            "production_security_ready": r.get("production_security_ready"),
        }

    def _readiness():
        from ecf.management.commands.dgii_readiness_report import build_readiness_report

        r = build_readiness_report()
        return {
            "overall_status": r.get("overall_status"),
            "compliance_status": r.get("compliance_status"),
            "blocker_count": len(r.get("blockers") or []),
            "blockers": r.get("blockers") or [],
            "final_decision": r.get("final_decision"),
        }

    def _endpoint():
        from ecf.dgii.endpoints import get_software_registration_metadata

        m = get_software_registration_metadata()
        return {
            "endpoints_enabled": m.get("endpoints_enabled"),
            "final_decision": m.get("final_decision"),
            "portal_submission_allowed": m.get("portal_submission_allowed"),
        }

    def _receiver():
        from ecf.dgii.receiver import get_receiver_contract_metadata

        m = get_receiver_contract_metadata()
        return {
            "readiness_status": m.get("readiness_status"),
            "final_decision": m.get("final_decision"),
            "portal_submission_allowed": m.get("portal_submission_allowed"),
        }

    _safe("final_go_no_go", _final_go_no_go)
    _safe("certification_package", _cert_package)
    _safe("staging_evidence", _staging)
    _safe("inbound_reporting", _reporting)
    _safe("security_policy", _security)
    _safe("readiness", _readiness)
    _safe("endpoint_plan", _endpoint)
    _safe("receiver_contract", _receiver)
    _safe(
        "inbound_xml_lab",
        lambda: {
            "lab": "dgii_inbound_xml_lab",
            "scope": "NON_PRODUCTION_LAB_ONLY",
            "certification_evidence": False,
        },
    )
    _safe(
        "inbound_schema_lab",
        lambda: {
            "lab": "dgii_inbound_schema_lab",
            "scope": "LOCAL_OFFLINE_ONLY",
            "certification_evidence": False,
        },
    )
    _safe(
        "inbound_signature_lab",
        lambda: {
            "lab": "dgii_inbound_signature_lab",
            "scope": "LOCAL_OFFLINE_TEST_ONLY",
            "crypto_verify": "NOT_IMPLEMENTED",
        },
    )
    _safe(
        "inbound_persistence_lab",
        lambda: {
            "lab": "dgii_inbound_persistence_lab",
            "scope": "NON_PRODUCTION_LAB_ONLY",
            "model": "InboundXMLLabRecord",
        },
    )
    _safe(
        "inbound_workflow_lab",
        lambda: {
            "lab": "dgii_inbound_workflow_lab",
            "scope": "NON_PRODUCTION_LAB_ONLY",
            "model": "InboundXMLLabWorkflowEvent",
        },
    )
    _safe(
        "inbound_audit_retention_lab",
        lambda: {
            "lab": "dgii_inbound_audit_retention_lab",
            "scope": "NON_PRODUCTION_LAB_ONLY",
            "model": "InboundXMLLabAuditEvent",
        },
    )
    return components


def _build_boundary_summary(components: dict[str, Any]) -> dict[str, Any]:
    public_enabled = bool(
        getattr(settings, "ETAXFLOW_ENABLE_PUBLIC_DGII_ENDPOINTS", False)
    )
    readiness = components.get("readiness") or {}
    return {
        "public_endpoints_enabled": public_enabled,
        "public_routes_status": "503_DISABLED" if not public_enabled else "NOT_APPROVED",
        "schema_validation": "LOCAL_OFFLINE_ONLY",
        "signature_verification": "LOCAL_OFFLINE_TEST_ONLY",
        "crypto_xml_dsig_verification": "NOT_IMPLEMENTED",
        "persistence": "NON_PRODUCTION_LAB_ONLY",
        "workflow": "NON_PRODUCTION_LAB_ONLY",
        "audit_retention": "NON_PRODUCTION_LAB_ONLY",
        "security_policy_decision": (components.get("security_policy") or {}).get(
            "policy_decision"
        ),
        "reporting": "METADATA_ONLY_NO_RAW_XML_DEFAULT",
        "staging_evidence_decision": (components.get("staging_evidence") or {}).get(
            "staging_evidence_decision"
        ),
        "certification_package_status": (
            components.get("certification_package") or {}
        ).get("package_status"),
        "final_go_no_go_decision": (components.get("final_go_no_go") or {}).get(
            "final_decision"
        ),
        "readiness_overall_status": readiness.get("overall_status"),
        "dgii_calls_made": False,
        "track_id_created": False,
        "certification_evidence_produced": False,
        "production_signing_implemented": False,
        "production_signature_verification_implemented": False,
    }


def _merge_blockers(readiness_blockers: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for name in list(PHASE_039_BLOCKERS) + readiness_blockers:
        if name not in seen:
            seen.add(name)
            ordered.append(name)
    return ordered


def build_final_inbound_audit_report(
    components: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """JSON-serializable final audit report. Always BLOCKED / NOT_DGII_COMPLIANT."""
    summaries = components if components is not None else collect_final_inbound_audit_inputs()
    readiness = summaries.get("readiness") or {}
    readiness_blockers = list(readiness.get("blockers") or [])
    blockers = _merge_blockers(readiness_blockers)
    public_enabled = bool(
        getattr(settings, "ETAXFLOW_ENABLE_PUBLIC_DGII_ENDPOINTS", False)
    )
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "policy_version": POLICY_VERSION,
        "lab_mode": LAB_MODE,
        "report_scope": REPORT_SCOPE,
        "phase_range": PHASE_RANGE,
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
        "final_decision": FINAL_DECISION_BLOCKED,
        "track_id": None,
        "dgii_call_made": False,
        "network_checks_performed": False,
        "signing_performed": False,
        "portal_upload_performed": False,
        "phase_inventory": get_phase_inventory(),
        "command_inventory": get_command_inventory(),
        "model_inventory": get_model_inventory(),
        "component_summaries": summaries,
        "boundary_summary": _build_boundary_summary(summaries),
        "blocker_count": len(blockers),
        "blockers": blockers,
        "human_decisions_required": list(HUMAN_DECISIONS_REQUIRED),
        "next_operational_steps": list(NEXT_OPERATIONAL_STEPS),
        "final_inbound_audit_lab_available": True,
        "final_inbound_audit_command": "dgii_final_inbound_audit_lab",
        "required_final_statements": {
            "NOT_DGII_COMPLIANT": True,
            "dgii_submission_allowed": False,
            "portal_submission_allowed": False,
            "public_endpoints_enabled": public_enabled,
            "endpoint_activation_allowed": False,
            "no_dgii_calls": True,
            "no_track_id": True,
            "no_certification_evidence": True,
            "no_production_signing": True,
            "no_production_signature_verification": True,
            "lab_only_persistence": True,
            "public_routes_disabled": not public_enabled,
            "final_decision": FINAL_DECISION_BLOCKED,
        },
        "warnings": [
            "FINAL_AUDIT_LAB_ONLY. Not DGII certification evidence.",
            "Does not authorize portal submission or endpoint activation.",
            "Does not authorize DGII calls or production signing.",
        ],
    }


def build_final_inbound_audit_markdown(
    report: dict[str, Any] | None = None,
) -> str:
    """Markdown audit report with explicit NOT_DGII_COMPLIANT boundary."""
    data = report if report is not None else build_final_inbound_audit_report()
    boundary = data.get("boundary_summary") or {}
    lines = [
        "# Final inbound lab audit report",
        "",
        "**NOT_DGII_COMPLIANT** — **FINAL_DECISION_BLOCKED** — **FINAL_AUDIT_LAB_ONLY**",
        "",
        "dgii_submission_allowed=false · portal_submission_allowed=false · certification_evidence=false",
        "",
        f"- phase_range: `{data.get('phase_range')}`",
        f"- report_scope: `{data.get('report_scope')}`",
        f"- final_decision: `{data.get('final_decision')}`",
        f"- dgii_submission_allowed: `false`",
        f"- portal_submission_allowed: `false`",
        f"- certification_evidence: `false`",
        f"- public_endpoints_enabled: `{str(data.get('public_endpoints_enabled')).lower()}`",
        f"- endpoint_activation_allowed: `false`",
        f"- production_signature_verification_ready: `false`",
        f"- track_id: `null`",
        f"- dgii_call_made: `{data.get('dgii_call_made')}`",
        f"- blocker_count: `{data.get('blocker_count')}`",
        "",
        "## Boundary summary",
        "",
        f"- public_routes_status: `{boundary.get('public_routes_status')}`",
        f"- schema_validation: `{boundary.get('schema_validation')}`",
        f"- signature_verification: `{boundary.get('signature_verification')}`",
        f"- crypto_xml_dsig_verification: `{boundary.get('crypto_xml_dsig_verification')}`",
        f"- security_policy: `{boundary.get('security_policy_decision')}`",
        f"- staging_evidence: `{boundary.get('staging_evidence_decision')}`",
        f"- certification_package: `{boundary.get('certification_package_status')}`",
        "",
        "## Human decisions required",
        "",
    ]
    for item in data.get("human_decisions_required") or []:
        lines.append(f"- {item}")
    lines.extend(["", "## Next operational steps", ""])
    for item in data.get("next_operational_steps") or []:
        lines.append(f"- {item}")
    lines.extend(["", "## Blockers (sample)", ""])
    for blocker in (data.get("blockers") or [])[:25]:
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
    """Resolve directory under runtime/dgii_final_audit_reports/; reject traversal."""
    root = EXPORT_ROOT.resolve()
    if output_dir is None:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        candidate = root / f"final_inbound_audit_{stamp}"
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


def _assert_no_raw_xml(obj: Any) -> None:
    blob = json.dumps(obj, default=str)
    if "raw_xml_text" in blob:
        raise ValueError("Audit report must not include raw_xml_text")


def write_final_inbound_audit_report(
    output_dir: str | Path | None = None,
    report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Write JSON/Markdown/manifest under allowed export directory."""
    target = resolve_output_dir(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    data = report if report is not None else build_final_inbound_audit_report()
    _assert_no_raw_xml(data)
    md = build_final_inbound_audit_markdown(data)
    files = {
        "final_inbound_lab_audit_report.json": json.dumps(
            data, indent=2, sort_keys=True, default=str
        )
        + "\n",
        "final_inbound_lab_audit_report.md": md if md.endswith("\n") else md + "\n",
    }
    written: list[str] = []
    for name, content in files.items():
        path = target / name
        path.write_text(content, encoding="utf-8")
        written.append(str(path))

    manifest = {
        "generated_at": data["generated_at"],
        "report_scope": REPORT_SCOPE,
        "phase_range": PHASE_RANGE,
        "final_decision": FINAL_DECISION_BLOCKED,
        "compliance_status": "NOT_DGII_COMPLIANT",
        "certification_evidence": False,
        "dgii_submission_allowed": False,
        "portal_submission_allowed": False,
        "track_id": None,
        "dgii_call_made": False,
        "includes_raw_xml": False,
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
        **data,
        "files_exported": written,
        "output_dir": str(target),
        "final_inbound_audit_status": "RUN",
    }
