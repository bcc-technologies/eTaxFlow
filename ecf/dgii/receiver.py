"""Internal DGII receiver contract helpers (design-only; no DB, no DGII calls)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
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
    return {
        "public_endpoints_enabled": endpoints_enabled,
        "receiver_processing_enabled": False,
        "supported_roots": ["ECF", "ARECF", "ACECF"],
        "signature_verification": "NOT_IMPLEMENTED",
        "signature_verification_implemented": signature_verification_implemented(),
        "persistence": "NOT_IMPLEMENTED",
        "compliance_status": "NOT_DGII_COMPLIANT",
        "dgii_submission_allowed": False,
        "track_id_creation": "DISABLED",
        "readiness_status": "BLOCKED",
        "design_only": True,
        "dgii_call_made": False,
        "track_id": None,
    }
