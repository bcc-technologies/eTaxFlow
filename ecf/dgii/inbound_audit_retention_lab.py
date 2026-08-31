"""Non-production inbound audit/retention lab (Phase 033 — no deletes, no DGII)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from django.db.models import QuerySet
from django.utils import timezone as django_timezone

from ecf.models import InboundXMLLabAuditEvent, InboundXMLLabRecord, InboundXMLLabWorkflowEvent

LAB_MODE = "NON_PRODUCTION_LAB_ONLY"
POLICY_VERSION = "phase-033-v1"
DEFAULT_RETENTION_DAYS = 30
EXPORT_ROOT = Path("runtime/dgii_lab_exports")

LAB_AUDIT_RECORD_CREATED = "LAB_AUDIT_RECORD_CREATED"
LAB_AUDIT_RECORD_UPDATED = "LAB_AUDIT_RECORD_UPDATED"
LAB_AUDIT_WORKFLOW_ROUTED = "LAB_AUDIT_WORKFLOW_ROUTED"
LAB_AUDIT_DUPLICATE_DETECTED = "LAB_AUDIT_DUPLICATE_DETECTED"
LAB_AUDIT_RAW_XML_STORED = "LAB_AUDIT_RAW_XML_STORED"
LAB_AUDIT_RETENTION_REVIEWED = "LAB_AUDIT_RETENTION_REVIEWED"
LAB_AUDIT_EXPORT_MANIFEST_CREATED = "LAB_AUDIT_EXPORT_MANIFEST_CREATED"
LAB_AUDIT_PURGE_CANDIDATE_IDENTIFIED = "LAB_AUDIT_PURGE_CANDIDATE_IDENTIFIED"
LAB_AUDIT_MANUAL_REVIEW_REQUIRED = "LAB_AUDIT_MANUAL_REVIEW_REQUIRED"

LAB_RETENTION_KEEP = "LAB_RETENTION_KEEP"
LAB_RETENTION_REVIEW = "LAB_RETENTION_REVIEW"
LAB_RETENTION_PURGE_CANDIDATE = "LAB_RETENTION_PURGE_CANDIDATE"
LAB_RETENTION_RAW_XML_REVIEW = "LAB_RETENTION_RAW_XML_REVIEW"
LAB_RETENTION_EXPORT_READY = "LAB_RETENTION_EXPORT_READY"
LAB_RETENTION_ERROR = "LAB_RETENTION_ERROR"

SEVERITY_INFO = "INFO"
SEVERITY_WARN = "WARN"
SEVERITY_ERROR = "ERROR"


def build_audit_input_from_lab_record(record: InboundXMLLabRecord) -> dict[str, Any]:
    """Extract lab-only fields. No production model access."""
    workflow_qs = record.lab_workflow_events.order_by("-created_at", "-id")
    workflow_count = workflow_qs.count()
    latest = workflow_qs.first()
    return {
        "record_id": record.pk,
        "filename": record.filename,
        "source_path": record.source_path,
        "raw_sha256": record.raw_sha256,
        "raw_size_bytes": record.raw_size_bytes,
        "root_tag": record.root_tag,
        "document_type": record.document_type,
        "classification_status": record.classification_status,
        "signature_present": record.signature_present,
        "signature_verification_status": record.signature_verification_status,
        "local_xsd_valid": record.local_xsd_valid,
        "xsd_compiled": record.xsd_compiled,
        "persisted_raw_xml": record.persisted_raw_xml,
        "compliance_status": record.compliance_status,
        "dgii_submission_allowed": record.dgii_submission_allowed,
        "certification_evidence": record.certification_evidence,
        "track_id": record.track_id,
        "dgii_call_made": record.dgii_call_made,
        "lab_mode": record.lab_mode,
        "created_at": record.created_at.isoformat() if record.created_at else None,
        "updated_at": record.updated_at.isoformat() if record.updated_at else None,
        "workflow_event_count": workflow_count,
        "latest_workflow_route": latest.route if latest else None,
        "latest_workflow_event_id": latest.pk if latest else None,
    }


def decide_lab_retention(
    record_payload: dict[str, Any],
    retention_days: int = DEFAULT_RETENTION_DAYS,
    *,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Pure retention/audit decision. No DB writes. No deletes."""
    try:
        retention_days = max(0, int(retention_days))
    except (TypeError, ValueError):
        return {
            "retention_decision": LAB_RETENTION_ERROR,
            "event_type": LAB_AUDIT_MANUAL_REVIEW_REQUIRED,
            "severity": SEVERITY_ERROR,
            "reason": "invalid_retention_days",
            "policy_version": POLICY_VERSION,
            "compliance_status": "NOT_DGII_COMPLIANT",
            "dgii_submission_allowed": False,
            "certification_evidence": False,
            "track_id": None,
            "dgii_call_made": False,
            "lab_mode": LAB_MODE,
        }

    now = now or django_timezone.now()
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    track_id = record_payload.get("track_id")
    track_present = track_id is not None and str(track_id).strip() != ""

    if record_payload.get("certification_evidence") is True:
        event_type = LAB_AUDIT_MANUAL_REVIEW_REQUIRED
        decision = LAB_RETENTION_REVIEW
        severity = SEVERITY_ERROR
        reason = "policy_violation_certification_evidence"
    elif record_payload.get("dgii_submission_allowed") is True:
        event_type = LAB_AUDIT_MANUAL_REVIEW_REQUIRED
        decision = LAB_RETENTION_REVIEW
        severity = SEVERITY_ERROR
        reason = "policy_violation_dgii_submission_allowed"
    elif track_present:
        event_type = LAB_AUDIT_MANUAL_REVIEW_REQUIRED
        decision = LAB_RETENTION_REVIEW
        severity = SEVERITY_ERROR
        reason = "policy_violation_track_id_present"
    elif record_payload.get("dgii_call_made") is True:
        event_type = LAB_AUDIT_MANUAL_REVIEW_REQUIRED
        decision = LAB_RETENTION_REVIEW
        severity = SEVERITY_ERROR
        reason = "policy_violation_dgii_call_made"
    elif record_payload.get("persisted_raw_xml") is True:
        event_type = LAB_AUDIT_RAW_XML_STORED
        decision = LAB_RETENTION_RAW_XML_REVIEW
        severity = SEVERITY_WARN
        reason = "raw_xml_stored_review_required"
    else:
        age_days = 0
        created_raw = record_payload.get("created_at")
        created_dt = None
        if isinstance(created_raw, datetime):
            created_dt = created_raw
        elif isinstance(created_raw, str) and created_raw:
            try:
                created_dt = datetime.fromisoformat(created_raw.replace("Z", "+00:00"))
            except ValueError:
                created_dt = None
        if created_dt is not None:
            if created_dt.tzinfo is None:
                created_dt = created_dt.replace(tzinfo=timezone.utc)
            age_days = max(0, (now - created_dt).days)

        if age_days > retention_days:
            event_type = LAB_AUDIT_PURGE_CANDIDATE_IDENTIFIED
            decision = LAB_RETENTION_PURGE_CANDIDATE
            severity = SEVERITY_WARN
            reason = f"older_than_{retention_days}_days"
        else:
            event_type = LAB_AUDIT_RETENTION_REVIEWED
            decision = LAB_RETENTION_KEEP
            severity = SEVERITY_INFO
            reason = "recent_safe_lab_record"

    return {
        "retention_decision": decision,
        "event_type": event_type,
        "severity": severity,
        "reason": reason,
        "policy_version": POLICY_VERSION,
        "retention_days": retention_days,
        "input_summary_json": {
            "record_id": record_payload.get("record_id"),
            "filename": record_payload.get("filename"),
            "raw_sha256": record_payload.get("raw_sha256"),
            "persisted_raw_xml": record_payload.get("persisted_raw_xml"),
            "workflow_event_count": record_payload.get("workflow_event_count", 0),
            "latest_workflow_route": record_payload.get("latest_workflow_route"),
            "created_at": record_payload.get("created_at"),
        },
        "output_summary_json": {
            "retention_decision": decision,
            "event_type": event_type,
            "reason": reason,
        },
        "compliance_status": "NOT_DGII_COMPLIANT",
        "dgii_submission_allowed": False,
        "certification_evidence": False,
        "track_id": None,
        "dgii_call_made": False,
        "lab_mode": LAB_MODE,
    }


def audit_lab_record(
    record: InboundXMLLabRecord,
    *,
    apply: bool = False,
    retention_days: int = DEFAULT_RETENTION_DAYS,
) -> dict[str, Any]:
    """Audit one lab record. Creates InboundXMLLabAuditEvent only when apply=True."""
    payload = build_audit_input_from_lab_record(record)
    decision = decide_lab_retention(payload, retention_days=retention_days)
    decision["record_id"] = record.pk
    decision["raw_sha256"] = record.raw_sha256
    decision["filename"] = record.filename
    decision["workflow_event_id"] = payload.get("latest_workflow_event_id")

    if not apply:
        decision["applied"] = False
        decision["audit_event_id"] = None
        decision["dry_run"] = True
        return decision

    workflow_event = None
    wf_id = payload.get("latest_workflow_event_id")
    if wf_id:
        workflow_event = InboundXMLLabWorkflowEvent.objects.filter(pk=wf_id).first()

    event = InboundXMLLabAuditEvent.objects.create(
        lab_record=record,
        workflow_event=workflow_event,
        event_type=decision["event_type"],
        retention_decision=decision["retention_decision"],
        severity=decision["severity"],
        reason=decision["reason"],
        policy_version=decision["policy_version"],
        input_summary_json=decision["input_summary_json"],
        output_summary_json=decision["output_summary_json"],
        compliance_status="NOT_DGII_COMPLIANT",
        dgii_submission_allowed=False,
        certification_evidence=False,
        track_id=None,
        dgii_call_made=False,
        lab_mode=LAB_MODE,
    )
    decision["applied"] = True
    decision["audit_event_id"] = event.pk
    decision["dry_run"] = False
    return decision


def audit_lab_records(
    records: QuerySet[InboundXMLLabRecord] | list[InboundXMLLabRecord],
    *,
    apply: bool = False,
    retention_days: int = DEFAULT_RETENTION_DAYS,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    if isinstance(records, QuerySet):
        ordered = records.order_by("created_at", "id")
        if limit is not None:
            ordered = ordered[:limit]
        record_list = list(ordered)
    else:
        record_list = sorted(records, key=lambda r: (r.created_at, r.pk))
        if limit is not None:
            record_list = record_list[:limit]
    return [
        audit_lab_record(record, apply=apply, retention_days=retention_days)
        for record in record_list
    ]


def build_export_manifest(
    records: QuerySet[InboundXMLLabRecord] | list[InboundXMLLabRecord],
    *,
    include_workflow_events: bool = True,
    include_audit_events: bool = True,
) -> dict[str, Any]:
    if isinstance(records, QuerySet):
        record_list = list(records.order_by("created_at", "id"))
    else:
        record_list = sorted(records, key=lambda r: (r.created_at, r.pk))

    summaries: list[dict[str, Any]] = []
    workflow_count = 0
    audit_count = 0
    for record in record_list:
        wf_count = record.lab_workflow_events.count()
        au_count = record.lab_audit_events.count()
        workflow_count += wf_count
        audit_count += au_count
        item: dict[str, Any] = {
            "record_id": record.pk,
            "filename": record.filename,
            "raw_sha256": record.raw_sha256,
            "raw_size_bytes": record.raw_size_bytes,
            "document_type": record.document_type,
            "root_tag": record.root_tag,
            "classification_status": record.classification_status,
            "persisted_raw_xml": record.persisted_raw_xml,
            "lab_mode": record.lab_mode,
            "compliance_status": record.compliance_status,
            "created_at": record.created_at.isoformat() if record.created_at else None,
        }
        if include_workflow_events:
            item["workflow_event_count"] = wf_count
            latest = record.lab_workflow_events.order_by("-created_at", "-id").first()
            item["latest_workflow_route"] = latest.route if latest else None
        if include_audit_events:
            item["audit_event_count"] = au_count
        # Never include raw_xml_text
        summaries.append(item)

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "policy_version": POLICY_VERSION,
        "record_count": len(summaries),
        "workflow_event_count": workflow_count if include_workflow_events else 0,
        "audit_event_count": audit_count if include_audit_events else 0,
        "records": summaries,
        "compliance_status": "NOT_DGII_COMPLIANT",
        "certification_evidence": False,
        "dgii_submission_allowed": False,
        "track_id": None,
        "dgii_call_made": False,
        "lab_mode": LAB_MODE,
        "export_scope": "METADATA_ONLY",
        "includes_raw_xml": False,
    }


def resolve_export_path(export_path: str | Path | None = None) -> Path:
    """Resolve path under runtime/dgii_lab_exports/; reject traversal."""
    root = EXPORT_ROOT.resolve()
    if export_path is None:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        candidate = root / f"inbound_lab_export_{stamp}.json"
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


def write_export_manifest(path: Path | str | None, manifest: dict[str, Any]) -> Path:
    """Write metadata-only JSON under allowed export directory."""
    target = resolve_export_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    # Defense: never write raw XML keys if somehow present
    safe = dict(manifest)
    safe.pop("raw_xml_text", None)
    for item in safe.get("records", []) or []:
        if isinstance(item, dict):
            item.pop("raw_xml_text", None)
    with target.open("w", encoding="utf-8") as handle:
        json.dump(safe, handle, indent=2, sort_keys=True, default=str)
        handle.write("\n")
    return target


def build_audit_retention_lab_report(
    results: list[dict[str, Any]],
    *,
    dry_run: bool,
    retention_days: int,
    export_path: str | None = None,
) -> dict[str, Any]:
    decision_counts: dict[str, int] = {}
    for item in results:
        key = item.get("retention_decision", "")
        decision_counts[key] = decision_counts.get(key, 0) + 1
    return {
        "lab_mode": LAB_MODE,
        "dry_run": dry_run,
        "apply_lab_audit": not dry_run,
        "retention_days": retention_days,
        "policy_version": POLICY_VERSION,
        "compliance_status": "NOT_DGII_COMPLIANT",
        "dgii_submission_allowed": False,
        "certification_evidence": False,
        "not_certification_evidence": True,
        "track_id": None,
        "dgii_call_made": False,
        "destructive_retention_actions_enabled": False,
        "export_manifest_scope": "METADATA_ONLY",
        "export_path": export_path,
        "result_count": len(results),
        "applied_count": sum(1 for item in results if item.get("applied")),
        "retention_decision_counts": decision_counts,
        "security_policy_lab_available": True,
        "security_policy_command": "dgii_inbound_security_policy_lab",
        "security_policy_status": "NOT_RUN_BY_DEFAULT",
        "reporting_lab_available": True,
        "reporting_command": "dgii_inbound_reporting_lab",
        "reporting_status": "NOT_RUN_BY_DEFAULT",
        "results": results,
    }
