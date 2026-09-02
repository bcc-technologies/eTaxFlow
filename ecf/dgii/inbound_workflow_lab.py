"""Non-production inbound workflow routing lab (Phase 032 — lab events only, no DGII)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from django.db.models import QuerySet

from ecf.dgii.inbound_persistence_lab import (
    DEFAULT_FIXTURE_DIR,
    analyze_path_payloads,
    build_lab_record_payload,
    persist_path,
)
from ecf.models import InboundXMLLabRecord, InboundXMLLabWorkflowEvent

LAB_MODE = "NON_PRODUCTION_LAB_ONLY"
RULE_VERSION = "phase-032-v1"

LAB_ROUTE_ECF_REVIEW = "LAB_ROUTE_ECF_REVIEW"
LAB_ROUTE_ARECF_REVIEW = "LAB_ROUTE_ARECF_REVIEW"
LAB_ROUTE_ACECF_REVIEW = "LAB_ROUTE_ACECF_REVIEW"
LAB_ROUTE_INVALID_XML_REVIEW = "LAB_ROUTE_INVALID_XML_REVIEW"
LAB_ROUTE_UNSUPPORTED_ROOT_REVIEW = "LAB_ROUTE_UNSUPPORTED_ROOT_REVIEW"
LAB_ROUTE_SCHEMA_ISSUE_REVIEW = "LAB_ROUTE_SCHEMA_ISSUE_REVIEW"
LAB_ROUTE_SIGNATURE_ISSUE_REVIEW = "LAB_ROUTE_SIGNATURE_ISSUE_REVIEW"
LAB_ROUTE_DUPLICATE_REVIEW = "LAB_ROUTE_DUPLICATE_REVIEW"
LAB_ROUTE_MANUAL_REVIEW = "LAB_ROUTE_MANUAL_REVIEW"

LAB_ROUTED = "LAB_ROUTED"
LAB_ROUTING_DRY_RUN = "LAB_ROUTING_DRY_RUN"
LAB_ROUTING_SKIPPED = "LAB_ROUTING_SKIPPED"
LAB_ROUTING_ERROR = "LAB_ROUTING_ERROR"

_SIGNATURE_ISSUE_STATUSES = frozenset(
    {"MISSING", "PLACEHOLDER_ONLY", "VERIFICATION_NOT_IMPLEMENTED"}
)


def build_workflow_input_from_lab_record(record: InboundXMLLabRecord) -> dict[str, Any]:
    """Extract lab-only fields for routing. No production model access."""
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
        "signature_verified": record.signature_verified,
        "local_xsd_valid": record.local_xsd_valid,
        "xsd_compiled": record.xsd_compiled,
        "xsd_available": record.xsd_available,
        "xsd_error_count": record.xsd_error_count,
        "errors_json": record.errors_json,
        "lab_mode": record.lab_mode,
    }


def build_workflow_input_from_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Normalize a persistence lab payload dict for routing."""
    return {
        "record_id": payload.get("record_id"),
        "filename": payload.get("filename", ""),
        "source_path": payload.get("source_path", ""),
        "raw_sha256": payload.get("raw_sha256", ""),
        "raw_size_bytes": payload.get("raw_size_bytes", 0),
        "root_tag": payload.get("root_tag", ""),
        "document_type": payload.get("document_type", ""),
        "classification_status": payload.get("classification_status", ""),
        "signature_present": payload.get("signature_present", False),
        "signature_verification_status": payload.get("signature_verification_status", ""),
        "signature_verified": payload.get("signature_verified", False),
        "local_xsd_valid": payload.get("local_xsd_valid"),
        "xsd_compiled": payload.get("xsd_compiled", False),
        "xsd_available": payload.get("xsd_available", False),
        "xsd_error_count": payload.get("xsd_error_count", 0),
        "errors_json": payload.get("errors_json", []),
        "lab_mode": payload.get("lab_mode", LAB_MODE),
        "is_duplicate": payload.get("is_duplicate", False),
    }


def decide_lab_workflow_route(payload: dict[str, Any]) -> dict[str, Any]:
    """Pure routing decision from lab payload. No DB writes."""
    classification = (payload.get("classification_status") or "").upper()
    document_type = (payload.get("document_type") or "").upper()
    root_tag = (payload.get("root_tag") or "").upper()
    sig_status = (payload.get("signature_verification_status") or "").upper()
    is_duplicate = bool(payload.get("is_duplicate"))

    route = LAB_ROUTE_MANUAL_REVIEW
    reason = "default_manual_review"

    if classification == "INVALID_XML" or sig_status == "PARSE_ERROR":
        route = LAB_ROUTE_INVALID_XML_REVIEW
        reason = "invalid_xml_or_parse_error"
    elif classification == "UNSUPPORTED_ROOT" or (
        document_type == "UNKNOWN" and root_tag not in {"", "ECF", "ARECF", "ACECF"}
    ):
        route = LAB_ROUTE_UNSUPPORTED_ROOT_REVIEW
        reason = "unsupported_root"
    elif is_duplicate:
        route = LAB_ROUTE_DUPLICATE_REVIEW
        reason = "duplicate_raw_sha256"
    elif payload.get("local_xsd_valid") is False or not payload.get("xsd_compiled"):
        route = LAB_ROUTE_SCHEMA_ISSUE_REVIEW
        reason = "schema_compile_or_validation_issue"
    elif not payload.get("signature_present") or sig_status in _SIGNATURE_ISSUE_STATUSES:
        route = LAB_ROUTE_SIGNATURE_ISSUE_REVIEW
        reason = "signature_missing_or_not_verified"
    elif document_type == "ECF":
        route = LAB_ROUTE_ECF_REVIEW
        reason = "document_type_ecf"
    elif document_type == "ARECF":
        route = LAB_ROUTE_ARECF_REVIEW
        reason = "document_type_arecf"
    elif document_type == "ACECF":
        route = LAB_ROUTE_ACECF_REVIEW
        reason = "document_type_acecf"

    status = LAB_ROUTING_DRY_RUN
    return {
        "route": route,
        "status": status,
        "reason": reason,
        "rule_version": RULE_VERSION,
        "input_summary_json": {
            "record_id": payload.get("record_id"),
            "filename": payload.get("filename"),
            "raw_sha256": payload.get("raw_sha256"),
            "document_type": document_type,
            "classification_status": classification,
            "signature_verification_status": sig_status,
            "local_xsd_valid": payload.get("local_xsd_valid"),
            "xsd_compiled": payload.get("xsd_compiled"),
            "is_duplicate": is_duplicate,
        },
        "output_summary_json": {"route": route, "reason": reason},
        "compliance_status": "NOT_DGII_COMPLIANT",
        "dgii_submission_allowed": False,
        "certification_evidence": False,
        "track_id": None,
        "dgii_call_made": False,
        "lab_mode": LAB_MODE,
    }


def route_lab_record(
    record: InboundXMLLabRecord,
    *,
    apply: bool = False,
    is_duplicate: bool = False,
) -> dict[str, Any]:
    """Route one lab record. Creates workflow event only when apply=True."""
    payload = build_workflow_input_from_lab_record(record)
    payload["is_duplicate"] = is_duplicate
    decision = decide_lab_workflow_route(payload)
    decision["record_id"] = record.pk
    decision["raw_sha256"] = record.raw_sha256
    decision["filename"] = record.filename

    if not apply:
        decision["status"] = LAB_ROUTING_DRY_RUN
        decision["workflow_event_id"] = None
        decision["applied"] = False
        return decision

    try:
        event = InboundXMLLabWorkflowEvent.objects.create(
            lab_record=record,
            route=decision["route"],
            status=LAB_ROUTED,
            reason=decision["reason"],
            rule_version=decision["rule_version"],
            input_summary_json=decision["input_summary_json"],
            output_summary_json=decision["output_summary_json"],
            compliance_status="NOT_DGII_COMPLIANT",
            dgii_submission_allowed=False,
            certification_evidence=False,
            track_id=None,
            dgii_call_made=False,
            lab_mode=LAB_MODE,
        )
    except Exception as exc:  # pragma: no cover - defensive
        return {
            **decision,
            "status": LAB_ROUTING_ERROR,
            "reason": f"workflow_event_create_failed:{exc}",
            "workflow_event_id": None,
            "applied": False,
        }

    decision["status"] = LAB_ROUTED
    decision["workflow_event_id"] = event.pk
    decision["applied"] = True
    return decision


def route_lab_records(
    records: QuerySet[InboundXMLLabRecord] | list[InboundXMLLabRecord],
    *,
    apply: bool = False,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    """Route lab records in deterministic order."""
    if isinstance(records, QuerySet):
        ordered = records.order_by("created_at", "id")
        if limit is not None:
            ordered = ordered[:limit]
        record_list = list(ordered)
    else:
        record_list = sorted(records, key=lambda r: (r.created_at, r.pk))
        if limit is not None:
            record_list = record_list[:limit]

    results: list[dict[str, Any]] = []
    for record in record_list:
        is_duplicate = record.lab_workflow_events.exists()
        results.append(route_lab_record(record, apply=apply, is_duplicate=is_duplicate))
    return results


def route_path_via_persistence_lab(
    path: Path | str,
    *,
    apply: bool = False,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    """Route fixtures via lab analysis; persist records/events only when apply=True."""
    target = Path(path)
    if apply:
        persist_results = persist_path(target)
        results: list[dict[str, Any]] = []
        items = persist_results[:limit] if limit is not None else persist_results
        for item in items:
            record = InboundXMLLabRecord.objects.get(pk=item["record_id"])
            is_duplicate = bool(item.get("updated"))
            results.append(
                route_lab_record(record, apply=True, is_duplicate=is_duplicate)
            )
        return results

    payloads = analyze_path_payloads(target)
    if limit is not None:
        payloads = payloads[:limit]
    results = []
    for payload in payloads:
        routing_input = build_workflow_input_from_payload(payload)
        decision = decide_lab_workflow_route(routing_input)
        decision["filename"] = payload.get("filename")
        decision["raw_sha256"] = payload.get("raw_sha256")
        decision["workflow_event_id"] = None
        decision["applied"] = False
        results.append(decision)
    return results


def build_workflow_lab_report(
    results: list[dict[str, Any]],
    *,
    dry_run: bool,
    source: str,
) -> dict[str, Any]:
    route_counts: dict[str, int] = {}
    for item in results:
        route = item.get("route", "")
        route_counts[route] = route_counts.get(route, 0) + 1
    return {
        "lab_mode": LAB_MODE,
        "dry_run": dry_run,
        "apply_lab_workflow": not dry_run,
        "source": source,
        "rule_version": RULE_VERSION,
        "compliance_status": "NOT_DGII_COMPLIANT",
        "dgii_submission_allowed": False,
        "certification_evidence": False,
        "not_certification_evidence": True,
        "track_id": None,
        "dgii_call_made": False,
        "workflow_lab_available": True,
        "workflow_command": "dgii_inbound_workflow_lab",
        "default_fixture_dir": str(DEFAULT_FIXTURE_DIR),
        "result_count": len(results),
        "applied_count": sum(1 for item in results if item.get("applied")),
        "route_counts": route_counts,
        "audit_retention_lab_available": True,
        "audit_retention_command": "dgii_inbound_audit_retention_lab",
        "audit_retention_status": "NOT_RUN_BY_DEFAULT",
        "security_policy_lab_available": True,
        "security_policy_command": "dgii_inbound_security_policy_lab",
        "security_policy_status": "NOT_RUN_BY_DEFAULT",
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
        "final_inbound_audit_lab_available": True,
        "final_inbound_audit_command": "dgii_final_inbound_audit_lab",
        "final_inbound_audit_status": "NOT_RUN_BY_DEFAULT",
        "results": results,
    }
