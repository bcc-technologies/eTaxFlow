"""Conservative structure extraction from local e-CF_31_v1.0.xsd.

Uses stdlib xml.etree only. No network. Does not validate instance documents.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

XS_NS = "http://www.w3.org/2001/XMLSchema"
XS = f"{{{XS_NS}}}"

DEFAULT_XSD_PATH = Path("docs/dgii/sources/e-CF_31_v1.0.xsd")


class Tipo31XsdStructureError(RuntimeError):
    """Raised when the local Tipo 31 XSD cannot be loaded or interpreted."""


def _local(tag: str) -> str:
    if tag.startswith("{"):
        return tag.rsplit("}", 1)[-1]
    return tag


def _min_occurs(el: ET.Element) -> int:
    raw = el.get("minOccurs")
    if raw is None:
        return 1
    try:
        return int(raw)
    except ValueError as exc:
        raise Tipo31XsdStructureError(
            f"Invalid minOccurs={raw!r} on element {el.get('name')!r}."
        ) from exc


def _max_occurs(el: ET.Element) -> str:
    return el.get("maxOccurs") or "1"


def load_tipo31_xsd_tree(xsd_path: Path | str | None = None) -> ET.ElementTree:
    """Parse the local e-CF 31 XSD into an ElementTree."""
    path = Path(xsd_path) if xsd_path is not None else DEFAULT_XSD_PATH
    if not path.is_file():
        raise Tipo31XsdStructureError(
            f"Local Tipo 31 XSD not found at {path.as_posix()}. "
            "Place e-CF_31_v1.0.xsd under docs/dgii/sources/."
        )
    try:
        return ET.parse(path)
    except ET.ParseError as exc:
        raise Tipo31XsdStructureError(
            f"Failed to parse local Tipo 31 XSD at {path.as_posix()}: {exc}"
        ) from exc


def _find_ecf_element(schema_root: ET.Element) -> ET.Element:
    for child in schema_root:
        if _local(child.tag) == "element" and child.get("name") == "ECF":
            return child
    raise Tipo31XsdStructureError(
        "Local Tipo 31 XSD does not define a top-level element named 'ECF'."
    )


def _find_sequence(container: ET.Element) -> ET.Element | None:
    """Find the first xs:sequence under an element/complexType container."""
    for child in container:
        tag = _local(child.tag)
        if tag == "complexType":
            found = _find_sequence(child)
            if found is not None:
                return found
        elif tag == "complexContent":
            for nested in child:
                if _local(nested.tag) in {"extension", "restriction"}:
                    found = _find_sequence(nested)
                    if found is not None:
                        return found
        elif tag == "sequence":
            return child
    return None


def extract_tipo31_root_name(xsd_path: Path | str | None = None) -> str:
    """Return the XSD-supported root element name (expected: ECF)."""
    tree = load_tipo31_xsd_tree(xsd_path)
    ecf = _find_ecf_element(tree.getroot())
    name = ecf.get("name")
    if not name:
        raise Tipo31XsdStructureError("ECF element is missing a name attribute.")
    return name


def extract_tipo31_top_level_sequence(
    xsd_path: Path | str | None = None,
) -> list[dict[str, Any]]:
    """Return ordered top-level particles under ECF."""
    tree = load_tipo31_xsd_tree(xsd_path)
    ecf = _find_ecf_element(tree.getroot())
    sequence = _find_sequence(ecf)
    if sequence is None:
        raise Tipo31XsdStructureError("ECF element has no xs:sequence.")

    particles: list[dict[str, Any]] = []
    for particle in sequence:
        tag = _local(particle.tag)
        if tag == "element":
            particles.append(
                {
                    "kind": "element",
                    "name": particle.get("name"),
                    "min_occurs": _min_occurs(particle),
                    "max_occurs": _max_occurs(particle),
                    "type": particle.get("type"),
                }
            )
        elif tag == "any":
            particles.append(
                {
                    "kind": "any",
                    "name": "Signature",  # Formato PDF names <Signature>; XSD uses xs:any
                    "xsd_representation": "xs:any",
                    "min_occurs": _min_occurs(particle),
                    "max_occurs": _max_occurs(particle),
                    "process_contents": particle.get("processContents"),
                    "notes": (
                        "Formato PDF section H names <Signature>; local XSD encodes "
                        "required xs:any processContents=skip after FechaHoraFirma."
                    ),
                }
            )
        else:
            particles.append(
                {
                    "kind": tag,
                    "name": particle.get("name"),
                    "min_occurs": _min_occurs(particle) if particle.get("minOccurs") is not None else None,
                    "max_occurs": particle.get("maxOccurs"),
                }
            )
    if not particles:
        raise Tipo31XsdStructureError("ECF xs:sequence contains no particles.")
    return particles


def _walk_element_paths(
    element: ET.Element,
    parent_path: str,
    *,
    required_out: list[str],
    optional_out: list[str],
) -> None:
    name = element.get("name")
    if not name:
        return
    path = f"{parent_path}/{name}" if parent_path else name
    required = _min_occurs(element) > 0
    if required:
        required_out.append(path)
    else:
        optional_out.append(path)

    sequence = _find_sequence(element)
    if sequence is None:
        return
    for particle in sequence:
        tag = _local(particle.tag)
        if tag == "element":
            _walk_element_paths(
                particle,
                path,
                required_out=required_out,
                optional_out=optional_out,
            )
        elif tag == "any":
            any_path = f"{path}/(xs:any)"
            if _min_occurs(particle) > 0:
                required_out.append(any_path)
            else:
                optional_out.append(any_path)


def extract_tipo31_required_paths(
    xsd_path: Path | str | None = None,
) -> list[str]:
    """Return source-backed required element paths (minOccurs > 0), stable order."""
    tree = load_tipo31_xsd_tree(xsd_path)
    ecf = _find_ecf_element(tree.getroot())
    required: list[str] = []
    optional: list[str] = []
    _walk_element_paths(ecf, "", required_out=required, optional_out=optional)
    return required


def extract_tipo31_optional_paths(
    xsd_path: Path | str | None = None,
) -> list[str]:
    """Return source-backed optional element paths (minOccurs = 0), stable order."""
    tree = load_tipo31_xsd_tree(xsd_path)
    ecf = _find_ecf_element(tree.getroot())
    required: list[str] = []
    optional: list[str] = []
    _walk_element_paths(ecf, "", required_out=required, optional_out=optional)
    return optional


def get_tipo31_xsd_structure_summary(
    xsd_path: Path | str | None = None,
) -> dict[str, Any]:
    """Compact structure summary for diagnostics and tests."""
    path = Path(xsd_path) if xsd_path is not None else DEFAULT_XSD_PATH
    root_name = extract_tipo31_root_name(path)
    top_level = extract_tipo31_top_level_sequence(path)
    required = extract_tipo31_required_paths(path)
    optional = extract_tipo31_optional_paths(path)
    return {
        "xsd_path": path.as_posix(),
        "root_name": root_name,
        "top_level_sequence": [p.get("name") for p in top_level],
        "top_level_particles": top_level,
        "required_path_count": len(required),
        "optional_path_count": len(optional),
        "required_paths": required,
        "optional_paths": optional,
        "signature_representation": "xs:any",
        "signature_named_in_formato_pdf": "Signature",
        "notes": (
            "Conservative local XSD extraction only. Does not claim DGII compliance "
            "and does not perform instance validation."
        ),
    }
