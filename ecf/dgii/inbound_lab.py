"""Non-production inbound XML lab (Phase 028 — no DB, no DGII, no network)."""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from ecf.dgii.receiver import (
    ReceiverDocumentType,
    ReceiverStatus,
    classify_inbound_xml,
    detect_signature_presence,
    identify_xml_root,
)

DEFAULT_FIXTURE_DIR = Path("tests/fixtures/dgii/inbound_lab")
SYNTHETIC_SAMPLE_MARKER = "NON_OFFICIAL_SYNTHETIC_SAMPLE"


@dataclass(frozen=True)
class InboundLabResult:
    filename: str | None
    sha256: str
    root_tag: str
    document_type: str
    signature_present: bool
    status: str
    errors: tuple[str, ...] = field(default_factory=tuple)
    compliance_status: str = "NOT_DGII_COMPLIANT"
    dgii_submission_allowed: bool = False
    certification_evidence: bool = False
    track_id: None = None
    persisted: bool = False
    dgii_call_made: bool = False

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["errors"] = list(self.errors)
        return payload


def compute_sha256(xml_bytes: bytes) -> str:
    return hashlib.sha256(xml_bytes).hexdigest()


def analyze_inbound_xml(xml_bytes: bytes, filename: str | None = None) -> InboundLabResult:
    """Classify synthetic/lab inbound XML; no persistence, no DGII."""
    classification = classify_inbound_xml(xml_bytes)
    root_tag = identify_xml_root(xml_bytes)
    if root_tag == ReceiverStatus.INVALID_XML:
        root_tag = ""
    signature_present = detect_signature_presence(xml_bytes)
    return InboundLabResult(
        filename=filename,
        sha256=compute_sha256(xml_bytes),
        root_tag=root_tag or classification.root_tag,
        document_type=classification.document_type.value,
        signature_present=signature_present,
        status=classification.status.value,
        errors=classification.errors,
    )


def analyze_fixture_file(path: Path | str) -> InboundLabResult:
    fixture_path = Path(path)
    xml_bytes = fixture_path.read_bytes()
    return analyze_inbound_xml(xml_bytes, filename=fixture_path.name)


def analyze_fixture_directory(path: Path | str) -> list[InboundLabResult]:
    directory = Path(path)
    if not directory.is_dir():
        raise NotADirectoryError(f"Not a directory: {directory}")
    results: list[InboundLabResult] = []
    for fixture_path in sorted(directory.glob("*.xml")):
        results.append(analyze_fixture_file(fixture_path))
    return results


def build_lab_report(results: list[InboundLabResult]) -> dict[str, Any]:
    """Aggregate lab run metadata for command JSON output."""
    error_count = sum(1 for item in results if item.errors)
    return {
        "lab_mode": "NON_PRODUCTION_ONLY",
        "synthetic_sample_marker": SYNTHETIC_SAMPLE_MARKER,
        "compliance_status": "NOT_DGII_COMPLIANT",
        "dgii_submission_allowed": False,
        "certification_evidence": False,
        "not_certification_evidence": True,
        "dgii_call_made": False,
        "track_id": None,
        "persisted": False,
        "fixture_count": len(results),
        "error_count": error_count,
        "schema_validation_available": True,
        "schema_validation_command": "dgii_inbound_schema_lab",
        "schema_validation_status": "NOT_RUN_BY_DEFAULT",
        "signature_verification_available": True,
        "signature_verification_command": "dgii_inbound_signature_lab",
        "signature_verification_status": "NOT_RUN_BY_DEFAULT",
        "persistence_lab_available": True,
        "persistence_command": "dgii_inbound_persistence_lab",
        "persistence_status": "NOT_RUN_BY_DEFAULT",
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
        "results": [item.to_dict() for item in results],
    }
