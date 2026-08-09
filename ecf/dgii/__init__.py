"""DGII e-CF mapping groundwork (Phase 005).

This package maps normalized Invoice data to future DGII e-CF concepts.
It does not generate DGII-compliant XML, sign documents, authenticate,
or send anything to DGII.
"""

from ecf.dgii.mapping import build_invoice_dgii_mapping_report
from ecf.dgii.types import DGIIMappingReport

__all__ = [
    "DGIIMappingReport",
    "build_invoice_dgii_mapping_report",
]
