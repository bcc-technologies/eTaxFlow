"""Local XML Schema validation helpers (offline only).

Uses ``lxml`` because Python's stdlib ``xml`` package cannot validate
documents against XSD. No network / remote schema fetching.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from ecf.dgii.xsd.tipo_ecf_31_structure import DEFAULT_XSD_PATH

# Experimental stub for the single unresolved local XSD type reference.
# Official local e-CF_31_v1.0.xsd references IndicadorServicioTodoIncluidoType
# but does not define it. This stub exists only so instance validation can run
# locally; it is NOT an official DGII schema and is NOT_DGII_COMPLIANT evidence.
_EXPERIMENTAL_TYPE_STUB = """
  <!-- EXPERIMENTAL LOCAL STUB ONLY — not an official DGII schema fragment -->
  <xs:simpleType name="IndicadorServicioTodoIncluidoType">
    <xs:annotation>
      <xs:documentation>
        Experimental local stub. Source XSD references this type but does not define it.
      </xs:documentation>
    </xs:annotation>
    <xs:restriction base="xs:integer">
      <xs:enumeration value="0"/>
      <xs:enumeration value="1"/>
    </xs:restriction>
  </xs:simpleType>
"""

_STUB_MARKER = '<xs:element name="ECF"'


@dataclass
class XSDValidationErrorItem:
    message: str
    line: int | None = None
    column: int | None = None
    domain: str | None = None
    type_name: str | None = None
    level: str = "error"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class XSDValidationResult:
    is_valid: bool
    xsd_path: str
    error_count: int = 0
    errors: list[XSDValidationErrorItem] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    validator_engine: str = "unavailable"
    notes: str = ""
    schema_compiled: bool = False
    schema_repair_applied: bool = False
    schema_mode: str = "UNAVAILABLE"
    available: bool = False

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["errors"] = [e if isinstance(e, dict) else e for e in payload["errors"]]
        return payload


class XSDValidatorUnavailableError(RuntimeError):
    """Raised when the configured XSD validator engine cannot be imported."""


def lxml_available() -> bool:
    try:
        import lxml.etree  # noqa: F401
    except ImportError:
        return False
    return True


def _require_lxml():
    try:
        from lxml import etree
    except ImportError as exc:
        raise XSDValidatorUnavailableError(
            "lxml is required for local XSD validation. "
            "Python stdlib cannot validate XML against XSD. "
            "Install the project dependency: lxml>=5.0,<7.0"
        ) from exc
    return etree


def _parser_no_network(etree):
    return etree.XMLParser(
        load_dtd=False,
        no_network=True,
        resolve_entities=False,
    )


def _build_schema(etree, xsd_path: Path, *, allow_local_schema_repair: bool):
    """Compile XMLSchema from local file; optionally stub missing type in-memory."""
    raw = xsd_path.read_bytes()
    parser = _parser_no_network(etree)
    repair_applied = False
    mode = "STRICT_LOCAL_XSD"
    notes: list[str] = []

    try:
        schema_doc = etree.parse(str(xsd_path), parser)
        schema = etree.XMLSchema(schema_doc)
        return schema, repair_applied, mode, notes
    except etree.XMLSchemaParseError as strict_exc:
        notes.append(
            f"Strict local XSD compile failed: {strict_exc}. "
            "This is a local-source limitation, not DGII certification evidence."
        )
        if not allow_local_schema_repair:
            raise

        text = raw.decode("utf-8")
        if "IndicadorServicioTodoIncluidoType" not in text or _STUB_MARKER not in text:
            raise

        repaired = text.replace(_STUB_MARKER, _EXPERIMENTAL_TYPE_STUB + _STUB_MARKER, 1)
        schema_doc = etree.fromstring(repaired.encode("utf-8"), parser=parser)
        schema = etree.XMLSchema(schema_doc)
        repair_applied = True
        mode = "LOCAL_XSD_WITH_EXPERIMENTAL_TYPE_STUB"
        notes.append(
            "Applied experimental in-memory stub for missing "
            "IndicadorServicioTodoIncluidoType so instance validation can run. "
            "Stub is NOT official DGII schema content."
        )
        return schema, repair_applied, mode, notes


def validate_xml_bytes_against_xsd(
    xml_bytes: bytes,
    xsd_path: Path | str | None = None,
    *,
    allow_local_schema_repair: bool = True,
) -> XSDValidationResult:
    """Validate XML bytes against a local XSD path (offline only)."""
    path = Path(xsd_path) if xsd_path is not None else DEFAULT_XSD_PATH
    path_text = path.as_posix()

    if not lxml_available():
        return XSDValidationResult(
            is_valid=False,
            xsd_path=path_text,
            error_count=1,
            errors=[
                XSDValidationErrorItem(
                    message=(
                        "lxml is not installed; local XSD validation unavailable. "
                        "stdlib cannot validate against XSD."
                    )
                )
            ],
            warnings=["VALIDATOR_UNAVAILABLE"],
            validator_engine="unavailable",
            notes="Install lxml>=5.0,<7.0 for local offline XSD validation.",
            schema_compiled=False,
            schema_repair_applied=False,
            schema_mode="UNAVAILABLE",
            available=False,
        )

    etree = _require_lxml()

    if not path.is_file():
        return XSDValidationResult(
            is_valid=False,
            xsd_path=path_text,
            error_count=1,
            errors=[
                XSDValidationErrorItem(
                    message=f"Local XSD file not found: {path_text}"
                )
            ],
            warnings=["XSD_FILE_MISSING"],
            validator_engine="lxml",
            notes="Place e-CF_31_v1.0.xsd under docs/dgii/sources/ for local validation.",
            schema_compiled=False,
            schema_repair_applied=False,
            schema_mode="UNAVAILABLE",
            available=True,
        )

    try:
        schema, repair_applied, mode, notes = _build_schema(
            etree,
            path,
            allow_local_schema_repair=allow_local_schema_repair,
        )
    except etree.XMLSchemaParseError as exc:
        err_items = [
            XSDValidationErrorItem(
                message=str(exc),
                line=getattr(getattr(exc, "error_log", None), "last_error", None)
                and exc.error_log.last_error.line,
            )
        ]
        if hasattr(exc, "error_log"):
            err_items = [
                XSDValidationErrorItem(
                    message=e.message,
                    line=e.line,
                    column=e.column,
                    domain=str(getattr(e, "domain_name", None) or ""),
                    type_name=str(getattr(e, "type_name", None) or ""),
                )
                for e in list(exc.error_log)
            ] or err_items
        return XSDValidationResult(
            is_valid=False,
            xsd_path=path_text,
            error_count=len(err_items),
            errors=err_items,
            warnings=["XSD_SCHEMA_COMPILE_FAILED"],
            validator_engine="lxml",
            notes=(
                "Local XSD could not be compiled. "
                "No instance validation was performed. NOT_DGII_COMPLIANT."
            ),
            schema_compiled=False,
            schema_repair_applied=False,
            schema_mode="SCHEMA_COMPILE_FAILED",
            available=True,
        )

    try:
        parser = _parser_no_network(etree)
        doc = etree.fromstring(xml_bytes, parser=parser)
    except etree.XMLSyntaxError as exc:
        return XSDValidationResult(
            is_valid=False,
            xsd_path=path_text,
            error_count=1,
            errors=[
                XSDValidationErrorItem(
                    message=str(exc),
                    line=getattr(exc, "lineno", None),
                )
            ],
            warnings=["XML_SYNTAX_ERROR"],
            validator_engine="lxml",
            notes="Instance XML could not be parsed. " + "; ".join(notes),
            schema_compiled=True,
            schema_repair_applied=repair_applied,
            schema_mode=mode,
            available=True,
        )

    ok = bool(schema.validate(doc))
    errors = [
        XSDValidationErrorItem(
            message=e.message,
            line=e.line,
            column=e.column,
            domain=str(getattr(e, "domain_name", None) or ""),
            type_name=str(getattr(e, "type_name", None) or ""),
        )
        for e in list(schema.error_log)
    ]
    warnings: list[str] = []
    if repair_applied:
        warnings.append("EXPERIMENTAL_XSD_TYPE_STUB_APPLIED")
    if not ok:
        warnings.append("INSTANCE_INVALID_AGAINST_LOCAL_XSD")

    return XSDValidationResult(
        is_valid=ok,
        xsd_path=path_text,
        error_count=len(errors),
        errors=errors,
        warnings=warnings,
        validator_engine="lxml",
        notes=(
            "; ".join(notes)
            + (" " if notes else "")
            + "Local offline validation only. Not certification evidence. NOT_DGII_COMPLIANT."
        ).strip(),
        schema_compiled=True,
        schema_repair_applied=repair_applied,
        schema_mode=mode,
        available=True,
    )
