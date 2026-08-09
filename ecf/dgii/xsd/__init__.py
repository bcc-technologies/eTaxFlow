"""Local DGII XSD helpers (read-only, no network)."""

from .tipo_ecf_31_structure import (
    extract_tipo31_optional_paths,
    extract_tipo31_required_paths,
    extract_tipo31_root_name,
    extract_tipo31_top_level_sequence,
    get_tipo31_xsd_structure_summary,
    load_tipo31_xsd_tree,
)

__all__ = [
    "load_tipo31_xsd_tree",
    "extract_tipo31_root_name",
    "extract_tipo31_top_level_sequence",
    "extract_tipo31_required_paths",
    "extract_tipo31_optional_paths",
    "get_tipo31_xsd_structure_summary",
]
