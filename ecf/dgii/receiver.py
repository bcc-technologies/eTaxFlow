"""Internal DGII receiver contract helpers (design-only; no DB, no DGII calls)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any

from lxml import etree

_DISABLED_MESSAGE = "Public DGII-facing endpoints are disabled in this environment."

KNOWN_ROOT_TAGS = frozenset({"ECF", "ARECF", "ACECF"})


class ReceiverDocumentType(StrEnum):
    ECF = "ECF"
    ARECF = "ARECF"
    ACECF = "ACECF"
    UNKNOWN = "UNKNOWN"


class ReceiverStatus(StrEnum):
    DISABLED = "DISABLED"
    DESIGN_ONLY = "DESIGN_ONLY"
    INVALID_XML = "INVALID_XML"
    UNSUPPORTED_ROOT = "UNSUPPORTED_ROOT"
    SIGNATURE_MISSING = "SIGNATURE_MISSING"
    SIGNATURE_VERIFICATION_NOT_IMPLEMENTED = "SIGNATURE_VERIFICATION_NOT_IMPLEMENTED"
    ACCEPTED_FOR_NON_PRODUCTION_REVIEW = "ACCEPTED_FOR_NON_PRODUCTION_REVIEW"


@dataclass(frozen=True)
class InboundClassification:
    document_type: ReceiverDocumentType
    root_tag: str
    status: ReceiverStatus
    errors: tuple[str, ...] = field(default_factory=tuple)
    signature_present: bool = False


def _safe_parser() -> etree.XMLParser:
    return etree.XMLParser(
        resolve_entities=False,
        no_network=True,
        huge_tree=False,
        dtd_validation=False,
        load_dtd=False,
    )


def _local_tag(tag: str) -> str:
    if "}" in tag:
        return tag.rsplit("}", 1)[-1]
    return tag


def _safe_fromstring(xml_bytes: bytes) -> etree._Element | None:
    if not xml_bytes or not xml_bytes.strip():
        return None
    try:
        return etree.fromstring(xml_bytes, parser=_safe_parser())
    except etree.XMLSyntaxError:
        return None


def identify_xml_root(xml_bytes: bytes) -> str:
    """Return local root tag name, or INVALID_XML when parsing fails."""
    element = _safe_fromstring(xml_bytes)
    if element is None:
        return ReceiverStatus.INVALID_XML
    return _local_tag(element.tag)


def detect_signature_presence(xml_bytes: bytes) -> bool:
    """Detect XMLDSig Signature element presence; does not verify."""
    element = _safe_fromstring(xml_bytes)
    if element is None:
        return False
    for node in element.iter():
        if _local_tag(node.tag) == "Signature":
            return True
    return False


def signature_verification_implemented() -> bool:
    """Production signature verification is intentionally not implemented."""
    return False


def classify_inbound_xml(xml_bytes: bytes) -> InboundClassification:
    """Classify inbound XML by root tag; safe parse only, no persistence."""
    root_tag = identify_xml_root(xml_bytes)
    if root_tag == ReceiverStatus.INVALID_XML:
        return InboundClassification(
            document_type=ReceiverDocumentType.UNKNOWN,
            root_tag="",
            status=ReceiverStatus.INVALID_XML,
            errors=("invalid_xml",),
        )

    if root_tag not in KNOWN_ROOT_TAGS:
        return InboundClassification(
            document_type=ReceiverDocumentType.UNKNOWN,
            root_tag=root_tag,
            status=ReceiverStatus.UNSUPPORTED_ROOT,
            errors=("unsupported_root",),
        )

    document_type = ReceiverDocumentType(root_tag)
    signature_present = detect_signature_presence(xml_bytes)
    if not signature_present:
        return InboundClassification(
            document_type=document_type,
            root_tag=root_tag,
            status=ReceiverStatus.SIGNATURE_MISSING,
            errors=("signature_missing",),
            signature_present=False,
        )

    if not signature_verification_implemented():
        return InboundClassification(
            document_type=document_type,
            root_tag=root_tag,
            status=ReceiverStatus.SIGNATURE_VERIFICATION_NOT_IMPLEMENTED,
            errors=("signature_verification_not_implemented",),
            signature_present=True,
        )

    return InboundClassification(
        document_type=document_type,
        root_tag=root_tag,
        status=ReceiverStatus.ACCEPTED_FOR_NON_PRODUCTION_REVIEW,
        signature_present=True,
    )


def build_disabled_receiver_response() -> dict[str, Any]:
    """Safe JSON payload for disabled public receiver routes."""
    return {
        "status": ReceiverStatus.DISABLED,
        "compliance_status": "NOT_DGII_COMPLIANT",
        "dgii_submission_allowed": False,
        "track_id": None,
        "message": _DISABLED_MESSAGE,
    }


def get_receiver_contract_metadata() -> dict[str, Any]:
    """Return read-only receiver support matrix (no network, no DB)."""
    from django.conf import settings

    endpoints_enabled = bool(getattr(settings, "ETAXFLOW_ENABLE_PUBLIC_DGII_ENDPOINTS", False))
    fixture_dir = Path("tests/fixtures/dgii/inbound_lab")
    return {
        "public_endpoints_enabled": endpoints_enabled,
        "receiver_processing_enabled": False,
        "supported_roots": ["ECF", "ARECF", "ACECF"],
        "signature_verification": "NOT_IMPLEMENTED",
        "signature_verification_implemented": signature_verification_implemented(),
        "persistence": "NOT_IMPLEMENTED",
        "schema_validation": "NOT_CLAIMED",
        "local_inbound_schema_lab_available": True,
        "local_inbound_signature_lab_available": True,
        "signature_verification_scope": "LOCAL_OFFLINE_TEST_ONLY",
        "signature_verification_command": "dgii_inbound_signature_lab",
        "production_signature_ready": False,
        "schema_validation_scope": "LOCAL_OFFLINE_ONLY",
        "schema_validation_command": "dgii_inbound_schema_lab",
        "schema_validation_certification_evidence": False,
        "supported_schema_roots": ["ECF", "ARECF", "ACECF"],
        "inbound_xml_lab_available": True,
        "non_production_inbound_persistence_lab_available": True,
        "persistence_scope": "NON_PRODUCTION_LAB_ONLY",
        "persistence_command": "dgii_inbound_persistence_lab",
        "production_persistence_ready": False,
        "public_route_persistence_enabled": False,
        "raw_xml_storage_default": "DISABLED",
        "non_production_inbound_workflow_lab_available": True,
        "workflow_scope": "NON_PRODUCTION_LAB_ONLY",
        "workflow_command": "dgii_inbound_workflow_lab",
        "production_workflow_ready": False,
        "public_route_workflow_enabled": False,
        "fiscal_acceptance_workflow_enabled": False,
        "non_production_inbound_audit_retention_lab_available": True,
        "audit_retention_scope": "NON_PRODUCTION_LAB_ONLY",
        "audit_retention_command": "dgii_inbound_audit_retention_lab",
        "production_audit_ready": False,
        "production_retention_ready": False,
        "public_route_audit_enabled": False,
        "destructive_retention_actions_enabled": False,
        "export_manifest_scope": "METADATA_ONLY",
        "inbound_security_policy_lab_available": True,
        "security_policy_scope": "NON_PRODUCTION_LAB_ONLY",
        "security_policy_command": "dgii_inbound_security_policy_lab",
        "security_policy_decision": "SECURITY_POLICY_BLOCKED",
        "production_security_ready": False,
        "public_endpoint_security_controls_enforced": False,
        "body_size_limit_enforced": False,
        "content_type_allowlist_enforced": False,
        "rate_limiting_enforced": False,
        "logging_redaction_approved": False,
        "trust_chain_validation_ready": False,
        "revocation_check_ready": False,
        "inbound_reporting_lab_available": True,
        "reporting_scope": "NON_PRODUCTION_LAB_ONLY",
        "reporting_command": "dgii_inbound_reporting_lab",
        "report_exports_metadata_only": True,
        "raw_xml_export_enabled": False,
        "production_dashboard_ready": False,
        "public_endpoint_reporting_enabled": False,
        "staging_evidence_lab_available": True,
        "staging_evidence_command": "dgii_staging_evidence_lab",
        "staging_evidence_scope": "NON_PRODUCTION_LAB_ONLY",
        "staging_evidence_decision": "STAGING_EVIDENCE_BLOCKED",
        "production_staging_ready": False,
        "public_endpoint_external_verification_ready": False,
        "dns_tls_evidence_ready": False,
        "manual_staging_review_required": True,
        "certification_package_lab_available": True,
        "certification_package_command": "dgii_certification_package_lab",
        "certification_package_scope": "DRAFT_ONLY",
        "certification_package_status": "PACKAGE_BLOCKED",
        "portal_submission_allowed": False,
        "portal_submission_ready": False,
        "package_requires_human_review": True,
        "lab_mode": "NON_PRODUCTION_ONLY",
        "synthetic_fixtures_available": fixture_dir.is_dir(),
        "certification_evidence": False,
        "compliance_status": "NOT_DGII_COMPLIANT",
        "dgii_submission_allowed": False,
        "track_id_creation": "DISABLED",
        "readiness_status": "BLOCKED",
        "design_only": True,
        "dgii_call_made": False,
        "track_id": None,
    }
