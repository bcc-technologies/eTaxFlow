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

ERROR_GROUP_SIGNATURE = "signature_missing_expected"
ERROR_GROUP_DEMO_FACET = "demo_facet_mismatch"
ERROR_GROUP_XSD_STUB = "local_xsd_stub_required"
ERROR_GROUP_STRUCTURAL = "structural_mismatch"
ERROR_GROUP_UNKNOWN = "unknown"


def classify_xsd_validation_error(message: str) -> str:
    """Classify one XSD validator message into a Phase 013 error group."""
    msg = (message or "").lower()
    if "missing child" in msg or ("expected is one of" in msg and "*" in msg):
        return ERROR_GROUP_SIGNATURE
    if "encf" in msg and (
        "pattern" in msg or "maxlength" in msg or "minlength" in msg or "length" in msg
    ):
        return ERROR_GROUP_DEMO_FACET
    if "rnc" in msg and "pattern" in msg:
        return ERROR_GROUP_DEMO_FACET
    if "indicadorserviciotodoincluido" in msg or "does not resolve" in msg:
        return ERROR_GROUP_XSD_STUB
    return ERROR_GROUP_UNKNOWN


def classify_validation_errors(
    errors: list[dict[str, Any]],
    *,
    schema_repair_applied: bool,
) -> dict[str, list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = {
        ERROR_GROUP_SIGNATURE: [],
        ERROR_GROUP_DEMO_FACET: [],
        ERROR_GROUP_XSD_STUB: [],
        ERROR_GROUP_STRUCTURAL: [],
        ERROR_GROUP_UNKNOWN: [],
    }
    for err in errors:
        item = dict(err)
        group = classify_xsd_validation_error(item.get("message") or "")
        item["error_group"] = group
        groups[group].append(item)
    if schema_repair_applied and not groups[ERROR_GROUP_XSD_STUB]:
        groups[ERROR_GROUP_XSD_STUB].append(
            {
                "message": (
                    "Local XSD compile required experimental stub for "
                    "IndicadorServicioTodoIncluidoType (declared type name has "
                    "leading whitespace in source file)."
                ),
                "line": None,
                "column": None,
                "error_group": ERROR_GROUP_XSD_STUB,
                "informational": True,
            }
        )
    return groups


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
    total_error_count: int = 0
    intentional_unsigned_error_count: int = 0
    avoidable_demo_facet_error_count: int = 0
    local_xsd_stub_error_count: int = 0
    structural_mismatch_count: int = 0
    unknown_error_count: int = 0
    error_groups: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
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
            "Demo/non-authorized eNCF remains NOT DGII-authorized "
            "(even when pattern-compatible via XSD_FACET_DEMO)."
        )
    if xsd_result.schema_repair_applied:
        expected_reasons.append(
            "Local XSD required experimental type stub to compile "
            "(IndicadorServicioTodoIncluidoType name whitespace defect in source file)"
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

    validation_errors = [e.to_dict() for e in xsd_result.errors]
    error_groups = classify_validation_errors(
        validation_errors,
        schema_repair_applied=xsd_result.schema_repair_applied,
    )
    # Annotate raw errors with groups for JSON consumers.
    for err in validation_errors:
        err["error_group"] = classify_xsd_validation_error(err.get("message") or "")

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

    # Expected invalid: Signature omission keeps draft non-compliant.
    is_valid = False if not diagnostics.signature_present else bool(xsd_result.is_valid)

    return Tipo31UnsignedValidationReport(
        invoice_internal_code=invoice.internal_code,
        invoice_id=invoice.pk,
        xsd_path=path.as_posix(),
        is_valid=is_valid,
        expected_validity=False,
        compliance_status=COMPLIANCE_CLAIM,
        known_missing_required_fields=missing,
        validation_errors=validation_errors,
        structural_mismatches=structural,
        warnings=warnings,
        notes=notes,
        expected_failure_reasons=expected_reasons,
        validator_engine=xsd_result.validator_engine,
        schema_mode=xsd_result.schema_mode,
        schema_repair_applied=xsd_result.schema_repair_applied,
        error_count=xsd_result.error_count,
        total_error_count=xsd_result.error_count,
        intentional_unsigned_error_count=len(error_groups[ERROR_GROUP_SIGNATURE]),
        avoidable_demo_facet_error_count=len(error_groups[ERROR_GROUP_DEMO_FACET]),
        local_xsd_stub_error_count=len(error_groups[ERROR_GROUP_XSD_STUB]),
        structural_mismatch_count=len(structural),
        unknown_error_count=len(error_groups[ERROR_GROUP_UNKNOWN]),
        error_groups=error_groups,
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
        f"- error_count / total_error_count: `{report.total_error_count}`",
        f"- intentional_unsigned_error_count: `{report.intentional_unsigned_error_count}`",
        f"- avoidable_demo_facet_error_count: `{report.avoidable_demo_facet_error_count}`",
        f"- local_xsd_stub_error_count: `{report.local_xsd_stub_error_count}`",
        f"- structural_mismatch_count: `{report.structural_mismatch_count}`",
        f"- unknown_error_count: `{report.unknown_error_count}`",
        "",
        "## Error groups",
        "",
    ]
    for group_name, items in (report.error_groups or {}).items():
        lines.append(f"### `{group_name}` ({len(items)})")
        lines.append("")
        if not items:
            lines.append("- (none)")
        else:
            for err in items:
                lines.append(f"- {err.get('message')}")
        lines.append("")
    lines.extend(
        [
            "## Expected failure reasons",
            "",
        ]
    )
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
