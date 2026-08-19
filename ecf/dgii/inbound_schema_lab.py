"""Local/offline inbound XSD validation lab (Phase 029 — no DB, no DGII, no network)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from lxml import etree

from ecf.dgii.inbound_lab import (
    DEFAULT_FIXTURE_DIR,
    InboundLabResult,
    analyze_inbound_xml,
)
from ecf.dgii.receiver import ReceiverDocumentType

SOURCES_DIR = Path("docs/dgii/sources")
SCHEMA_VALIDATION_SCOPE = "LOCAL_OFFLINE_ONLY"

DEFAULT_XSD_BY_DOCUMENT_TYPE = {
    ReceiverDocumentType.ECF.value: "e-CF_31_v1.0.xsd",
    ReceiverDocumentType.ARECF.value: "ARECF_v1.0.xsd",
    ReceiverDocumentType.ACECF.value: "ACECF_v1.0.xsd",
}

_MAX_XSD_ERRORS = 20
_MAX_ERROR_CHARS = 500


def _safe_parser() -> etree.XMLParser:
    return etree.XMLParser(
        resolve_entities=False,
        no_network=True,
        huge_tree=False,
        dtd_validation=False,
        load_dtd=False,
    )


def _normalize_document_type(document_type: str | ReceiverDocumentType | None) -> str:
    if document_type is None:
        return ReceiverDocumentType.UNKNOWN.value
    if isinstance(document_type, ReceiverDocumentType):
        return document_type.value
    return str(document_type).strip().upper() or ReceiverDocumentType.UNKNOWN.value


def _truncate_error(message: str) -> str:
    text = " ".join(str(message).split())
    if len(text) <= _MAX_ERROR_CHARS:
        return text
    return f"{text[:_MAX_ERROR_CHARS]}..."


def _collect_error_log(error_log) -> tuple[str, ...]:
    messages: list[str] = []
    for entry in error_log:
        messages.append(_truncate_error(entry))
        if len(messages) >= _MAX_XSD_ERRORS:
            break
    return tuple(messages)


@dataclass(frozen=True)
class LocalXsdMapping:
    document_type: str
    xsd_filename: str | None
    xsd_path: str | None
    xsd_available: bool
    status: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class LocalXsdCompileResult:
    xsd_path: str | None
    xsd_compiled: bool
    errors: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class LocalXsdValidationResult:
    xsd_path: str | None
    xsd_available: bool
    xsd_compiled: bool
    local_xsd_valid: bool
    xsd_error_count: int
    xsd_errors: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["xsd_errors"] = list(self.xsd_errors)
        return payload


@dataclass(frozen=True)
class InboundSchemaLabResult:
    filename: str | None
    sha256: str
    root_tag: str
    document_type: str
    signature_present: bool
    signature_verified: bool
    status: str
    errors: tuple[str, ...]
    xsd_path: str | None
    xsd_available: bool
    xsd_compiled: bool
    local_xsd_valid: bool
    xsd_error_count: int
    xsd_errors: tuple[str, ...]
    schema_validation_scope: str = SCHEMA_VALIDATION_SCOPE
    compliance_status: str = "NOT_DGII_COMPLIANT"
    dgii_submission_allowed: bool = False
    certification_evidence: bool = False
    track_id: None = None
    persisted: bool = False
    dgii_call_made: bool = False

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["errors"] = list(self.errors)
        payload["xsd_errors"] = list(self.xsd_errors)
        return payload


def find_local_xsd_for_document_type(
    document_type: str | ReceiverDocumentType | None,
    xml_bytes: bytes | None = None,
) -> LocalXsdMapping:
    """Map inbound type to a local XSD path. ECF lab uses Tipo 31 XSD only."""
    del xml_bytes  # TipoeCF detector not implemented; ECF always maps to e-CF 31.
    normalized = _normalize_document_type(document_type)
    filename = DEFAULT_XSD_BY_DOCUMENT_TYPE.get(normalized)
    if not filename:
        return LocalXsdMapping(
            document_type=normalized,
            xsd_filename=None,
            xsd_path=None,
            xsd_available=False,
            status="UNSUPPORTED",
        )
    path = SOURCES_DIR / filename
    available = path.is_file()
    return LocalXsdMapping(
        document_type=normalized,
        xsd_filename=filename,
        xsd_path=str(path) if available else str(path),
        xsd_available=available,
        status="MAPPED" if available else "MISSING",
    )


def compile_local_xsd(xsd_path: Path | str | None) -> LocalXsdCompileResult:
    """Compile a local XSD with no network and no remote resource fetch."""
    if xsd_path is None:
        return LocalXsdCompileResult(xsd_path=None, xsd_compiled=False, errors=("xsd_path_missing",))
    path = Path(xsd_path)
    if not path.is_file():
        return LocalXsdCompileResult(
            xsd_path=str(path),
            xsd_compiled=False,
            errors=("xsd_file_not_found",),
        )
    try:
        xsd_doc = etree.parse(str(path), parser=_safe_parser())
        etree.XMLSchema(xsd_doc)
    except (etree.XMLSchemaParseError, etree.XMLSyntaxError, OSError) as exc:
        return LocalXsdCompileResult(
            xsd_path=str(path),
            xsd_compiled=False,
            errors=(_truncate_error(exc),),
        )
    return LocalXsdCompileResult(xsd_path=str(path), xsd_compiled=True)


def validate_xml_against_local_xsd(
    xml_bytes: bytes,
    xsd_path: Path | str | None,
) -> LocalXsdValidationResult:
    """Validate XML against a local XSD. Missing/invalid inputs return structured errors."""
    path = Path(xsd_path) if xsd_path is not None else None
    if path is None or not path.is_file():
        return LocalXsdValidationResult(
            xsd_path=str(path) if path is not None else None,
            xsd_available=False,
            xsd_compiled=False,
            local_xsd_valid=False,
            xsd_error_count=1,
            xsd_errors=("xsd_unavailable",),
        )

    compile_result = compile_local_xsd(path)
    xml_doc = None
    xml_parse_errors: tuple[str, ...] = ()
    if not xml_bytes or not xml_bytes.strip():
        xml_parse_errors = ("invalid_xml",)
    else:
        try:
            xml_doc = etree.fromstring(xml_bytes, parser=_safe_parser())
        except etree.XMLSyntaxError:
            xml_parse_errors = ("invalid_xml",)

    if xml_parse_errors:
        extra = compile_result.errors if not compile_result.xsd_compiled else ()
        errors = xml_parse_errors + extra
        return LocalXsdValidationResult(
            xsd_path=str(path),
            xsd_available=True,
            xsd_compiled=compile_result.xsd_compiled,
            local_xsd_valid=False,
            xsd_error_count=len(errors),
            xsd_errors=errors,
        )

    if not compile_result.xsd_compiled:
        errors = compile_result.errors or ("xsd_compile_failed",)
        return LocalXsdValidationResult(
            xsd_path=str(path),
            xsd_available=True,
            xsd_compiled=False,
            local_xsd_valid=False,
            xsd_error_count=len(errors),
            xsd_errors=errors,
        )

    xsd_doc = etree.parse(str(path), parser=_safe_parser())
    schema = etree.XMLSchema(xsd_doc)
    is_valid = bool(schema.validate(xml_doc))
    errors = _collect_error_log(schema.error_log)
    if not is_valid and not errors:
        errors = ("local_xsd_invalid",)
    return LocalXsdValidationResult(
        xsd_path=str(path),
        xsd_available=True,
        xsd_compiled=True,
        local_xsd_valid=is_valid,
        xsd_error_count=len(errors),
        xsd_errors=errors,
    )


def _merge_lab_and_xsd(
    lab: InboundLabResult,
    xsd: LocalXsdValidationResult,
) -> InboundSchemaLabResult:
    return InboundSchemaLabResult(
        filename=lab.filename,
        sha256=lab.sha256,
        root_tag=lab.root_tag,
        document_type=lab.document_type,
        signature_present=lab.signature_present,
        signature_verified=False,
        status=lab.status,
        errors=lab.errors,
        xsd_path=xsd.xsd_path,
        xsd_available=xsd.xsd_available,
        xsd_compiled=xsd.xsd_compiled,
        local_xsd_valid=xsd.local_xsd_valid,
        xsd_error_count=xsd.xsd_error_count,
        xsd_errors=xsd.xsd_errors,
    )


def analyze_inbound_xml_with_local_xsd(
    xml_bytes: bytes,
    filename: str | None = None,
) -> InboundSchemaLabResult:
    """Classify inbound XML and add local/offline XSD validation fields."""
    lab = analyze_inbound_xml(xml_bytes, filename=filename)
    mapping = find_local_xsd_for_document_type(lab.document_type, xml_bytes)
    if not mapping.xsd_available:
        xsd = LocalXsdValidationResult(
            xsd_path=mapping.xsd_path,
            xsd_available=False,
            xsd_compiled=False,
            local_xsd_valid=False,
            xsd_error_count=1,
            xsd_errors=("xsd_unavailable" if mapping.status == "MISSING" else "xsd_unmapped",),
        )
        return _merge_lab_and_xsd(lab, xsd)
    xsd = validate_xml_against_local_xsd(xml_bytes, mapping.xsd_path)
    return _merge_lab_and_xsd(lab, xsd)


def analyze_path_with_local_xsd(path: Path | str) -> list[InboundSchemaLabResult]:
    """Analyze a fixture file or directory; directory order is sorted by filename."""
    target = Path(path)
    if target.is_file():
        xml_bytes = target.read_bytes()
        return [analyze_inbound_xml_with_local_xsd(xml_bytes, filename=target.name)]
    if target.is_dir():
        results: list[InboundSchemaLabResult] = []
        for fixture_path in sorted(target.glob("*.xml")):
            xml_bytes = fixture_path.read_bytes()
            results.append(
                analyze_inbound_xml_with_local_xsd(xml_bytes, filename=fixture_path.name)
            )
        return results
    raise FileNotFoundError(f"Path is neither file nor directory: {target}")


def build_schema_lab_report(results: list[InboundSchemaLabResult]) -> dict[str, Any]:
    invalid_count = sum(1 for item in results if not item.local_xsd_valid)
    return {
        "lab_mode": "NON_PRODUCTION_ONLY",
        "schema_validation_scope": SCHEMA_VALIDATION_SCOPE,
        "synthetic_sample_marker": "NON_OFFICIAL_SYNTHETIC_SAMPLE",
        "compliance_status": "NOT_DGII_COMPLIANT",
        "dgii_submission_allowed": False,
        "certification_evidence": False,
        "not_certification_evidence": True,
        "dgii_call_made": False,
        "track_id": None,
        "persisted": False,
        "fixture_count": len(results),
        "local_xsd_invalid_count": invalid_count,
        "default_fixture_dir": str(DEFAULT_FIXTURE_DIR),
        "xsd_mapping": {
            doc_type: filename for doc_type, filename in DEFAULT_XSD_BY_DOCUMENT_TYPE.items()
        },
        "signature_verification_available": True,
        "signature_verification_command": "dgii_inbound_signature_lab",
        "signature_verification_status": "NOT_RUN_BY_DEFAULT",
        "persistence_lab_available": True,
        "persistence_command": "dgii_inbound_persistence_lab",
        "persistence_status": "NOT_RUN_BY_DEFAULT",
        "results": [item.to_dict() for item in results],
    }
