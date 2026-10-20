"""Inbound reporting export lab (Phase 035 — metadata-only, no DGII, no raw XML)."""

from __future__ import annotations

import csv
import io
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from django.conf import settings

LAB_MODE = "NON_PRODUCTION_LAB_ONLY"
REPORT_SCOPE = "NON_PRODUCTION_LAB_ONLY"
POLICY_VERSION = "phase-035-v1"
EXPORT_ROOT = Path("runtime/dgii_lab_reports")


def _count_breakdown(values: list[Any]) -> dict[str, int]:
    counter = Counter("" if v is None else str(v) for v in values)
    return dict(sorted(counter.items()))


def _safe_bool(value: Any, default: bool = False) -> bool:
    return bool(value) if value is not None else default


def collect_lab_report_data() -> dict[str, Any]:
    """Gather metadata-only inbound lab report inputs. No network, no raw XML."""
    from ecf.models import (
        InboundXMLLabAuditEvent,
        InboundXMLLabRecord,
        InboundXMLLabWorkflowEvent,
    )

    records = list(InboundXMLLabRecord.objects.order_by("created_at", "id"))
    workflow_events = list(
        InboundXMLLabWorkflowEvent.objects.order_by("created_at", "id")
    )
    audit_events = list(InboundXMLLabAuditEvent.objects.order_by("created_at", "id"))

    record_rows = [
        {
            "id": row.pk,
            "filename": row.filename,
            "raw_sha256": row.raw_sha256,
            "document_type": row.document_type,
            "root_tag": row.root_tag,
            "classification_status": row.classification_status,
            "local_xsd_valid": row.local_xsd_valid,
            "xsd_compiled": row.xsd_compiled,
            "signature_present": row.signature_present,
            "signature_verification_status": row.signature_verification_status,
            "persisted_raw_xml": row.persisted_raw_xml,
            "lab_mode": row.lab_mode,
            "compliance_status": row.compliance_status,
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }
        for row in records
    ]
    workflow_rows = [
        {
            "id": event.pk,
            "lab_record_id": event.lab_record_id,
            "route": event.route,
            "status": event.status,
            "reason": event.reason,
            "lab_mode": event.lab_mode,
            "created_at": event.created_at.isoformat() if event.created_at else None,
        }
        for event in workflow_events
    ]
    audit_rows = [
        {
            "id": event.pk,
            "lab_record_id": event.lab_record_id,
            "event_type": event.event_type,
            "retention_decision": event.retention_decision,
            "severity": event.severity,
            "reason": event.reason,
            "lab_mode": event.lab_mode,
            "created_at": event.created_at.isoformat() if event.created_at else None,
        }
        for event in audit_events
    ]

    security_summary: dict[str, Any] = {}
    try:
        from ecf.dgii.inbound_security_policy_lab import build_security_policy_report

        security_report = build_security_policy_report()
        security_summary = {
            "policy_decision": security_report.get("policy_decision"),
            "production_security_ready": security_report.get("production_security_ready"),
            "summary": security_report.get("summary"),
            "blocker_count": len(security_report.get("blockers") or []),
            "blockers": security_report.get("blockers") or [],
        }
    except Exception as exc:  # pragma: no cover - defensive
        security_summary = {"error": f"security_policy_unavailable:{exc}"}

    endpoint_plan: dict[str, Any] = {}
    try:
        from ecf.dgii.endpoints import get_software_registration_metadata

        endpoint_plan = get_software_registration_metadata()
    except Exception as exc:  # pragma: no cover
        endpoint_plan = {"error": f"endpoint_plan_unavailable:{exc}"}

    receiver_contract: dict[str, Any] = {}
    try:
        from ecf.dgii.receiver import get_receiver_contract_metadata

        receiver_contract = get_receiver_contract_metadata()
    except Exception as exc:  # pragma: no cover
        receiver_contract = {"error": f"receiver_contract_unavailable:{exc}"}

    readiness: dict[str, Any] = {}
    try:
        from ecf.management.commands.dgii_readiness_report import build_readiness_report

        readiness = build_readiness_report()
    except Exception as exc:  # pragma: no cover
        readiness = {"error": f"readiness_unavailable:{exc}"}

    return {
        "records": record_rows,
        "workflow_events": workflow_rows,
        "audit_events": audit_rows,
        "security_policy": security_summary,
        "endpoint_plan": endpoint_plan,
        "receiver_contract": receiver_contract,
        "readiness": readiness,
        "public_endpoints_enabled": bool(
            getattr(settings, "ETAXFLOW_ENABLE_PUBLIC_DGII_ENDPOINTS", False)
        ),
    }


def build_inbound_lab_summary(data: dict[str, Any] | None = None) -> dict[str, Any]:
    """JSON-serializable summary with required compliance boundary fields."""
    payload = data if data is not None else collect_lab_report_data()
    records = payload.get("records") or []
    workflows = payload.get("workflow_events") or []
    audits = payload.get("audit_events") or []
    readiness = payload.get("readiness") or {}
    security = payload.get("security_policy") or {}

    blockers = list(readiness.get("blockers") or [])
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "report_scope": REPORT_SCOPE,
        "policy_version": POLICY_VERSION,
        "lab_mode": LAB_MODE,
        "compliance_status": "NOT_DGII_COMPLIANT",
        "dgii_submission_allowed": False,
        "certification_evidence": False,
        "not_certification_evidence": True,
        "public_endpoints_enabled": _safe_bool(payload.get("public_endpoints_enabled")),
        "track_id": None,
        "dgii_call_made": False,
        "record_count": len(records),
        "workflow_event_count": len(workflows),
        "audit_event_count": len(audits),
        "document_type_breakdown": _count_breakdown(
            [item.get("document_type") for item in records]
        ),
        "schema_status_breakdown": _count_breakdown(
            [
                (
                    "valid"
                    if item.get("local_xsd_valid") is True
                    else "invalid"
                    if item.get("local_xsd_valid") is False
                    else "unknown"
                )
                for item in records
            ]
        ),
        "signature_status_breakdown": _count_breakdown(
            [item.get("signature_verification_status") for item in records]
        ),
        "workflow_route_breakdown": _count_breakdown(
            [item.get("route") for item in workflows]
        ),
        "retention_decision_breakdown": _count_breakdown(
            [item.get("retention_decision") for item in audits]
        ),
        "security_control_summary": security,
        "readiness_summary": {
            "overall_status": readiness.get("overall_status"),
            "compliance_status": readiness.get("compliance_status"),
            "dgii_submission_allowed": readiness.get("dgii_submission_allowed"),
            "production_signature_ready": readiness.get("production_signature_ready"),
            "production_security_ready": readiness.get("production_security_ready"),
            "blocker_count": len(blockers),
        },
        "blocker_count": len(blockers),
        "blockers": blockers,
        "files_exported": [],
        "includes_raw_xml": False,
        "export_scope": "METADATA_ONLY",
    }


def build_json_report(data: dict[str, Any] | None = None) -> dict[str, Any]:
    """Full JSON-serializable report (metadata only)."""
    payload = data if data is not None else collect_lab_report_data()
    summary = build_inbound_lab_summary(payload)
    return {
        **summary,
        "report_type": "DGII_INBOUND_REPORTING_LAB",
        "records": payload.get("records") or [],
        "workflow_events": payload.get("workflow_events") or [],
        "audit_events": payload.get("audit_events") or [],
        "endpoint_plan": payload.get("endpoint_plan") or {},
        "receiver_contract": payload.get("receiver_contract") or {},
        "readiness": {
            "overall_status": (payload.get("readiness") or {}).get("overall_status"),
            "compliance_status": (payload.get("readiness") or {}).get("compliance_status"),
            "dgii_submission_allowed": (payload.get("readiness") or {}).get(
                "dgii_submission_allowed"
            ),
            "production_signature_ready": (payload.get("readiness") or {}).get(
                "production_signature_ready"
            ),
            "production_security_ready": (payload.get("readiness") or {}).get(
                "production_security_ready"
            ),
            "blockers": (payload.get("readiness") or {}).get("blockers") or [],
            "not_certification_evidence": (payload.get("readiness") or {}).get(
                "not_certification_evidence", True
            ),
        },
        "reporting_lab_available": True,
        "reporting_command": "dgii_inbound_reporting_lab",
        "staging_evidence_lab_available": True,
        "staging_evidence_command": "dgii_staging_evidence_lab",
        "staging_evidence_status": "NOT_RUN_BY_DEFAULT",
        "certification_package_lab_available": True,
        "certification_package_command": "dgii_certification_package_lab",
        "certification_package_status": "NOT_RUN_BY_DEFAULT",
        "final_go_no_go_lab_available": True,
        "final_go_no_go_command": "dgii_final_go_no_go_lab",
        "final_go_no_go_status": "NOT_RUN_BY_DEFAULT",
        "final_inbound_audit_lab_available": True,
        "final_inbound_audit_command": "dgii_final_inbound_audit_lab",
        "final_inbound_audit_status": "NOT_RUN_BY_DEFAULT",
        "warnings": [
            "Metadata-only report. Raw XML is not exported.",
            "Not DGII certification evidence.",
            "Not a production dashboard.",
            "Public endpoints remain DISABLED.",
        ],
    }


def build_csv_summary(data: dict[str, Any] | None = None) -> str:
    """CSV metadata summary. Never includes raw_xml_text."""
    payload = data if data is not None else collect_lab_report_data()
    summary = build_inbound_lab_summary(payload)
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["section", "key", "value"])
    writer.writerow(["boundary", "compliance_status", summary["compliance_status"]])
    writer.writerow(
        ["boundary", "dgii_submission_allowed", summary["dgii_submission_allowed"]]
    )
    writer.writerow(
        ["boundary", "certification_evidence", summary["certification_evidence"]]
    )
    writer.writerow(
        ["boundary", "public_endpoints_enabled", summary["public_endpoints_enabled"]]
    )
    writer.writerow(["boundary", "track_id", ""])
    writer.writerow(["boundary", "dgii_call_made", summary["dgii_call_made"]])
    writer.writerow(["counts", "record_count", summary["record_count"]])
    writer.writerow(["counts", "workflow_event_count", summary["workflow_event_count"]])
    writer.writerow(["counts", "audit_event_count", summary["audit_event_count"]])
    writer.writerow(["counts", "blocker_count", summary["blocker_count"]])
    for section, mapping in (
        ("document_type", summary["document_type_breakdown"]),
        ("schema_status", summary["schema_status_breakdown"]),
        ("signature_status", summary["signature_status_breakdown"]),
        ("workflow_route", summary["workflow_route_breakdown"]),
        ("retention_decision", summary["retention_decision_breakdown"]),
    ):
        for key, value in mapping.items():
            writer.writerow([section, key, value])
    for blocker in summary["blockers"]:
        writer.writerow(["blocker", blocker, "true"])
    text = buffer.getvalue()
    if "raw_xml_text" in text:
        raise ValueError("CSV summary must not contain raw_xml_text")
    return text


def build_markdown_summary(data: dict[str, Any] | None = None) -> str:
    """Markdown metadata summary with explicit NOT_DGII_COMPLIANT warning."""
    payload = data if data is not None else collect_lab_report_data()
    summary = build_inbound_lab_summary(payload)
    lines = [
        "# Non-production inbound lab report",
        "",
        "**NOT_DGII_COMPLIANT**",
        "",
        f"- report_scope: `{summary['report_scope']}`",
        f"- lab_mode: `{summary['lab_mode']}`",
        f"- dgii_submission_allowed: `{summary['dgii_submission_allowed']}`",
        f"- certification_evidence: `{summary['certification_evidence']}`",
        f"- public_endpoints_enabled: `{summary['public_endpoints_enabled']}`",
        f"- track_id: `null`",
        f"- dgii_call_made: `{summary['dgii_call_made']}`",
        f"- includes_raw_xml: `{summary['includes_raw_xml']}`",
        "",
        "## Counts",
        "",
        f"- record_count: {summary['record_count']}",
        f"- workflow_event_count: {summary['workflow_event_count']}",
        f"- audit_event_count: {summary['audit_event_count']}",
        f"- blocker_count: {summary['blocker_count']}",
        "",
        "## Breakdowns",
        "",
        f"- document_type: `{summary['document_type_breakdown']}`",
        f"- schema_status: `{summary['schema_status_breakdown']}`",
        f"- signature_status: `{summary['signature_status_breakdown']}`",
        f"- workflow_route: `{summary['workflow_route_breakdown']}`",
        f"- retention_decision: `{summary['retention_decision_breakdown']}`",
        "",
        "## Readiness",
        "",
        f"- overall_status: `{summary['readiness_summary'].get('overall_status')}`",
        f"- production_security_ready: `{summary['readiness_summary'].get('production_security_ready')}`",
        "",
        "This report is **not** certification evidence and is **not** a production dashboard.",
        "",
    ]
    text = "\n".join(lines)
    if "raw_xml_text" in text:
        raise ValueError("Markdown summary must not contain raw_xml_text")
    return text


def resolve_output_dir(output_dir: str | Path | None = None) -> Path:
    """Resolve directory under runtime/dgii_lab_reports/; reject traversal."""
    root = EXPORT_ROOT.resolve()
    if output_dir is None:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        candidate = root / f"inbound_lab_report_{stamp}"
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
        raise ValueError("Report payload must not include raw_xml_text")


def write_report_bundle(
    output_dir: str | Path | None = None,
    data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Write JSON/CSV/Markdown/manifest under allowed export directory."""
    target = resolve_output_dir(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    payload = data if data is not None else collect_lab_report_data()
    report = build_json_report(payload)
    csv_text = build_csv_summary(payload)
    md_text = build_markdown_summary(payload)
    _assert_no_raw_xml(report)

    files = {
        "inbound_lab_report.json": json.dumps(
            report, indent=2, sort_keys=True, default=str
        )
        + "\n",
        "inbound_lab_summary.csv": csv_text
        if csv_text.endswith("\n")
        else csv_text + "\n",
        "inbound_lab_summary.md": md_text if md_text.endswith("\n") else md_text + "\n",
    }
    written: list[str] = []
    for name, content in files.items():
        path = target / name
        path.write_text(content, encoding="utf-8")
        written.append(str(path))

    manifest = {
        "generated_at": report["generated_at"],
        "report_scope": REPORT_SCOPE,
        "policy_version": POLICY_VERSION,
        "compliance_status": "NOT_DGII_COMPLIANT",
        "certification_evidence": False,
        "dgii_submission_allowed": False,
        "public_endpoints_enabled": report["public_endpoints_enabled"],
        "track_id": None,
        "dgii_call_made": False,
        "includes_raw_xml": False,
        "export_scope": "METADATA_ONLY",
        "files": [Path(p).name for p in written] + ["manifest.json"],
        "output_dir": str(target),
    }
    manifest_path = target / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    written.append(str(manifest_path))
    report["files_exported"] = written
    report["output_dir"] = str(target)
    report["reporting_status"] = "RUN"
    report["staging_evidence_lab_available"] = True
    report["staging_evidence_command"] = "dgii_staging_evidence_lab"
    report["staging_evidence_status"] = "NOT_RUN_BY_DEFAULT"
    report["certification_package_lab_available"] = True
    report["certification_package_command"] = "dgii_certification_package_lab"
    report["certification_package_status"] = "NOT_RUN_BY_DEFAULT"
    report["final_go_no_go_lab_available"] = True
    report["final_go_no_go_command"] = "dgii_final_go_no_go_lab"
    report["final_go_no_go_status"] = "NOT_RUN_BY_DEFAULT"
    report["final_inbound_audit_lab_available"] = True
    report["final_inbound_audit_command"] = "dgii_final_inbound_audit_lab"
    report["final_inbound_audit_status"] = "NOT_RUN_BY_DEFAULT"
    return report


def build_reporting_lab_report(
    *,
    data: dict[str, Any] | None = None,
    files_exported: list[str] | None = None,
    output_dir: str | None = None,
) -> dict[str, Any]:
    report = build_json_report(data)
    report["files_exported"] = files_exported or []
    report["output_dir"] = output_dir
    report["reporting_lab_available"] = True
    report["reporting_command"] = "dgii_inbound_reporting_lab"
    report["reporting_status"] = "RUN"
    report["staging_evidence_lab_available"] = True
    report["staging_evidence_command"] = "dgii_staging_evidence_lab"
    report["staging_evidence_status"] = "NOT_RUN_BY_DEFAULT"
    report["certification_package_lab_available"] = True
    report["certification_package_command"] = "dgii_certification_package_lab"
    report["certification_package_status"] = "NOT_RUN_BY_DEFAULT"
    report["final_go_no_go_lab_available"] = True
    report["final_go_no_go_command"] = "dgii_final_go_no_go_lab"
    report["final_go_no_go_status"] = "NOT_RUN_BY_DEFAULT"
    report["final_inbound_audit_lab_available"] = True
    report["final_inbound_audit_command"] = "dgii_final_inbound_audit_lab"
    report["final_inbound_audit_status"] = "NOT_RUN_BY_DEFAULT"
    return report
