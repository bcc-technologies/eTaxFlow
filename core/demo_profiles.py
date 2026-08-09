"""Synthetic demo profiles for local XSD facet-safe feedback.

All values are synthetic and NOT DGII-authorized.
They exist only to reduce avoidable local XSD facet noise during unsigned
draft validation experiments. They do NOT imply DGII compliance.
"""

from __future__ import annotations

# RNCValidationType: pattern [0-9]{11}|[0-9]{9}
# Use 9-digit synthetic issuer RNC (not a verified real BCC RNC).
DEMO_XSD_FACET_ISSUER_RNC = "131000001"
DEMO_XSD_FACET_CUSTOMER_RNC = "123456789"  # already 9-digit synthetic
DEMO_XSD_FACET_SUPPLIER_RNC = "987654321"  # already 9-digit synthetic

# Legacy seed issuer RNC that fails local XSD (10 digits).
LEGACY_DEMO_ISSUER_RNCS = frozenset({"1310000000"})

DEMO_ISSUER_LEGAL_NAME = "BARREIRO CASANOVA CASTILLO TECHNOLOGIES, S.R.L."

# eNCFValidationType: pattern ([a-z0-9A-Z]{13}); minLength=13; maxLength=13
# TipoeCF-style synthetic prefix E31 + 10 zero-padded digits.
DEMO_XSD_FACET_ENCF_PREFIX = "E31"
DEMO_XSD_FACET_ENCF_PAD_WIDTH = 10
DEMO_XSD_FACET_ENCF_START = 9000000001
DEMO_XSD_FACET_ENCF_END = 9000009999
DEMO_XSD_FACET_ENCF_SOURCE = "XSD_FACET_DEMO"
DEMO_XSD_FACET_ENCF_ENVIRONMENT = "DEV"

DEMO_XSD_FACET_NOTES = (
    "SYNTHETIC XSD-FACET DEMO ONLY — NOT DGII-authorized, not requested from DGII, "
    "not a production eNCF range. Values exist solely to satisfy local "
    "e-CF_31_v1.0.xsd length/pattern facets during unsigned draft lab validation. "
    "NOT_DGII_COMPLIANT."
)
