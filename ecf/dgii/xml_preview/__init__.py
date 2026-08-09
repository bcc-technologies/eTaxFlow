"""Non-production Tipo e-CF 31 XML structure preview.

NOT_DGII_COMPLIANT. No XMLDSig, no certificates, no DGII submission.
"""

from .documents import generate_tipo31_preview_document
from .tipo_ecf_31_preview import build_tipo31_xml_preview

__all__ = [
    "build_tipo31_xml_preview",
    "generate_tipo31_preview_document",
]
