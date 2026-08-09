"""Local XSD validation report for unsigned Tipo 31 drafts.

Expected to fail: Signature/xs:any omitted, demo eNCF limitations, etc.
Does not create Document/ECFDocument, sign, or call DGII.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

from ecf.dgii.field_catalogs.tipo_ecf_31 import COMPLIANCE_CLAIM
from ecf.dgii.xml_draft.tipo_ecf_31_unsigned import (
    build_tipo31_unsigned_draft_diagnostics,
    build_tipo31_unsigned_xml_draft,
)
from ecf.dgii.xsd.tipo_ecf_31_structure import DEFAULT_XSD_PATH
from ecf.dgii.xsd.validation import (
    XSDValidationResult,
    lxml_available,
    validate_xml_bytes_against_xsd,
)
from invoicing.models import Invoice

EXPECTED_FAILURE_REASON = (
    "Signature missing / unsigned draft (required XSD xs:any / Formato Signature omitted)"
)


@dataclass
class Tipo31UnsignedValidationReport:
    invoice_internal_code: str
    invoice_id: int | None
    xsd_path: str
    is_valid: bool
    expected_validity: bool = False
    compliance_status: str = COMPLIANCE_CLAIM
    known_missing_required_fields: list[str] = field(default_factory=list)
    validation_errors: list[dict[str, Any]] = field(default_factory=list)
    structural_mismatches: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    expected_failure_reasons: list[str] = field(default_factory=list)
    validator_engine: str = "unavailable"
    schema_mode: str = "UNAVAILABLE"
    schema_repair_applied: bool = False
    error_count: int = 0
    uses_demo_encf: bool = False
    signature_present: bool = False
    dgii_submission_allowed: bool = False
    local_xsd_validation_available: bool = False
    local_xsd_validation_expected_to_fail: bool = True
    expected_invalid_unsigned_draft: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _classify_structural_mismatches(
    xml_bytes: bytes,
    xsd_result: XSDValidationResult,
    *,
    uses_demo_encf: bool,
) -> list[str]:
    mismatches: list[str] = []
    root = ET.fromstring(xml_bytes)
    child_tags = [child.tag for child in list(root)]

    if "Signature" in child_tags:
        mismatches.append("Unexpected Signature element present in unsigned draft.")
    else:
        mismatches.append(
            "Signature / required XSD xs:any after FechaHoraFirma is omitted "
            "(expected for unsigned draft)."
        )

    if "FechaHoraFirma" not in child_tags:
        mismatches.append("FechaHoraFirma element missing from unsigned draft XML.")

    if uses_demo_encf:
        mismatches.append(
            "official_encf appears demo/non-authorized and is not DGII-authorized."
        )

    for err in xsd_result.errors:
        msg = (err.message or "").lower()
        if "encf" in msg and ("pattern" in msg or "maxlength" in msg or "length" in msg):
            item = f"XSD facet mismatch on eNCF: {err.message}"
            if item not in mismatches:
                mismatches.append(item)
        if "missing child" in msg or ("expected is one of" in msg and "*" in msg):
            item = (
                "XSD reports missing required child after FechaHoraFirma "
                f"(Signature/xs:any): {err.message}"
            )
            if item not in mismatches:
                mismatches.append(item)

    if xsd_result.schema_mode == "SCHEMA_COMPILE_FAILED":
        mismatches.append(
            "Local XSD failed to compile; instance validation could not complete."
        )
    if xsd_result.schema_repair_applied:
        mismatches.append(
            "Validation used experimental local stub for missing "
            "IndicadorServicioTodoIncluidoType (not official DGII schema)."
        )
    return mismatches


def validate_tipo31_unsigned_draft(
    invoice: Invoice,
    *,
    allow_demo_encf: bool = False,
    require_signing_placeholder: bool = True,
    allow_local_schema_repair: bool = True,
    xsd_path: Path | str | None = None,
) -> Tipo31UnsignedValidationReport:
    """Build unsigned draft and validate against local XSD (no side effects)."""
    path = Path(xsd_path) if xsd_path is not None else DEFAULT_XSD_PATH

    diagnostics = build_tipo31_unsigned_draft_diagnostics(
        invoice,
        allow_demo_encf=allow_demo_encf,
        require_signing_placeholder=require_signing_placeholder,
    )
    xml_bytes = build_tipo31_unsigned_xml_draft(
        invoice,
        allow_demo_encf=allow_demo_encf,
        require_signing_placeholder=require_signing_placeholder,
    )

    xsd_result = validate_xml_bytes_against_xsd(
        xml_bytes,
        path,
        allow_local_schema_repair=allow_local_schema_repair,
    )

    missing = list(diagnostics.missing_required_fields)
    if "Signature" not in missing:
        missing.append("Signature")

    expected_reasons = [EXPECTED_FAILURE_REASON]
    if diagnostics.uses_demo_encf:
        expected_reasons.append(
            "Demo/non-authorized eNCF is not DGII-authorized and may violate eNCF facets"
        )
    if xsd_result.schema_repair_applied:
        expected_reasons.append(
            "Local XSD required experimental type stub to compile "
            "(IndicadorServicioTodoIncluidoType missing in source file)"
        )
    if not xsd_result.schema_compiled:
        expected_reasons.append(
            "Local XSD could not be compiled without repair; validation remains experimental"
        )

    structural = _classify_structural_mismatches(
        xml_bytes,
        xsd_result,
        uses_demo_encf=diagnostics.uses_demo_encf,
    )

    warnings = sorted(
        set(diagnostics.warnings)
        | set(xsd_result.warnings)
        | {
            "EXPECTED_INVALID_UNSIGNED_DRAFT",
            "NOT_CERTIFICATION_EVIDENCE",
        }
    )

    notes = [
        "Unsigned Tipo 31 draft local XSD validation experiment only.",
        "Failure is expected while Signature/XMLDSig is unimplemented.",
        "This report is NOT DGII compliance or certification evidence.",
        "No Document/ECFDocument was created; no DGII submission occurred.",
    ]
    if xsd_result.notes:
        notes.append(xsd_result.notes)

    # Expected invalid: either schema says invalid, or known Signature omission.
    is_valid = bool(xsd_result.is_valid) and diagnostics.signature_present
    # Signature is never present in this phase → always expected invalid.
    is_valid = False if not diagnostics.signature_present else is_valid

    return Tipo31UnsignedValidationReport(
        invoice_internal_code=invoice.internal_code,
        invoice_id=invoice.pk,
        xsd_path=path.as_posix(),
        is_valid=is_valid,
        expected_validity=False,
        compliance_status=COMPLIANCE_CLAIM,
        known_missing_required_fields=missing,
        validation_errors=[e.to_dict() for e in xsd_result.errors],
        structural_mismatches=structural,
        warnings=warnings,
        notes=notes,
        expected_failure_reasons=expected_reasons,
        validator_engine=xsd_result.validator_engine,
        schema_mode=xsd_result.schema_mode,
        schema_repair_applied=xsd_result.schema_repair_applied,
        error_count=xsd_result.error_count,
        uses_demo_encf=diagnostics.uses_demo_encf,
        signature_present=False,
        dgii_submission_allowed=False,
        local_xsd_validation_available=lxml_available() and path.is_file(),
        local_xsd_validation_expected_to_fail=True,
        expected_invalid_unsigned_draft=True,
    )


def render_tipo31_unsigned_validation_markdown(
    report: Tipo31UnsignedValidationReport,
) -> str:
    """Render a Markdown validation report (local artifact; not certification)."""
    lines = [
        "# Tipo 31 unsigned draft — local XSD validation report",
        "",
        "> **NOT_DGII_COMPLIANT.** Not certification evidence. No DGII submission.",
        "",
        "## Summary",
        "",
        f"- Invoice: `{report.invoice_internal_code}` (id={report.invoice_id})",
        f"- XSD: `{report.xsd_path}`",
        f"- Validator engine: `{report.validator_engine}`",
        f"- Schema mode: `{report.schema_mode}`",
        f"- Schema repair applied: `{report.schema_repair_applied}`",
        f"- is_valid: `{report.is_valid}`",
        f"- expected_validity: `{report.expected_validity}`",
        f"- expected_invalid_unsigned_draft: `{report.expected_invalid_unsigned_draft}`",
        f"- compliance_status: `{report.compliance_status}`",
        f"- signature_present: `{report.signature_present}`",
        f"- uses_demo_encf: `{report.uses_demo_encf}`",
        f"- error_count: `{report.error_count}`",
        "",
        "## Expected failure reasons",
        "",
    ]
    for reason in report.expected_failure_reasons:
        lines.append(f"- {reason}")
    lines.extend(["", "## Known missing required fields", ""])
    for field_name in report.known_missing_required_fields:
        lines.append(f"- `{field_name}`")
    lines.extend(["", "## Structural mismatches", ""])
    for item in report.structural_mismatches:
        lines.append(f"- {item}")
    lines.extend(["", "## Validation errors", ""])
    if not report.validation_errors:
        lines.append("- (none)")
    else:
        for err in report.validation_errors:
            loc = ""
            if err.get("line") is not None:
                loc = f"L{err.get('line')}"
                if err.get("column") is not None:
                    loc += f":C{err.get('column')}"
                loc += " "
            lines.append(f"- {loc}{err.get('message')}")
    lines.extend(["", "## Warnings", ""])
    for warning in report.warnings:
        lines.append(f"- `{warning}`")
    lines.extend(["", "## Notes", ""])
    for note in report.notes:
        lines.append(f"- {note}")
    lines.extend(
        [
            "",
            "## Explicit non-claims",
            "",
            "- This report does **not** prove DGII compliance.",
            "- This report does **not** authorize demo eNCF values.",
            "- Signature/XMLDSig remains unimplemented.",
            "- No certificates, private keys, TrackId, or DGII calls were used.",
            "",
        ]
    )
    return "\n".join(lines)


def write_tipo31_unsigned_validation_report(
    report: Tipo31UnsignedValidationReport,
    output_path: Path | str,
) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_tipo31_unsigned_validation_markdown(report), encoding="utf-8")
    return path
