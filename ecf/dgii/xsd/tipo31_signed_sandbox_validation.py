"""Offline XSD validation for an explicitly test-only signed Tipo 31 draft."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from ecf.dgii.field_catalogs.tipo_ecf_31 import COMPLIANCE_CLAIM
from ecf.dgii.xml_draft.tipo_ecf_31_unsigned import build_tipo31_unsigned_xml_draft
from ecf.dgii.xsd.tipo31_unsigned_validation import classify_xsd_validation_error
from ecf.dgii.xsd.tipo_ecf_31_structure import DEFAULT_XSD_PATH
from ecf.dgii.xsd.validation import (
    XSDValidationResult,
    lxml_available,
    validate_xml_bytes_against_xsd,
)
from ecf.services.signing_sandbox import (
    TEST_ONLY_SIGNATURE,
    SandboxSigningError,
    sandbox_signature_diagnostics,
    sign_xml_sandbox,
    verify_xml_sandbox_signature,
)
from invoicing.models import Invoice


@dataclass
class Tipo31SignedSandboxValidationReport:
    invoice_internal_code: str
    invoice_id: int | None
    xsd_path: str
    xsd_valid: bool
    signed_sandbox_valid: bool
    signature_status: str = TEST_ONLY_SIGNATURE
    signature_present: bool = False
    signature_verified: bool = False
    remaining_errors: list[dict[str, Any]] = field(default_factory=list)
    signature_errors: list[str] = field(default_factory=list)
    schema_stub_limitations: list[str] = field(default_factory=list)
    validator_engine: str = "unavailable"
    schema_mode: str = "UNAVAILABLE"
    schema_repair_applied: bool = False
    local_xsd_validation_available: bool = False
    compliance_status: str = COMPLIANCE_CLAIM
    dgii_submission_allowed: bool = False
    dgii_call_made: bool = False
    track_id: None = None
    not_certification_evidence: bool = True
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _schema_stub_limitations(xsd_result: XSDValidationResult) -> list[str]:
    limitations: list[str] = []
    if xsd_result.schema_repair_applied:
        limitations.append(
            "Local XSD required an experimental in-memory stub for "
            "IndicadorServicioTodoIncluidoType; this is not official schema content."
        )
    if xsd_result.notes:
        limitations.append(xsd_result.notes)
    return limitations


def _annotate_xsd_errors(xsd_result: XSDValidationResult) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    for error in xsd_result.errors:
        item = error.to_dict()
        item["error_group"] = classify_xsd_validation_error(item.get("message", ""))
        errors.append(item)
    return errors


def validate_tipo31_signed_sandbox(
    invoice: Invoice,
    *,
    allow_demo_encf: bool = False,
    test_only: bool = False,
    require_signing_placeholder: bool = True,
    allow_local_schema_repair: bool = True,
    xsd_path: Path | str | None = None,
) -> Tipo31SignedSandboxValidationReport:
    """Sign and validate a Tipo 31 draft locally with explicit test-only mode."""
    if test_only is not True:
        raise SandboxSigningError(
            "Signed sandbox validation requires explicit --test-only mode."
        )
    path = Path(xsd_path) if xsd_path is not None else DEFAULT_XSD_PATH
    unsigned_xml = build_tipo31_unsigned_xml_draft(
        invoice,
        allow_demo_encf=allow_demo_encf,
        require_signing_placeholder=require_signing_placeholder,
    )
    signed_xml = sign_xml_sandbox(unsigned_xml, test_only=True)
    signature_diagnostics = sandbox_signature_diagnostics(signed_xml)
    signature_errors: list[str] = []
    try:
        signature_verified = verify_xml_sandbox_signature(signed_xml, test_only=True)
    except SandboxSigningError as exc:
        signature_verified = False
        signature_errors.append(str(exc))
    if not signature_verified:
        signature_errors.append("TEST_ONLY_SIGNATURE verification failed.")

    xsd_result = validate_xml_bytes_against_xsd(
        signed_xml,
        path,
        allow_local_schema_repair=allow_local_schema_repair,
    )
    remaining_errors = _annotate_xsd_errors(xsd_result)
    notes = [
        "Signed Tipo 31 sandbox validation is local/offline only.",
        "Signature material is synthetic TEST_ONLY material and is not a DGII certificate.",
        "This result is NOT certification evidence and remains NOT_DGII_COMPLIANT.",
        "No TrackId was created and no DGII call was made.",
    ]
    if signature_diagnostics.get("signature_status") != TEST_ONLY_SIGNATURE:
        signature_errors.append("Sandbox signature diagnostics marker is missing.")

    xsd_valid = bool(xsd_result.is_valid)
    signed_sandbox_valid = xsd_valid and signature_verified and not remaining_errors
    return Tipo31SignedSandboxValidationReport(
        invoice_internal_code=invoice.internal_code,
        invoice_id=invoice.pk,
        xsd_path=path.as_posix(),
        xsd_valid=xsd_valid,
        signed_sandbox_valid=signed_sandbox_valid,
        signature_status=TEST_ONLY_SIGNATURE,
        signature_present=bool(signature_diagnostics.get("signature_present")),
        signature_verified=signature_verified,
        remaining_errors=remaining_errors,
        signature_errors=signature_errors,
        schema_stub_limitations=_schema_stub_limitations(xsd_result),
        validator_engine=xsd_result.validator_engine,
        schema_mode=xsd_result.schema_mode,
        schema_repair_applied=xsd_result.schema_repair_applied,
        local_xsd_validation_available=lxml_available() and path.is_file(),
        notes=notes,
    )
