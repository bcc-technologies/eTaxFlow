"""Extract exact local Tipo 31 XSD facet constraints (stdlib parse only)."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

from ecf.dgii.xsd.tipo_ecf_31_structure import DEFAULT_XSD_PATH

XS = "{http://www.w3.org/2001/XMLSchema}"


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def _find_simple_type(schema_root: ET.Element, type_name: str) -> ET.Element | None:
    for el in schema_root:
        if _local(el.tag) == "simpleType" and el.get("name") == type_name:
            return el
    # Also scan all (handles odd whitespace names nearby).
    for el in schema_root.iter():
        if _local(el.tag) == "simpleType" and (el.get("name") or "").strip() == type_name:
            return el
    return None


def _facet_dict(simple_type: ET.Element) -> dict[str, Any]:
    out: dict[str, Any] = {
        "type_name": (simple_type.get("name") or "").strip(),
        "raw_type_name": simple_type.get("name"),
        "pattern": None,
        "min_length": None,
        "max_length": None,
        "enumerations": [],
    }
    for el in simple_type.iter():
        tag = _local(el.tag)
        if tag == "pattern":
            out["pattern"] = el.get("value")
        elif tag == "minLength":
            out["min_length"] = el.get("value")
        elif tag == "maxLength":
            out["max_length"] = el.get("value")
        elif tag == "enumeration":
            out["enumerations"].append(el.get("value"))
    return out


def _line_of(path: Path, needle: str) -> int | None:
    try:
        for idx, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if needle in line:
                return idx
    except OSError:
        return None
    return None


def extract_tipo31_xsd_facets(xsd_path: Path | str | None = None) -> dict[str, Any]:
    """Return exact facets for eNCF and RNC types from the local XSD."""
    path = Path(xsd_path) if xsd_path is not None else DEFAULT_XSD_PATH
    tree = ET.parse(path)
    root = tree.getroot()

    encf_type = _find_simple_type(root, "eNCFValidationType")
    rnc_type = _find_simple_type(root, "RNCValidationType")
    if encf_type is None or rnc_type is None:
        raise RuntimeError(
            "Could not extract eNCFValidationType and/or RNCValidationType from local XSD."
        )

    # Detect leading-space defect on IndicadorServicioTodoIncluidoType.
    stub_defect = None
    for el in root.iter():
        if _local(el.tag) == "simpleType":
            name = el.get("name") or ""
            if "IndicadorServicioTodoIncluidoType" in name and name != "IndicadorServicioTodoIncluidoType":
                stub_defect = {
                    "declared_name": name,
                    "expected_name": "IndicadorServicioTodoIncluidoType",
                    "issue": "Type name has unexpected whitespace/mismatch vs element type reference.",
                    "approx_line": _line_of(path, 'name=" IndicadorServicioTodoIncluidoType"')
                    or _line_of(path, "IndicadorServicioTodoIncluidoType"),
                }
                break

    return {
        "xsd_path": path.as_posix(),
        "eNCF": {
            **_facet_dict(encf_type),
            "element_paths": ["ECF/Encabezado/IdDoc/eNCF"],
            "element_decl_line": _line_of(path, 'name="eNCF"'),
            "type_decl_line": _line_of(path, 'name="eNCFValidationType"'),
        },
        "RNC": {
            **_facet_dict(rnc_type),
            "element_paths": [
                "ECF/Encabezado/Emisor/RNCEmisor",
                "ECF/Encabezado/Comprador/RNCComprador",
            ],
            "element_decl_lines": {
                "RNCEmisor": _line_of(path, 'name="RNCEmisor"'),
                "RNCComprador": _line_of(path, 'name="RNCComprador"'),
            },
            "type_decl_line": _line_of(path, 'name="RNCValidationType"'),
        },
        "local_xsd_defects": [stub_defect] if stub_defect else [],
    }


def rnc_matches_xsd_facet(value: str | None, facets: dict[str, Any] | None = None) -> bool:
    import re

    if value is None:
        return False
    data = facets or extract_tipo31_xsd_facets()
    pattern = data["RNC"]["pattern"]
    if not pattern:
        return False
    return re.fullmatch(pattern, str(value)) is not None


def encf_matches_xsd_facet(value: str | None, facets: dict[str, Any] | None = None) -> bool:
    import re

    if value is None:
        return False
    data = facets or extract_tipo31_xsd_facets()
    pattern = data["eNCF"]["pattern"]
    if not pattern:
        return False
    text = str(value)
    min_len = int(data["eNCF"]["min_length"] or 0)
    max_len = int(data["eNCF"]["max_length"] or 10**9)
    if not (min_len <= len(text) <= max_len):
        return False
    return re.fullmatch(pattern, text) is not None
