"""Staging deployment evidence collector lab (Phase 036 — offline/manual only)."""

from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from django.conf import settings

LAB_MODE = "NON_PRODUCTION_LAB_ONLY"
EVIDENCE_SCOPE = "NON_PRODUCTION_LAB_ONLY"
POLICY_VERSION = "phase-036-v1"
EXPORT_ROOT = Path("runtime/dgii_staging_evidence")

EVIDENCE_MISSING = "EVIDENCE_MISSING"
EVIDENCE_PROVIDED = "EVIDENCE_PROVIDED"
EVIDENCE_INCOMPLETE = "EVIDENCE_INCOMPLETE"
EVIDENCE_NOT_VERIFIED = "EVIDENCE_NOT_VERIFIED"
EVIDENCE_MANUAL_REVIEW_REQUIRED = "EVIDENCE_MANUAL_REVIEW_REQUIRED"
EVIDENCE_REJECTED = "EVIDENCE_REJECTED"

STAGING_EVIDENCE_BLOCKED = "STAGING_EVIDENCE_BLOCKED"
STAGING_EVIDENCE_LAB_ONLY = "STAGING_EVIDENCE_LAB_ONLY"
STAGING_EVIDENCE_MANUAL_REVIEW_REQUIRED = "STAGING_EVIDENCE_MANUAL_REVIEW_REQUIRED"
STAGING_EVIDENCE_READY_FOR_HUMAN_REVIEW = "STAGING_EVIDENCE_READY_FOR_HUMAN_REVIEW"

_REQUIRED_EVIDENCE: tuple[dict[str, Any], ...] = (
    {
        "evidence_id": "dns_record_configured",
        "category": "dns",
        "title": "DNS record configured for staging host",
        "required_before_portal_submission": True,
        "required_before_public_processing": True,
    },
    {
        "evidence_id": "tls_certificate_present",
        "category": "tls",
        "title": "TLS certificate present for staging host",
        "required_before_portal_submission": True,
        "required_before_public_processing": True,
    },
    {
        "evidence_id": "https_reachability_verified",
        "category": "https",
        "title": "HTTPS reachability verified externally (manual)",
        "required_before_portal_submission": True,
        "required_before_public_processing": True,
    },
    {
        "evidence_id": "public_base_url_configured",
        "category": "configuration",
        "title": "Public base URL configured for staging",
        "required_before_portal_submission": True,
        "required_before_public_processing": True,
    },
    {
        "evidence_id": "recepcion_endpoint_disabled_verified",
        "category": "disabled_routes",
        "title": "Recepción endpoint externally verified DISABLED/503",
        "required_before_portal_submission": True,
        "required_before_public_processing": True,
    },
    {
        "evidence_id": "aprobacion_endpoint_disabled_verified",
        "category": "disabled_routes",
        "title": "Aprobación Comercial endpoint externally verified DISABLED/503",
        "required_before_portal_submission": True,
        "required_before_public_processing": True,
    },
    {
        "evidence_id": "autenticacion_semilla_disabled_verified",
        "category": "disabled_routes",
        "title": "Autenticación semilla endpoint externally verified DISABLED/503",
        "required_before_portal_submission": True,
        "required_before_public_processing": True,
    },
    {
        "evidence_id": "autenticacion_validacion_disabled_verified",
        "category": "disabled_routes",
        "title": "Autenticación validacióncertificado endpoint externally verified DISABLED/503",
        "required_before_portal_submission": True,
        "required_before_public_processing": True,
    },
    {
        "evidence_id": "disabled_post_returns_503_verified",
        "category": "disabled_post",
        "title": "Disabled POST returns 503 (external/manual)",
        "required_before_portal_submission": True,
        "required_before_public_processing": True,
    },
    {
        "evidence_id": "disabled_post_no_xml_parse_verified",
        "category": "disabled_post",
        "title": "Disabled POST does not parse XML (external/manual)",
        "required_before_portal_submission": True,
        "required_before_public_processing": True,
    },
    {
        "evidence_id": "disabled_post_no_db_write_verified",
        "category": "disabled_post",
        "title": "Disabled POST does not write DB (external/manual)",
        "required_before_portal_submission": True,
        "required_before_public_processing": True,
    },
    {
        "evidence_id": "staging_environment_variables_reviewed",
        "category": "environment",
        "title": "Staging environment variables reviewed",
        "required_before_portal_submission": True,
        "required_before_public_processing": True,
    },
    {
        "evidence_id": "staging_database_separation_verified",
        "category": "database",
        "title": "Staging database separation verified",
        "required_before_portal_submission": True,
        "required_before_public_processing": True,
    },
    {
        "evidence_id": "staging_secrets_policy_reviewed",
        "category": "secrets",
        "title": "Staging secrets policy reviewed",
        "required_before_portal_submission": True,
        "required_before_public_processing": True,
    },
    {
        "evidence_id": "staging_logging_redaction_reviewed",
        "category": "logging",
        "title": "Staging logging redaction reviewed",
        "required_before_portal_submission": True,
        "required_before_public_processing": True,
    },
    {
        "evidence_id": "staging_rate_limit_policy_reviewed",
        "category": "security",
        "title": "Staging rate-limit policy reviewed",
        "required_before_portal_submission": True,
        "required_before_public_processing": False,
    },
    {
        "evidence_id": "security_owner_review_completed",
        "category": "governance",
        "title": "Security owner staging review completed",
        "required_before_portal_submission": True,
        "required_before_public_processing": True,
    },
    {
        "evidence_id": "tax_compliance_owner_review_completed",
        "category": "governance",
        "title": "Tax/compliance owner staging review completed",
        "required_before_portal_submission": True,
        "required_before_public_processing": True,
    },
    {
        "evidence_id": "phase_024_authorization_gate_signed_off",
        "category": "governance",
        "title": "Phase 024 authorization gate signed off for staging",
        "required_before_portal_submission": True,
        "required_before_public_processing": True,
    },
)


def get_required_evidence_catalog() -> list[dict[str, Any]]:
    """Deterministic catalog of required manual staging evidence items."""
    items: list[dict[str, Any]] = []
    for raw in _REQUIRED_EVIDENCE:
        items.append(
            {
                **deepcopy(raw),
                "current_status": EVIDENCE_MISSING,
                "manual_review_required": True,
                "blocker": True,
                "notes": (
                    "Manual offline evidence only. This lab does not perform "
                    "DNS/TLS/HTTPS/network checks."
                ),
            }
        )
    return items


def build_evidence_template() -> dict[str, Any]:
    """JSON-serializable template with all required items and empty manual fields."""
    catalog = get_required_evidence_catalog()
    evidence_items = []
    for item in catalog:
        evidence_items.append(
            {
                "evidence_id": item["evidence_id"],
                "category": item["category"],
                "title": item["title"],
                "status": EVIDENCE_MISSING,
                "provided_by": "",
                "reviewed_by": "",
                "reviewed_at": None,
                "source_reference": "",
                "notes": "",
                "evidence_hash": "",
                "manual_review_required": True,
                "required_before_portal_submission": item[
                    "required_before_portal_submission"
                ],
                "required_before_public_processing": item[
                    "required_before_public_processing"
                ],
                "blocker": True,
                "certification_evidence": False,
                "dgii_submission_allowed": False,
                "track_id": None,
                "dgii_call_made": False,
            }
        )
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "policy_version": POLICY_VERSION,
        "evidence_scope": EVIDENCE_SCOPE,
        "lab_mode": LAB_MODE,
        "compliance_status": "NOT_DGII_COMPLIANT",
        "dgii_submission_allowed": False,
        "certification_evidence": False,
        "public_endpoints_enabled": False,
        "production_staging_ready": False,
        "track_id": None,
        "dgii_call_made": False,
        "network_checks_performed": False,
        "staging_evidence_decision": STAGING_EVIDENCE_LAB_ONLY,
        "warnings": [
            "Template is not evidence.",
            "This lab does not perform network checks.",
            "Public endpoints remain DISABLED.",
            "Not DGII certification evidence.",
        ],
        "evidence_items": evidence_items,
    }


def _normalize_item(item: dict[str, Any], catalog_by_id: dict[str, dict[str, Any]]) -> dict[str, Any]:
    evidence_id = str(item.get("evidence_id") or "")
    catalog = catalog_by_id.get(evidence_id, {})
    status = str(item.get("status") or EVIDENCE_MISSING)
    provided_by = str(item.get("provided_by") or "").strip()
    source_reference = str(item.get("source_reference") or "").strip()
    reviewed_by = str(item.get("reviewed_by") or "").strip()
    notes = str(item.get("notes") or "").strip()
    evidence_hash = str(item.get("evidence_hash") or "").strip()

    if status == EVIDENCE_PROVIDED and (not provided_by or not source_reference):
        status = EVIDENCE_INCOMPLETE
    if status == EVIDENCE_PROVIDED and not reviewed_by:
        status = EVIDENCE_MANUAL_REVIEW_REQUIRED

    return {
        "evidence_id": evidence_id,
        "category": item.get("category") or catalog.get("category") or "",
        "title": item.get("title") or catalog.get("title") or evidence_id,
        "status": status,
        "provided_by": provided_by,
        "reviewed_by": reviewed_by,
        "reviewed_at": item.get("reviewed_at"),
        "source_reference": source_reference,
        "notes": notes,
        "evidence_hash": evidence_hash,
        "manual_review_required": bool(
            item.get("manual_review_required", True)
        )
        or status
        in {
            EVIDENCE_MISSING,
            EVIDENCE_INCOMPLETE,
            EVIDENCE_NOT_VERIFIED,
            EVIDENCE_MANUAL_REVIEW_REQUIRED,
        },
        "required_before_portal_submission": bool(
            item.get(
                "required_before_portal_submission",
                catalog.get("required_before_portal_submission", True),
            )
        ),
        "required_before_public_processing": bool(
            item.get(
                "required_before_public_processing",
                catalog.get("required_before_public_processing", True),
            )
        ),
        "blocker": status
        not in {EVIDENCE_PROVIDED}
        or bool(item.get("manual_review_required", True)),
        "certification_evidence": False,
        "dgii_submission_allowed": False,
        "track_id": None,
        "dgii_call_made": False,
    }


def validate_evidence_payload(payload: dict[str, Any] | None) -> dict[str, Any]:
    """Validate loaded evidence JSON. Never claims staging approval or compliance."""
    catalog = get_required_evidence_catalog()
    catalog_by_id = {item["evidence_id"]: item for item in catalog}
    raw_items = list((payload or {}).get("evidence_items") or [])
    by_id = {
        str(item.get("evidence_id")): item
        for item in raw_items
        if item.get("evidence_id")
    }

    evidence_items: list[dict[str, Any]] = []
    for catalog_item in catalog:
        eid = catalog_item["evidence_id"]
        if eid in by_id:
            evidence_items.append(_normalize_item(by_id[eid], catalog_by_id))
        else:
            evidence_items.append(
                _normalize_item(
                    {
                        "evidence_id": eid,
                        "category": catalog_item["category"],
                        "title": catalog_item["title"],
                        "status": EVIDENCE_MISSING,
                        "required_before_portal_submission": catalog_item[
                            "required_before_portal_submission"
                        ],
                        "required_before_public_processing": catalog_item[
                            "required_before_public_processing"
                        ],
                    },
                    catalog_by_id,
                )
            )

    missing = [i for i in evidence_items if i["status"] == EVIDENCE_MISSING]
    incomplete = [i for i in evidence_items if i["status"] == EVIDENCE_INCOMPLETE]
    provided = [
        i
        for i in evidence_items
        if i["status"]
        in {EVIDENCE_PROVIDED, EVIDENCE_MANUAL_REVIEW_REQUIRED, EVIDENCE_NOT_VERIFIED}
    ]
    manual_review = [
        i
        for i in evidence_items
        if i["manual_review_required"] or i["status"] == EVIDENCE_MANUAL_REVIEW_REQUIRED
    ]
    rejected = [i for i in evidence_items if i["status"] == EVIDENCE_REJECTED]

    blockers = [
        i["evidence_id"]
        for i in evidence_items
        if i["blocker"] or i["status"] in {EVIDENCE_MISSING, EVIDENCE_INCOMPLETE, EVIDENCE_REJECTED}
    ]
    # Stable unique order
    seen: set[str] = set()
    ordered_blockers: list[str] = []
    for bid in blockers:
        if bid not in seen:
            seen.add(bid)
            ordered_blockers.append(bid)

    all_required_present = all(
        i["status"]
        in {
            EVIDENCE_PROVIDED,
            EVIDENCE_MANUAL_REVIEW_REQUIRED,
            EVIDENCE_NOT_VERIFIED,
        }
        and i["provided_by"]
        and i["source_reference"]
        for i in evidence_items
        if i["required_before_portal_submission"]
    )
    any_missing_required = any(
        i["status"] in {EVIDENCE_MISSING, EVIDENCE_INCOMPLETE, EVIDENCE_REJECTED}
        for i in evidence_items
        if i["required_before_portal_submission"]
    )

    if any_missing_required or rejected:
        decision = STAGING_EVIDENCE_BLOCKED
    elif all_required_present and manual_review:
        decision = STAGING_EVIDENCE_READY_FOR_HUMAN_REVIEW
    elif provided:
        decision = STAGING_EVIDENCE_MANUAL_REVIEW_REQUIRED
    else:
        decision = STAGING_EVIDENCE_BLOCKED

    public_enabled = bool(
        getattr(settings, "ETAXFLOW_ENABLE_PUBLIC_DGII_ENDPOINTS", False)
    )

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "policy_version": POLICY_VERSION,
        "evidence_scope": EVIDENCE_SCOPE,
        "lab_mode": LAB_MODE,
        "staging_evidence_decision": decision,
        "compliance_status": "NOT_DGII_COMPLIANT",
        "dgii_submission_allowed": False,
        "certification_evidence": False,
        "not_certification_evidence": True,
        "public_endpoints_enabled": public_enabled,
        "production_staging_ready": False,
        "track_id": None,
        "dgii_call_made": False,
        "network_checks_performed": False,
        "evidence_items": evidence_items,
        "missing_count": len(missing),
        "incomplete_count": len(incomplete),
        "provided_count": len(provided),
        "manual_review_count": len(manual_review),
        "rejected_count": len(rejected),
        "blocker_count": len(ordered_blockers),
        "blockers": ordered_blockers,
        "staging_evidence_lab_available": True,
        "staging_evidence_command": "dgii_staging_evidence_lab",
        "warnings": [
            "Offline/manual evidence only. No network checks performed.",
            "Evidence does not equal staging approval or DGII certification.",
            "Public endpoints remain DISABLED unless explicitly enabled elsewhere.",
        ],
    }


def summarize_evidence(evidence_result: dict[str, Any]) -> dict[str, Any]:
    """Compact JSON-serializable summary."""
    return {
        "generated_at": evidence_result.get("generated_at"),
        "evidence_scope": evidence_result.get("evidence_scope", EVIDENCE_SCOPE),
        "staging_evidence_decision": evidence_result.get("staging_evidence_decision"),
        "compliance_status": evidence_result.get("compliance_status"),
        "dgii_submission_allowed": False,
        "certification_evidence": False,
        "public_endpoints_enabled": evidence_result.get("public_endpoints_enabled", False),
        "production_staging_ready": False,
        "track_id": None,
        "dgii_call_made": False,
        "network_checks_performed": False,
        "missing_count": evidence_result.get("missing_count", 0),
        "incomplete_count": evidence_result.get("incomplete_count", 0),
        "provided_count": evidence_result.get("provided_count", 0),
        "manual_review_count": evidence_result.get("manual_review_count", 0),
        "blocker_count": evidence_result.get("blocker_count", 0),
        "blockers": evidence_result.get("blockers") or [],
    }


def resolve_evidence_path(path: str | Path | None = None, *, default_name: str) -> Path:
    """Resolve path under runtime/dgii_staging_evidence/; reject traversal."""
    root = EXPORT_ROOT.resolve()
    if path is None:
        candidate = root / default_name
    else:
        candidate = Path(path)
        if not candidate.is_absolute():
            candidate = (Path.cwd() / candidate).resolve()
        else:
            candidate = candidate.resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise ValueError(
            f"Path must be under {EXPORT_ROOT}/ (got {candidate})"
        ) from exc
    return candidate


def write_evidence_template(path: str | Path | None = None) -> Path:
    """Write template JSON under runtime/dgii_staging_evidence/."""
    target = resolve_evidence_path(path, default_name="staging_evidence_template.json")
    target.parent.mkdir(parents=True, exist_ok=True)
    template = build_evidence_template()
    target.write_text(
        json.dumps(template, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    return target


def write_evidence_report(
    path: str | Path | None,
    evidence_result: dict[str, Any],
) -> Path:
    """Write metadata-only JSON report under runtime/dgii_staging_evidence/."""
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    target = resolve_evidence_path(
        path, default_name=f"staging_evidence_report_{stamp}.json"
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        **evidence_result,
        "report_type": "DGII_STAGING_EVIDENCE_LAB",
        "summary": summarize_evidence(evidence_result),
    }
    target.write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    return target


def load_evidence_file(path: str | Path) -> dict[str, Any]:
    target = resolve_evidence_path(path, default_name="unused.json")
    if not target.is_file():
        raise ValueError(f"Evidence file not found: {target}")
    data = json.loads(target.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Evidence file must contain a JSON object")
    return data


def build_staging_evidence_lab_report(
    *,
    evidence_result: dict[str, Any] | None = None,
    template_path: str | None = None,
    report_path: str | None = None,
) -> dict[str, Any]:
    result = evidence_result if evidence_result is not None else validate_evidence_payload(
        build_evidence_template()
    )
    report = {
        **result,
        "report_type": "DGII_STAGING_EVIDENCE_LAB",
        "summary": summarize_evidence(result),
        "template_path": template_path,
        "report_path": report_path,
        "staging_evidence_lab_available": True,
        "staging_evidence_command": "dgii_staging_evidence_lab",
        "staging_evidence_status": "RUN",
    }
    return report
