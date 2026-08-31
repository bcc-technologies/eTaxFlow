"""Inbound security controls policy review lab (Phase 034 — report only, no DGII)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from django.conf import settings

LAB_MODE = "NON_PRODUCTION_LAB_ONLY"
POLICY_VERSION = "phase-034-v1"
POLICY_SCOPE = "NON_PRODUCTION_LAB_ONLY"
EXPORT_ROOT = Path("runtime/dgii_security_reports")

CONTROL_PASS = "CONTROL_PASS"
CONTROL_FAIL = "CONTROL_FAIL"
CONTROL_WARNING = "CONTROL_WARNING"
CONTROL_NOT_IMPLEMENTED = "CONTROL_NOT_IMPLEMENTED"
CONTROL_NOT_APPLICABLE = "CONTROL_NOT_APPLICABLE"
CONTROL_MANUAL_REVIEW_REQUIRED = "CONTROL_MANUAL_REVIEW_REQUIRED"

SECURITY_POLICY_BLOCKED = "SECURITY_POLICY_BLOCKED"
SECURITY_POLICY_LAB_ONLY = "SECURITY_POLICY_LAB_ONLY"
SECURITY_POLICY_MANUAL_REVIEW_REQUIRED = "SECURITY_POLICY_MANUAL_REVIEW_REQUIRED"
SECURITY_POLICY_READY_FOR_HUMAN_REVIEW = "SECURITY_POLICY_READY_FOR_HUMAN_REVIEW"


def _control(
    control_id: str,
    name: str,
    family: str,
    current_status: str,
    evidence: str,
    *,
    required_before_public_processing: bool = True,
    blocker: bool = False,
    notes: str = "",
) -> dict[str, Any]:
    return {
        "control_id": control_id,
        "name": name,
        "family": family,
        "required_before_public_processing": required_before_public_processing,
        "current_status": current_status,
        "evidence": evidence,
        "blocker": blocker,
        "notes": notes,
    }


def get_security_control_catalog() -> list[dict[str, Any]]:
    """Deterministic inbound security control catalog (lab/design evidence only)."""
    endpoints_enabled = bool(getattr(settings, "ETAXFLOW_ENABLE_PUBLIC_DGII_ENDPOINTS", False))
    public_base_url = str(getattr(settings, "ETAXFLOW_PUBLIC_BASE_URL", "") or "")
    max_body = getattr(settings, "ETAXFLOW_DGII_INBOUND_MAX_BODY_BYTES", None)
    allowed_types = getattr(settings, "ETAXFLOW_DGII_INBOUND_ALLOWED_CONTENT_TYPES", None)
    rate_policy = getattr(settings, "ETAXFLOW_DGII_INBOUND_RATE_LIMIT_POLICY", "NOT_IMPLEMENTED")
    log_raw = bool(getattr(settings, "ETAXFLOW_DGII_LOG_RAW_XML", False))
    store_raw_default = bool(getattr(settings, "ETAXFLOW_DGII_STORE_RAW_XML_DEFAULT", False))
    live_transport = bool(getattr(settings, "DGII_LIVE_TRANSPORT_ENABLED", False))

    body_placeholder = max_body is not None
    content_type_placeholder = bool(allowed_types)

    return [
        _control(
            "endpoint_disabled_by_default",
            "Public DGII endpoints disabled by default",
            "endpoint_gate",
            CONTROL_PASS if not endpoints_enabled else CONTROL_FAIL,
            f"ETAXFLOW_ENABLE_PUBLIC_DGII_ENDPOINTS={endpoints_enabled}",
            blocker=bool(endpoints_enabled),
            notes="Default must remain false until all security gates pass.",
        ),
        _control(
            "public_base_url_not_required_by_default",
            "Public base URL blank by default",
            "endpoint_gate",
            CONTROL_PASS if not public_base_url else CONTROL_WARNING,
            f"ETAXFLOW_PUBLIC_BASE_URL={'set' if public_base_url else 'blank'}",
            blocker=False,
        ),
        _control(
            "disabled_routes_return_503",
            "Disabled public routes return 503 JSON",
            "endpoint_gate",
            CONTROL_PASS,
            "ecf.views.dgii_public_endpoints return JsonResponse(..., status=503)",
        ),
        _control(
            "disabled_routes_do_not_parse_xml",
            "Disabled routes do not parse request body",
            "endpoint_gate",
            CONTROL_PASS,
            "Views intentionally ignore request.body while disabled",
        ),
        _control(
            "disabled_routes_do_not_persist",
            "Disabled routes do not persist inbound data",
            "endpoint_gate",
            CONTROL_PASS,
            "No persistence/workflow/audit service imports from public views",
        ),
        _control(
            "disabled_routes_do_not_create_trackid",
            "Disabled routes do not create TrackId",
            "endpoint_gate",
            CONTROL_PASS,
            "Disabled response track_id=null; no TrackId factory",
        ),
        _control(
            "allowed_methods_policy_defined",
            "Allowed HTTP methods documented on stubs",
            "request_policy",
            CONTROL_WARNING,
            "Stubs accept GET/POST/etc but always return 503; future allowlist not enforced",
            notes="CONFIGURED_PLACEHOLDER / DESIGN_ONLY — not production method enforcement",
        ),
        _control(
            "body_size_limit_not_implemented",
            "Inbound body size limit not enforced on public routes",
            "request_policy",
            CONTROL_NOT_IMPLEMENTED,
            (
                f"ETAXFLOW_DGII_INBOUND_MAX_BODY_BYTES={max_body} "
                f"({'CONFIGURED_PLACEHOLDER' if body_placeholder else 'missing'}) — not ENFORCED"
            ),
            blocker=True,
            notes="Placeholder setting does not equal enforcement.",
        ),
        _control(
            "content_type_allowlist_not_enforced",
            "Content-Type allowlist not enforced on public routes",
            "request_policy",
            CONTROL_NOT_IMPLEMENTED,
            (
                f"ETAXFLOW_DGII_INBOUND_ALLOWED_CONTENT_TYPES={allowed_types} "
                f"({'CONFIGURED_PLACEHOLDER' if content_type_placeholder else 'missing'}) — not ENFORCED"
            ),
            blocker=True,
            notes="Placeholder setting does not equal enforcement.",
        ),
        _control(
            "safe_xml_parser_available",
            "Safe XML parser helpers available for lab paths",
            "xml_parser",
            CONTROL_PASS,
            "Lab parsers use resolve_entities=False, no_network=True",
            notes="Lab-only; public disabled routes do not parse.",
        ),
        _control(
            "external_entity_resolution_disabled",
            "External entity resolution disabled in lab parsers",
            "xml_parser",
            CONTROL_PASS,
            "lxml XMLParser(resolve_entities=False) in inbound labs",
        ),
        _control(
            "no_network_xml_parsing",
            "Network disabled during lab XML parse",
            "xml_parser",
            CONTROL_PASS,
            "lxml XMLParser(no_network=True) in inbound labs",
        ),
        _control(
            "rate_limiting_not_implemented",
            "Inbound rate limiting not implemented",
            "abuse_controls",
            CONTROL_NOT_IMPLEMENTED,
            f"ETAXFLOW_DGII_INBOUND_RATE_LIMIT_POLICY={rate_policy}",
            blocker=True,
        ),
        _control(
            "logging_redaction_policy_needed",
            "Logging redaction policy not approved",
            "logging",
            CONTROL_MANUAL_REVIEW_REQUIRED,
            f"ETAXFLOW_DGII_LOG_RAW_XML={log_raw} (must remain false in production)",
            blocker=True,
        ),
        _control(
            "raw_xml_storage_disabled_by_default",
            "Raw XML storage disabled by default",
            "data_handling",
            CONTROL_PASS if not store_raw_default else CONTROL_FAIL,
            f"ETAXFLOW_DGII_STORE_RAW_XML_DEFAULT={store_raw_default}",
            blocker=bool(store_raw_default),
        ),
        _control(
            "duplicate_detection_lab_only",
            "Duplicate detection is lab/idempotency only",
            "data_handling",
            CONTROL_WARNING,
            "raw_sha256 unique upsert in persistence lab; production replay controls NOT_IMPLEMENTED",
            blocker=True,
            notes="Lab hash uniqueness is not production replay protection.",
        ),
        _control(
            "production_signature_verification_not_implemented",
            "Production XMLDSig verification not implemented",
            "cryptography",
            CONTROL_NOT_IMPLEMENTED,
            "Signature lab LOCAL_OFFLINE_TEST_ONLY; cryptographic verify NOT_IMPLEMENTED",
            blocker=True,
        ),
        _control(
            "certificate_trust_chain_not_implemented",
            "Certificate trust-chain validation not implemented",
            "cryptography",
            CONTROL_NOT_IMPLEMENTED,
            "No production trust store / chain validation",
            blocker=True,
        ),
        _control(
            "revocation_check_not_implemented",
            "Certificate revocation (CRL/OCSP) not implemented",
            "cryptography",
            CONTROL_NOT_IMPLEMENTED,
            "No CRL/OCSP network checks; intentionally disabled",
            blocker=True,
        ),
        _control(
            "audit_retention_lab_only",
            "Audit/retention is lab-only",
            "audit_retention",
            CONTROL_WARNING,
            "InboundXMLLabAuditEvent + dgii_inbound_audit_retention_lab only",
            blocker=True,
        ),
        _control(
            "destructive_retention_disabled",
            "Destructive retention actions disabled",
            "audit_retention",
            CONTROL_PASS,
            "Phase 033/034 do not delete or purge lab records",
        ),
        _control(
            "secret_storage_policy_needed",
            "Secret management policy not verified",
            "secrets",
            CONTROL_MANUAL_REVIEW_REQUIRED,
            "No private keys in repo; deployment secret manager integration still required",
            blocker=True,
        ),
        _control(
            "environment_separation_not_verified",
            "Staging/production environment separation not verified",
            "environment",
            CONTROL_MANUAL_REVIEW_REQUIRED,
            "Staging DNS/SSL checklist exists; human verification pending",
            blocker=True,
        ),
        _control(
            "dns_tls_not_verified",
            "Public receiver DNS/TLS not verified",
            "environment",
            CONTROL_MANUAL_REVIEW_REQUIRED,
            "Phase 026 checklist UNVERIFIED by default",
            blocker=True,
        ),
        _control(
            "human_authorization_gate_not_signed_off",
            "Phase 024 human authorization gate not signed off",
            "governance",
            CONTROL_MANUAL_REVIEW_REQUIRED,
            "docs/dgii/governance/PHASE_024_DGII_AUTHORIZATION_GATE.md requires human owner",
            blocker=True,
        ),
        _control(
            "dgii_submission_disabled",
            "DGII submission disabled",
            "transport",
            CONTROL_PASS if not live_transport else CONTROL_FAIL,
            f"DGII_LIVE_TRANSPORT_ENABLED={live_transport}; dgii_submission_allowed=false",
            blocker=bool(live_transport),
        ),
        _control(
            "trackid_creation_disabled",
            "TrackId creation disabled",
            "transport",
            CONTROL_PASS,
            "track_id_creation=DISABLED across labs and disabled responses",
        ),
    ]


def evaluate_security_policy() -> dict[str, Any]:
    """Evaluate inbound security policy. Always BLOCKED until gates are human-approved."""
    controls = get_security_control_catalog()
    pass_count = sum(1 for c in controls if c["current_status"] == CONTROL_PASS)
    fail_count = sum(1 for c in controls if c["current_status"] == CONTROL_FAIL)
    warning_count = sum(1 for c in controls if c["current_status"] == CONTROL_WARNING)
    not_implemented_count = sum(
        1 for c in controls if c["current_status"] == CONTROL_NOT_IMPLEMENTED
    )
    manual_review_count = sum(
        1 for c in controls if c["current_status"] == CONTROL_MANUAL_REVIEW_REQUIRED
    )
    blockers = [c["control_id"] for c in controls if c.get("blocker")]
    endpoints_enabled = bool(getattr(settings, "ETAXFLOW_ENABLE_PUBLIC_DGII_ENDPOINTS", False))

    return {
        "policy_scope": POLICY_SCOPE,
        "policy_version": POLICY_VERSION,
        "policy_decision": SECURITY_POLICY_BLOCKED,
        "lab_mode": LAB_MODE,
        "compliance_status": "NOT_DGII_COMPLIANT",
        "dgii_submission_allowed": False,
        "certification_evidence": False,
        "not_certification_evidence": True,
        "public_endpoints_enabled": endpoints_enabled,
        "production_security_ready": False,
        "track_id": None,
        "dgii_call_made": False,
        "controls": controls,
        "pass_count": pass_count,
        "fail_count": fail_count,
        "warning_count": warning_count,
        "not_implemented_count": not_implemented_count,
        "manual_review_count": manual_review_count,
        "blockers": blockers,
        "warnings": [
            "This lab review does not enable public endpoints.",
            "CONFIGURED_PLACEHOLDER settings are not ENFORCED controls.",
            "Not a penetration test or legal/compliance approval.",
            "Not DGII certification evidence.",
        ],
    }


def build_security_policy_report() -> dict[str, Any]:
    """JSON-serializable security policy report."""
    evaluation = evaluate_security_policy()
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "report_type": "DGII_INBOUND_SECURITY_POLICY_LAB",
        "policy_scope": evaluation["policy_scope"],
        "policy_version": evaluation["policy_version"],
        "policy_decision": evaluation["policy_decision"],
        "lab_mode": evaluation["lab_mode"],
        "compliance_status": evaluation["compliance_status"],
        "dgii_submission_allowed": evaluation["dgii_submission_allowed"],
        "certification_evidence": evaluation["certification_evidence"],
        "not_certification_evidence": True,
        "public_endpoints_enabled": evaluation["public_endpoints_enabled"],
        "production_security_ready": False,
        "track_id": None,
        "dgii_call_made": False,
        "summary": {
            "control_count": len(evaluation["controls"]),
            "pass_count": evaluation["pass_count"],
            "fail_count": evaluation["fail_count"],
            "warning_count": evaluation["warning_count"],
            "not_implemented_count": evaluation["not_implemented_count"],
            "manual_review_count": evaluation["manual_review_count"],
            "blocker_count": len(evaluation["blockers"]),
        },
        "controls": evaluation["controls"],
        "blockers": evaluation["blockers"],
        "warnings": evaluation["warnings"],
        "security_policy_lab_available": True,
        "security_policy_command": "dgii_inbound_security_policy_lab",
        "reporting_lab_available": True,
        "reporting_command": "dgii_inbound_reporting_lab",
        "reporting_status": "NOT_RUN_BY_DEFAULT",
        "staging_evidence_lab_available": True,
        "staging_evidence_command": "dgii_staging_evidence_lab",
        "staging_evidence_status": "NOT_RUN_BY_DEFAULT",
        "certification_package_lab_available": True,
        "certification_package_command": "dgii_certification_package_lab",
        "certification_package_status": "NOT_RUN_BY_DEFAULT",
        "final_go_no_go_lab_available": True,
        "final_go_no_go_command": "dgii_final_go_no_go_lab",
        "final_go_no_go_status": "NOT_RUN_BY_DEFAULT",
    }


def resolve_export_path(export_path: str | Path | None = None) -> Path:
    """Resolve path under runtime/dgii_security_reports/; reject traversal."""
    root = EXPORT_ROOT.resolve()
    if export_path is None:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        candidate = root / f"inbound_security_policy_{stamp}.json"
    else:
        candidate = Path(export_path)
        if not candidate.is_absolute():
            candidate = (Path.cwd() / candidate).resolve()
        else:
            candidate = candidate.resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise ValueError(
            f"Export path must be under {EXPORT_ROOT}/ (got {candidate})"
        ) from exc
    return candidate


def write_security_policy_report(path: Path | str | None, report: dict[str, Any]) -> Path:
    """Write metadata-only JSON under allowed export directory."""
    target = resolve_export_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    safe = dict(report)
    safe.pop("raw_xml_text", None)
    with target.open("w", encoding="utf-8") as handle:
        json.dump(safe, handle, indent=2, sort_keys=True, default=str)
        handle.write("\n")
    return target
