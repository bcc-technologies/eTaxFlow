"""Non-production inbound persistence lab (Phase 031 — lab table only, no DGII)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ecf.dgii.inbound_lab import DEFAULT_FIXTURE_DIR, analyze_inbound_xml, compute_sha256
from ecf.dgii.inbound_schema_lab import analyze_inbound_xml_with_local_xsd
from ecf.dgii.inbound_signature_lab import analyze_inbound_xml_with_signature_lab
from ecf.models import InboundXMLLabRecord

LAB_MODE = "NON_PRODUCTION_LAB_ONLY"


def _as_error_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value else []
    return [str(item) for item in value]


def _decode_lab_xml(xml_bytes: bytes) -> str:
    return xml_bytes.decode("utf-8", errors="replace")


def build_lab_record_payload(
    xml_bytes: bytes,
    filename: str | None = None,
    source_path: str | None = None,
) -> dict[str, Any]:
    """Assemble a lab-only persistence payload. Does not write the database."""
    classification = analyze_inbound_xml(xml_bytes, filename=filename)
    schema = analyze_inbound_xml_with_local_xsd(xml_bytes, filename=filename)
    signature = analyze_inbound_xml_with_signature_lab(xml_bytes, filename=filename)
    errors = (
        _as_error_list(classification.errors)
        + _as_error_list(schema.xsd_errors)
        + _as_error_list(signature.signature_errors)
    )
    return {
        "source_path": source_path or "",
        "filename": filename or "",
        "raw_sha256": compute_sha256(xml_bytes),
        "raw_size_bytes": len(xml_bytes),
        "root_tag": classification.root_tag or "",
        "document_type": classification.document_type,
        "classification_status": classification.status,
        "signature_present": signature.signature_present,
        "signature_verification_status": signature.signature_verification_status,
        "signature_verified": False,
        "production_signature_ready": False,
        "schema_validation_scope": schema.schema_validation_scope,
        "xsd_path": schema.xsd_path or "",
        "xsd_available": schema.xsd_available,
        "xsd_compiled": schema.xsd_compiled,
        "local_xsd_valid": schema.local_xsd_valid,
        "xsd_error_count": schema.xsd_error_count,
        "errors_json": errors,
        "compliance_status": "NOT_DGII_COMPLIANT",
        "dgii_submission_allowed": False,
        "certification_evidence": False,
        "track_id": None,
        "dgii_call_made": False,
        "lab_mode": LAB_MODE,
    }


def persist_lab_record(
    xml_bytes: bytes,
    filename: str | None = None,
    source_path: str | None = None,
    store_raw_xml: bool = False,
    allow_duplicates: bool = False,
) -> dict[str, Any]:
    """Write one InboundXMLLabRecord. Never Invoice/Document/ECFDocument. No TrackId."""
    payload = build_lab_record_payload(
        xml_bytes,
        filename=filename,
        source_path=source_path,
    )
    defaults = {
        **payload,
        "persisted_raw_xml": bool(store_raw_xml),
        "raw_xml_text": _decode_lab_xml(xml_bytes) if store_raw_xml else "",
        "compliance_status": "NOT_DGII_COMPLIANT",
        "dgii_submission_allowed": False,
        "certification_evidence": False,
        "track_id": None,
        "dgii_call_made": False,
        "lab_mode": LAB_MODE,
        "production_signature_ready": False,
        "signature_verified": False,
    }
    sha = defaults.pop("raw_sha256")
    # Unique raw_sha256: --allow-duplicates still upserts (no true duplicate rows).
    _ = allow_duplicates
    record, created = InboundXMLLabRecord.objects.update_or_create(
        raw_sha256=sha,
        defaults=defaults,
    )
    updated = not created
    return {
        "created": created,
        "updated": updated,
        "record_id": record.pk,
        "raw_sha256": record.raw_sha256,
        "filename": record.filename,
        "document_type": record.document_type,
        "persisted_raw_xml": record.persisted_raw_xml,
        "compliance_status": record.compliance_status,
        "certification_evidence": record.certification_evidence,
        "dgii_submission_allowed": record.dgii_submission_allowed,
        "track_id": record.track_id,
        "dgii_call_made": record.dgii_call_made,
        "lab_mode": record.lab_mode,
    }


def persist_path(
    path: Path | str,
    store_raw_xml: bool = False,
    allow_duplicates: bool = False,
) -> list[dict[str, Any]]:
    target = Path(path)
    if target.is_file():
        return [
            persist_lab_record(
                target.read_bytes(),
                filename=target.name,
                source_path=str(target),
                store_raw_xml=store_raw_xml,
                allow_duplicates=allow_duplicates,
            )
        ]
    if target.is_dir():
        results: list[dict[str, Any]] = []
        for fixture_path in sorted(target.glob("*.xml")):
            results.append(
                persist_lab_record(
                    fixture_path.read_bytes(),
                    filename=fixture_path.name,
                    source_path=str(fixture_path),
                    store_raw_xml=store_raw_xml,
                    allow_duplicates=allow_duplicates,
                )
            )
        return results
    raise FileNotFoundError(f"Path is neither file nor directory: {target}")


def analyze_path_payloads(path: Path | str) -> list[dict[str, Any]]:
    """Dry-run payloads; no database writes."""
    target = Path(path)
    if target.is_file():
        return [
            build_lab_record_payload(
                target.read_bytes(),
                filename=target.name,
                source_path=str(target),
            )
        ]
    if target.is_dir():
        results: list[dict[str, Any]] = []
        for fixture_path in sorted(target.glob("*.xml")):
            results.append(
                build_lab_record_payload(
                    fixture_path.read_bytes(),
                    filename=fixture_path.name,
                    source_path=str(fixture_path),
                )
            )
        return results
    raise FileNotFoundError(f"Path is neither file nor directory: {target}")


def build_persistence_lab_report(
    results: list[dict[str, Any]],
    *,
    dry_run: bool,
    store_raw_xml: bool,
) -> dict[str, Any]:
    return {
        "lab_mode": LAB_MODE,
        "dry_run": dry_run,
        "persist_lab_records": not dry_run,
        "store_raw_lab_xml": store_raw_xml,
        "compliance_status": "NOT_DGII_COMPLIANT",
        "dgii_submission_allowed": False,
        "certification_evidence": False,
        "not_certification_evidence": True,
        "track_id": None,
        "dgii_call_made": False,
        "default_fixture_dir": str(DEFAULT_FIXTURE_DIR),
        "result_count": len(results),
        "created_count": sum(1 for item in results if item.get("created")),
        "updated_count": sum(1 for item in results if item.get("updated")),
        "workflow_lab_available": True,
        "workflow_command": "dgii_inbound_workflow_lab",
        "workflow_status": "NOT_RUN_BY_DEFAULT",
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
        "results": results,
    }
