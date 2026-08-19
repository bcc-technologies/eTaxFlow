"""Local/offline inbound XMLDSig inspection lab (Phase 030 — no DB, no DGII, no network)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any

from lxml import etree

from ecf.dgii.inbound_lab import DEFAULT_FIXTURE_DIR, InboundLabResult, analyze_inbound_xml
from ecf.dgii.receiver import ReceiverStatus

XMLDSIG_NS = "http://www.w3.org/2000/09/xmldsig#"
VERIFICATION_SCOPE = "LOCAL_OFFLINE_TEST_ONLY"


class SignatureLabStatus(StrEnum):
    MISSING = "MISSING"
    PLACEHOLDER_ONLY = "PLACEHOLDER_ONLY"
    UNSUPPORTED_SIGNATURE_FORMAT = "UNSUPPORTED_SIGNATURE_FORMAT"
    VERIFICATION_NOT_IMPLEMENTED = "VERIFICATION_NOT_IMPLEMENTED"
    TEST_ONLY_VALID = "TEST_ONLY_VALID"
    TEST_ONLY_INVALID = "TEST_ONLY_INVALID"
    PARSE_ERROR = "PARSE_ERROR"


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


def _namespace(tag: str) -> str:
    if tag.startswith("{") and "}" in tag:
        return tag[1:].split("}", 1)[0]
    return ""


def _safe_fromstring(xml_bytes: bytes) -> etree._Element | None:
    if not xml_bytes or not xml_bytes.strip():
        return None
    try:
        return etree.fromstring(xml_bytes, parser=_safe_parser())
    except etree.XMLSyntaxError:
        return None


def _find_signature_element(root: etree._Element) -> etree._Element | None:
    for node in root.iter():
        if _local_tag(node.tag) == "Signature":
            return node
    return None


def _child_text(element: etree._Element, local_name: str) -> str:
    for node in element.iter():
        if _local_tag(node.tag) == local_name and node.text and node.text.strip():
            return node.text.strip()
    return ""


def _attr_algorithm(element: etree._Element, local_name: str) -> str | None:
    for node in element.iter():
        if _local_tag(node.tag) == local_name:
            value = node.get("Algorithm") or node.get("algorithm")
            if value:
                return value
    return None


@dataclass(frozen=True)
class SignatureMetadata:
    signature_present: bool
    signature_namespace: str | None
    signature_algorithm: str | None
    digest_algorithm: str | None
    certificate_present: bool
    certificate_subject_summary: str | None
    has_signature_value: bool
    has_digest_value: bool
    errors: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["errors"] = list(self.errors)
        return payload


@dataclass(frozen=True)
class SignatureVerifyResult:
    status: SignatureLabStatus
    signature_verified: bool
    errors: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class InboundSignatureLabResult:
    filename: str | None
    sha256: str
    root_tag: str
    document_type: str
    signature_present: bool
    signature_namespace: str | None
    signature_algorithm: str | None
    digest_algorithm: str | None
    certificate_present: bool
    certificate_subject_summary: str | None
    signature_verification_status: str
    signature_verified: bool
    signature_errors: tuple[str, ...]
    verification_scope: str = VERIFICATION_SCOPE
    production_signature_ready: bool = False
    compliance_status: str = "NOT_DGII_COMPLIANT"
    dgii_submission_allowed: bool = False
    certification_evidence: bool = False
    track_id: None = None
    persisted: bool = False
    dgii_call_made: bool = False
    status: str = ""
    errors: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["signature_errors"] = list(self.signature_errors)
        payload["errors"] = list(self.errors)
        return payload


def inspect_signature_metadata(xml_bytes: bytes) -> SignatureMetadata:
    """Inspect XMLDSig Signature nodes. No network, no verification."""
    root = _safe_fromstring(xml_bytes)
    if root is None:
        return SignatureMetadata(
            signature_present=False,
            signature_namespace=None,
            signature_algorithm=None,
            digest_algorithm=None,
            certificate_present=False,
            certificate_subject_summary=None,
            has_signature_value=False,
            has_digest_value=False,
            errors=("invalid_xml",),
        )
    signature = _find_signature_element(root)
    if signature is None:
        return SignatureMetadata(
            signature_present=False,
            signature_namespace=None,
            signature_algorithm=None,
            digest_algorithm=None,
            certificate_present=False,
            certificate_subject_summary=None,
            has_signature_value=False,
            has_digest_value=False,
        )
    cert_text = _child_text(signature, "X509Certificate")
    return SignatureMetadata(
        signature_present=True,
        signature_namespace=_namespace(signature.tag) or None,
        signature_algorithm=_attr_algorithm(signature, "SignatureMethod"),
        digest_algorithm=_attr_algorithm(signature, "DigestMethod"),
        certificate_present=bool(cert_text),
        certificate_subject_summary=None,
        has_signature_value=bool(_child_text(signature, "SignatureValue")),
        has_digest_value=bool(_child_text(signature, "DigestValue")),
    )


def classify_signature_status(xml_bytes: bytes) -> SignatureLabStatus:
    """Classify synthetic Signature nodes. Placeholders are never valid."""
    meta = inspect_signature_metadata(xml_bytes)
    if meta.errors and "invalid_xml" in meta.errors:
        return SignatureLabStatus.PARSE_ERROR
    if not meta.signature_present:
        return SignatureLabStatus.MISSING
    ns = meta.signature_namespace or ""
    if ns and ns != XMLDSIG_NS:
        return SignatureLabStatus.UNSUPPORTED_SIGNATURE_FORMAT
    if not meta.has_signature_value or not meta.has_digest_value:
        return SignatureLabStatus.PLACEHOLDER_ONLY
    return SignatureLabStatus.VERIFICATION_NOT_IMPLEMENTED


def verify_signature_local_test_only(
    xml_bytes: bytes,
    trusted_test_certificate: bytes | None = None,
) -> SignatureVerifyResult:
    """Offline test-only verification. No production trust store, no network.

    Cryptographic XMLDSig verification is NOT_IMPLEMENTED in this phase: there is
    no safe existing verifier and signxml is not a project dependency.
    """
    del trusted_test_certificate  # unused; no verifier to consume a test cert
    status = classify_signature_status(xml_bytes)
    if status == SignatureLabStatus.PARSE_ERROR:
        return SignatureVerifyResult(status=status, signature_verified=False, errors=("invalid_xml",))
    if status == SignatureLabStatus.MISSING:
        return SignatureVerifyResult(status=status, signature_verified=False, errors=("signature_missing",))
    if status == SignatureLabStatus.PLACEHOLDER_ONLY:
        return SignatureVerifyResult(
            status=status,
            signature_verified=False,
            errors=("placeholder_signature",),
        )
    if status == SignatureLabStatus.UNSUPPORTED_SIGNATURE_FORMAT:
        return SignatureVerifyResult(
            status=status,
            signature_verified=False,
            errors=("unsupported_signature_format",),
        )
    return SignatureVerifyResult(
        status=SignatureLabStatus.VERIFICATION_NOT_IMPLEMENTED,
        signature_verified=False,
        errors=("xmldsig_verification_not_implemented",),
    )


def analyze_inbound_xml_with_signature_lab(
    xml_bytes: bytes,
    filename: str | None = None,
) -> InboundSignatureLabResult:
    """Classify inbound XML and add local/offline signature inspection fields."""
    lab: InboundLabResult = analyze_inbound_xml(xml_bytes, filename=filename)
    meta = inspect_signature_metadata(xml_bytes)
    verify = verify_signature_local_test_only(xml_bytes)
    status = verify.status
    if lab.status == ReceiverStatus.INVALID_XML:
        status = SignatureLabStatus.PARSE_ERROR
    return InboundSignatureLabResult(
        filename=lab.filename,
        sha256=lab.sha256,
        root_tag=lab.root_tag,
        document_type=lab.document_type,
        signature_present=meta.signature_present,
        signature_namespace=meta.signature_namespace,
        signature_algorithm=meta.signature_algorithm,
        digest_algorithm=meta.digest_algorithm,
        certificate_present=meta.certificate_present,
        certificate_subject_summary=meta.certificate_subject_summary,
        signature_verification_status=status.value,
        signature_verified=False,
        signature_errors=verify.errors or meta.errors,
        status=lab.status,
        errors=lab.errors,
    )


def analyze_path_with_signature_lab(path: Path | str) -> list[InboundSignatureLabResult]:
    target = Path(path)
    if target.is_file():
        return [
            analyze_inbound_xml_with_signature_lab(
                target.read_bytes(),
                filename=target.name,
            )
        ]
    if target.is_dir():
        results: list[InboundSignatureLabResult] = []
        for fixture_path in sorted(target.glob("*.xml")):
            results.append(
                analyze_inbound_xml_with_signature_lab(
                    fixture_path.read_bytes(),
                    filename=fixture_path.name,
                )
            )
        return results
    raise FileNotFoundError(f"Path is neither file nor directory: {target}")


def build_signature_lab_report(results: list[InboundSignatureLabResult]) -> dict[str, Any]:
    invalid_count = sum(
        1
        for item in results
        if item.signature_verification_status
        in {SignatureLabStatus.TEST_ONLY_INVALID, SignatureLabStatus.PARSE_ERROR}
    )
    return {
        "lab_mode": "NON_PRODUCTION_ONLY",
        "verification_scope": VERIFICATION_SCOPE,
        "synthetic_sample_marker": "NON_OFFICIAL_SYNTHETIC_SAMPLE",
        "compliance_status": "NOT_DGII_COMPLIANT",
        "dgii_submission_allowed": False,
        "certification_evidence": False,
        "not_certification_evidence": True,
        "production_signature_ready": False,
        "dgii_call_made": False,
        "track_id": None,
        "persisted": False,
        "cryptographic_xmldsig_verification": "NOT_IMPLEMENTED",
        "fixture_count": len(results),
        "invalid_signature_count": invalid_count,
        "default_fixture_dir": str(DEFAULT_FIXTURE_DIR),
        "persistence_lab_available": True,
        "persistence_command": "dgii_inbound_persistence_lab",
        "persistence_status": "NOT_RUN_BY_DEFAULT",
        "results": [item.to_dict() for item in results],
    }
