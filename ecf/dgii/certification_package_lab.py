"""Certification portal submission package draft lab (Phase 037 — DRAFT_ONLY)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from django.conf import settings

PACKAGE_SCOPE = "DRAFT_ONLY"
LAB_MODE = "NON_PRODUCTION_LAB_ONLY"
POLICY_VERSION = "phase-037-v1"
EXPORT_ROOT = Path("runtime/dgii_certification_package_drafts")

PACKAGE_DRAFT_ONLY = "PACKAGE_DRAFT_ONLY"
PACKAGE_BLOCKED = "PACKAGE_BLOCKED"
PACKAGE_MANUAL_REVIEW_REQUIRED = "PACKAGE_MANUAL_REVIEW_REQUIRED"
PACKAGE_READY_FOR_HUMAN_REVIEW = "PACKAGE_READY_FOR_HUMAN_REVIEW"

RECEPCION_PATH = "/fe/recepcion/api/ecf"
APROBACION_PATH = "/fe/aprobacioncomercial/api/ecf"
AUTENTICACION_SEMILLA_PATH = "/fe/autenticacion/api/semilla"
AUTENTICACION_VALIDACION_PATH = "/fe/autenticacion/api/validacioncertificado"

HUMAN_DECISIONS_REQUIRED = (
    "Confirm Phase 024 DGII authorization gate sign-off.",
    "Confirm public base URL and external DNS/TLS verification evidence.",
    "Confirm disabled public endpoint external verification evidence.",
    "Complete security owner review of inbound controls and staging evidence.",
    "Complete tax/compliance owner review.",
    "Approve production signing architecture and key custody model.",
    "Confirm portal credentials custody (never store secrets in git).",
    "Explicit human decision to proceed toward portal postulation (still not automatic submission).",
)


def _normalize_base_url(base: str) -> str:
    return (base or "").strip().rstrip("/")


def _compose_url(base: str, path: str) -> str:
    base_norm = _normalize_base_url(base)
    if not base_norm:
        return ""
    path_norm = path if path.startswith("/") else f"/{path}"
    return f"{base_norm}{path_norm}"


def get_software_package_defaults() -> dict[str, Any]:
    """Return draft software postulation defaults. No network, no submission claim."""
    public_base_url = _normalize_base_url(
        getattr(settings, "ETAXFLOW_PUBLIC_BASE_URL", "")
    )
    software_type = getattr(settings, "ETAXFLOW_SOFTWARE_TYPE", "PROPIO")
    software_name = getattr(settings, "ETAXFLOW_SOFTWARE_NAME", "eTaxFlow")
    software_version = getattr(settings, "ETAXFLOW_SOFTWARE_VERSION", "0.1.0")
    endpoints_enabled = bool(
        getattr(settings, "ETAXFLOW_ENABLE_PUBLIC_DGII_ENDPOINTS", False)
    )
    planned = build_endpoint_url_draft(public_base_url)
    return {
        "software_type": software_type,
        "software_name": software_name,
        "software_version": software_version,
        "public_base_url": public_base_url,
        "public_base_url_configured": bool(public_base_url),
        "recepcion_path": RECEPCION_PATH,
        "aprobacion_comercial_path": APROBACION_PATH,
        "autenticacion_semilla_path": AUTENTICACION_SEMILLA_PATH,
        "autenticacion_validacion_path": AUTENTICACION_VALIDACION_PATH,
        "planned_urls": planned,
        "provider_mode": "NOT_APPLICABLE_FOR_SOFTWARE_PROPIO",
        "package_scope": PACKAGE_SCOPE,
        "package_status": PACKAGE_BLOCKED,
        "submission_allowed": False,
        "requires_human_review": True,
        "compliance_status": "NOT_DGII_COMPLIANT",
        "dgii_submission_allowed": False,
        "certification_evidence": False,
        "public_endpoints_enabled": endpoints_enabled,
        "production_staging_ready": False,
        "production_security_ready": False,
        "production_signature_ready": False,
        "track_id": None,
        "dgii_call_made": False,
        "portal_submission_allowed": False,
        "network_checks_performed": False,
        "signing_performed": False,
        "portal_upload_performed": False,
    }


def build_endpoint_url_draft(public_base_url: str | None = None) -> dict[str, Any]:
    """Build planned URLs only. Blank base is allowed; no network validation."""
    base = _normalize_base_url(public_base_url or "")
    return {
        "public_base_url": base,
        "public_base_url_configured": bool(base),
        "public_base_url_externally_verified": False,
        "recepcion_path": RECEPCION_PATH,
        "aprobacion_comercial_path": APROBACION_PATH,
        "autenticacion_semilla_path": AUTENTICACION_SEMILLA_PATH,
        "autenticacion_validacion_path": AUTENTICACION_VALIDACION_PATH,
        "recepcion_url": _compose_url(base, RECEPCION_PATH),
        "aprobacion_comercial_url": _compose_url(base, APROBACION_PATH),
        "autenticacion_semilla_url": _compose_url(base, AUTENTICACION_SEMILLA_PATH),
        "autenticacion_validacion_url": _compose_url(
            base, AUTENTICACION_VALIDACION_PATH
        ),
        "url_status": "BLOCKED" if not base else "DESIGN_ONLY",
        "notes": (
            "Planned paths only. Blank public_base_url yields empty absolute URLs. "
            "No live DNS/TLS/HTTPS checks."
        ),
    }


def collect_package_supporting_summaries() -> dict[str, Any]:
    """Safely collect supporting summaries from existing labs/plans."""
    summaries: dict[str, Any] = {}

    try:
        from ecf.dgii.endpoints import get_software_registration_metadata

        endpoint = get_software_registration_metadata()
        summaries["endpoint_plan"] = {
            "readiness_status": endpoint.get("readiness_status"),
            "url_status": endpoint.get("url_status"),
            "endpoints_enabled": endpoint.get("endpoints_enabled"),
            "deployment_readiness_status": endpoint.get("deployment_readiness_status"),
            "staging_evidence_decision": endpoint.get("staging_evidence_decision"),
            "production_staging_ready": endpoint.get("production_staging_ready"),
            "public_base_url_configured": endpoint.get("public_base_url_configured"),
            "compliance_status": endpoint.get("compliance_status"),
            "dgii_submission_allowed": endpoint.get("dgii_submission_allowed"),
        }
    except Exception as exc:  # pragma: no cover
        summaries["endpoint_plan"] = {"error": f"endpoint_plan_unavailable:{exc}"}

    try:
        from ecf.dgii.receiver import get_receiver_contract_metadata

        receiver = get_receiver_contract_metadata()
        summaries["receiver_contract"] = {
            "readiness_status": receiver.get("readiness_status"),
            "compliance_status": receiver.get("compliance_status"),
            "dgii_submission_allowed": receiver.get("dgii_submission_allowed"),
            "production_security_ready": receiver.get("production_security_ready"),
            "production_staging_ready": receiver.get("production_staging_ready"),
            "staging_evidence_decision": receiver.get("staging_evidence_decision"),
            "certification_evidence": receiver.get("certification_evidence"),
        }
    except Exception as exc:  # pragma: no cover
        summaries["receiver_contract"] = {
            "error": f"receiver_contract_unavailable:{exc}"
        }

    try:
        from ecf.dgii.staging_evidence_lab import (
            build_evidence_template,
            summarize_evidence,
            validate_evidence_payload,
        )

        staging = validate_evidence_payload(build_evidence_template())
        summaries["staging_evidence"] = summarize_evidence(staging)
    except Exception as exc:  # pragma: no cover
        summaries["staging_evidence"] = {"error": f"staging_evidence_unavailable:{exc}"}

    try:
        from ecf.dgii.inbound_security_policy_lab import build_security_policy_report

        security = build_security_policy_report()
        summaries["security_policy"] = {
            "policy_decision": security.get("policy_decision"),
            "production_security_ready": security.get("production_security_ready"),
            "summary": security.get("summary"),
            "blocker_count": len(security.get("blockers") or []),
            "compliance_status": security.get("compliance_status"),
        }
    except Exception as exc:  # pragma: no cover
        summaries["security_policy"] = {"error": f"security_policy_unavailable:{exc}"}

    try:
        from ecf.dgii.inbound_reporting_lab import build_inbound_lab_summary

        reporting = build_inbound_lab_summary()
        summaries["inbound_reporting"] = {
            "report_scope": reporting.get("report_scope"),
            "record_count": reporting.get("record_count"),
            "workflow_event_count": reporting.get("workflow_event_count"),
            "audit_event_count": reporting.get("audit_event_count"),
            "blocker_count": reporting.get("blocker_count"),
            "compliance_status": reporting.get("compliance_status"),
            "includes_raw_xml": reporting.get("includes_raw_xml"),
        }
    except Exception as exc:  # pragma: no cover
        summaries["inbound_reporting"] = {
            "error": f"inbound_reporting_unavailable:{exc}"
        }

    try:
        from ecf.management.commands.dgii_readiness_report import build_readiness_report

        readiness = build_readiness_report()
        summaries["readiness"] = {
            "overall_status": readiness.get("overall_status"),
            "compliance_status": readiness.get("compliance_status"),
            "dgii_submission_allowed": readiness.get("dgii_submission_allowed"),
            "production_signature_ready": readiness.get("production_signature_ready"),
            "production_security_ready": readiness.get("production_security_ready"),
            "production_staging_ready": readiness.get("production_staging_ready"),
            "blocker_count": len(readiness.get("blockers") or []),
            "blockers": readiness.get("blockers") or [],
            "not_certification_evidence": readiness.get(
                "not_certification_evidence", True
            ),
        }
    except Exception as exc:  # pragma: no cover
        summaries["readiness"] = {"error": f"readiness_unavailable:{exc}"}

    return summaries


def _default_package_blockers(summaries: dict[str, Any]) -> list[str]:
    readiness_blockers = list(
        ((summaries.get("readiness") or {}).get("blockers") or [])
    )
    package_blockers = [
        "certification_package_draft_only",
        "portal_submission_not_allowed",
        "portal_submission_ready_false",
        "public_base_url_not_verified",
        "endpoint_external_evidence_missing",
        "security_owner_review_missing",
        "tax_compliance_owner_review_missing",
        "phase_024_gate_not_signed_off",
        "production_signing_architecture_not_approved",
        "production_signature_verification_not_implemented",
        "certification_portal_credentials_not_confirmed",
        "certification_package_not_human_approved",
    ]
    seen: set[str] = set()
    ordered: list[str] = []
    for name in package_blockers + readiness_blockers:
        if name not in seen:
            seen.add(name)
            ordered.append(name)
    return ordered


def build_certification_package_draft(
    summaries: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """JSON-serializable draft package. Always PACKAGE_BLOCKED / DRAFT_ONLY."""
    defaults = get_software_package_defaults()
    supporting = summaries if summaries is not None else collect_package_supporting_summaries()
    blockers = _default_package_blockers(supporting)
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "policy_version": POLICY_VERSION,
        "lab_mode": LAB_MODE,
        "package_scope": PACKAGE_SCOPE,
        "package_status": PACKAGE_BLOCKED,
        "package_vocabulary_note": PACKAGE_DRAFT_ONLY,
        "submission_allowed": False,
        "portal_submission_allowed": False,
        "requires_human_review": True,
        "software_fields": {
            "software_type": defaults["software_type"],
            "software_name": defaults["software_name"],
            "software_version": defaults["software_version"],
            "provider_mode": defaults["provider_mode"],
            "public_base_url": defaults["public_base_url"],
            "public_base_url_configured": defaults["public_base_url_configured"],
        },
        "planned_urls": defaults["planned_urls"],
        "supporting_summaries": supporting,
        "blockers": blockers,
        "blocker_count": len(blockers),
        "human_decisions_required": list(HUMAN_DECISIONS_REQUIRED),
        "compliance_status": "NOT_DGII_COMPLIANT",
        "dgii_submission_allowed": False,
        "certification_evidence": False,
        "not_certification_evidence": True,
        "public_endpoints_enabled": defaults["public_endpoints_enabled"],
        "production_staging_ready": False,
        "production_security_ready": False,
        "production_signature_ready": False,
        "track_id": None,
        "dgii_call_made": False,
        "network_checks_performed": False,
        "signing_performed": False,
        "portal_upload_performed": False,
        "warnings": [
            "DRAFT_ONLY. This is not a portal submission.",
            "No signed XML was generated.",
            "No DGII call was made.",
            "Public endpoints remain DISABLED.",
            "Not certification evidence.",
        ],
        "certification_package_lab_available": True,
        "certification_package_command": "dgii_certification_package_lab",
        "final_go_no_go_lab_available": True,
        "final_go_no_go_command": "dgii_final_go_no_go_lab",
        "final_go_no_go_status": "NOT_RUN_BY_DEFAULT",
    }


def build_certification_package_markdown(
    package: dict[str, Any] | None = None,
) -> str:
    """Markdown package with explicit DRAFT_ONLY warning."""
    draft = package if package is not None else build_certification_package_draft()
    software = draft.get("software_fields") or {}
    urls = draft.get("planned_urls") or {}
    lines = [
        "# Certification portal submission package (DRAFT_ONLY)",
        "",
        "**DRAFT_ONLY** — **PACKAGE_BLOCKED** — **NOT_DGII_COMPLIANT**",
        "",
        "This package is **not** a portal submission, **not** a signed XML, and **not** certification evidence.",
        "",
        "## Software fields",
        "",
        f"- software_type: `{software.get('software_type')}`",
        f"- software_name: `{software.get('software_name')}`",
        f"- software_version: `{software.get('software_version')}`",
        f"- provider_mode: `{software.get('provider_mode')}`",
        f"- public_base_url: `{software.get('public_base_url') or '(blank)'}`",
        f"- public_base_url_configured: `{software.get('public_base_url_configured')}`",
        "",
        "## Planned URLs",
        "",
        f"- recepcion_path: `{urls.get('recepcion_path')}`",
        f"- aprobacion_comercial_path: `{urls.get('aprobacion_comercial_path')}`",
        f"- autenticacion_semilla_path: `{urls.get('autenticacion_semilla_path')}`",
        f"- autenticacion_validacion_path: `{urls.get('autenticacion_validacion_path')}`",
        f"- recepcion_url: `{urls.get('recepcion_url') or '(requires public_base_url)'}`",
        f"- aprobacion_comercial_url: `{urls.get('aprobacion_comercial_url') or '(requires public_base_url)'}`",
        f"- autenticacion_semilla_url: `{urls.get('autenticacion_semilla_url') or '(requires public_base_url)'}`",
        f"- autenticacion_validacion_url: `{urls.get('autenticacion_validacion_url') or '(requires public_base_url)'}`",
        "",
        "## Boundaries",
        "",
        f"- submission_allowed: `{draft.get('submission_allowed')}`",
        f"- dgii_submission_allowed: `{draft.get('dgii_submission_allowed')}`",
        f"- certification_evidence: `{draft.get('certification_evidence')}`",
        f"- public_endpoints_enabled: `{draft.get('public_endpoints_enabled')}`",
        f"- production_staging_ready: `{draft.get('production_staging_ready')}`",
        f"- production_security_ready: `{draft.get('production_security_ready')}`",
        f"- production_signature_ready: `{draft.get('production_signature_ready')}`",
        f"- track_id: `null`",
        f"- dgii_call_made: `{draft.get('dgii_call_made')}`",
        f"- blocker_count: `{draft.get('blocker_count')}`",
        "",
        "## Human decisions required",
        "",
    ]
    for item in draft.get("human_decisions_required") or []:
        lines.append(f"- {item}")
    lines.extend(["", "## Blockers (sample)", ""])
    for blocker in (draft.get("blockers") or [])[:20]:
        lines.append(f"- `{blocker}`")
    lines.extend(
        [
            "",
            "No portal upload. No signing. No DGII call. Public routes remain DISABLED.",
            "",
        ]
    )
    return "\n".join(lines)


def resolve_output_dir(output_dir: str | Path | None = None) -> Path:
    """Resolve directory under runtime/dgii_certification_package_drafts/; reject traversal."""
    root = EXPORT_ROOT.resolve()
    if output_dir is None:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        candidate = root / f"certification_package_{stamp}"
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


def write_certification_package(
    output_dir: str | Path | None = None,
    package: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Write JSON/Markdown/manifest under allowed export directory."""
    target = resolve_output_dir(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    draft = package if package is not None else build_certification_package_draft()
    md = build_certification_package_markdown(draft)
    files = {
        "certification_package_draft.json": json.dumps(
            draft, indent=2, sort_keys=True, default=str
        )
        + "\n",
        "certification_package_draft.md": md if md.endswith("\n") else md + "\n",
    }
    written: list[str] = []
    for name, content in files.items():
        path = target / name
        path.write_text(content, encoding="utf-8")
        written.append(str(path))

    manifest = {
        "generated_at": draft["generated_at"],
        "package_scope": PACKAGE_SCOPE,
        "package_status": PACKAGE_BLOCKED,
        "policy_version": POLICY_VERSION,
        "compliance_status": "NOT_DGII_COMPLIANT",
        "submission_allowed": False,
        "portal_submission_allowed": False,
        "certification_evidence": False,
        "dgii_submission_allowed": False,
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
    draft = {
        **draft,
        "files_exported": written,
        "output_dir": str(target),
        "certification_package_status": "RUN",
        "final_go_no_go_lab_available": True,
        "final_go_no_go_command": "dgii_final_go_no_go_lab",
        "final_go_no_go_status": "NOT_RUN_BY_DEFAULT",
    }
    return draft
