"""Tipo e-CF 31 field catalog scaffold (non-production).

This module does not generate XML, validate XSD, sign, authenticate, or submit
to DGII. Catalog status remains pending until official sources are reviewed.
"""

from __future__ import annotations

from pathlib import Path

TIPO_ECF_31_CATALOG_STATUS = "SKELETON_PENDING_OFFICIAL_SOURCE_REVIEW"
TIPO_ECF_31_DOCUMENT_TYPE = "31"
TIPO_ECF_31_DOCUMENT_NAME = "Factura de Crédito Fiscal Electrónica"
TIPO_ECF_31_FUTURE_CATALOG = "TIPO_ECF_31"

# Obligation matrices are intentionally empty until Formato e-CF PDF review.
REQUIRED_FIELDS: list[str] = []
OPTIONAL_FIELDS: list[str] = []

# Conservative eTaxFlow availability notes (internal model fields only).
ETAXFLOW_AVAILABLE_FIELDS: list[str] = [
    "Invoice.internal_code",
    "Invoice.official_ncf",
    "Invoice.official_encf",
    "Invoice.fiscal_document_type_ref.code",
    "Invoice.issue_date",
    "Invoice.due_date",
    "Invoice.currency",
    "Invoice.subtotal",
    "Invoice.discount_total",
    "Invoice.tax_total",
    "Invoice.grand_total",
    "Organization.rnc",
    "Organization.legal_name",
    "Organization.commercial_name",
    "Organization.address",
    "Organization.phone",
    "Organization.email",
    "Organization.website",
    "Contact.rnc_or_id",
    "Contact.id_type",
    "Contact.legal_name",
    "Contact.commercial_name",
    "Contact.address",
    "Contact.phone",
    "Contact.email",
    "InvoiceLine.line_order",
    "InvoiceLine.description",
    "InvoiceLine.quantity",
    "InvoiceLine.unit_price",
    "InvoiceLine.discount_amount",
    "InvoiceLine.tax_rate",
    "InvoiceLine.tax_amount",
    "InvoiceLine.line_total",
    "InvoiceLine.item_code_snapshot",
    "InvoiceLine.item_name_snapshot",
    "InvoiceLine.unit_snapshot",
    "InvoiceLine.tax_rate_snapshot",
    "InvoiceLine.currency_snapshot",
]

ETAXFLOW_MISSING_FIELDS: list[str] = [
    "official eNCF sequence assignment workflow",
    "FechaVencimientoSecuencia",
    "TipoIngresos",
    "TipoPago / TablaFormasPago",
    "ActividadEconomica (issuer)",
    "buyer Municipio/Provincia",
    "IndicadorFacturacion",
    "IndicadorBienoServicio",
    "ITBIS rate buckets I1/I2/I3",
    "ImpuestosAdicionales model",
    "InformacionReferencia for NC/ND",
    "digital signature block",
]

OPEN_QUESTIONS: list[str] = [
    "Confirm Tipo 31 obligation matrix from Formato e-CF PDF vs XSD minOccurs.",
    "Decide mapping for NumeroFacturaInterna vs internal_code (must stay distinct from eNCF).",
    "Define ITBIS bucket mapping from a single Invoice.tax_total.",
    "Clarify buyer ID variants required for credito fiscal.",
    "Decide ownership of e-NCF sequence ranges and FechaVencimientoSecuencia.",
]

# Element names observed in local XSD only (not a compliance claim).
XSD_VISIBLE_CORE_ELEMENTS: list[str] = [
    "ECF",
    "Encabezado",
    "Version",
    "IdDoc",
    "TipoeCF",
    "eNCF",
    "FechaVencimientoSecuencia",
    "TipoIngresos",
    "TipoPago",
    "Emisor",
    "RNCEmisor",
    "RazonSocialEmisor",
    "Comprador",
    "RNCComprador",
    "RazonSocialComprador",
    "DetallesItems",
    "Item",
    "NumeroLinea",
    "NombreItem",
    "CantidadItem",
    "PrecioUnitarioItem",
    "Totales",
    "MontoTotal",
    "TotalITBIS",
]

_MARKDOWN_CATALOG = Path("docs/dgii/mapping/TIPO_ECF_31_FIELD_CATALOG.md")
_XSD_PATH = Path("docs/dgii/sources/e-CF_31_v1.0.xsd")


def tipo_ecf_31_xsd_present() -> bool:
    return _XSD_PATH.exists()


def tipo_ecf_31_markdown_present() -> bool:
    return _MARKDOWN_CATALOG.exists()


def tipo_ecf_31_catalog_summary() -> dict:
    return {
        "future_catalog": TIPO_ECF_31_FUTURE_CATALOG,
        "catalog_status": TIPO_ECF_31_CATALOG_STATUS,
        "document_type": TIPO_ECF_31_DOCUMENT_TYPE,
        "document_name": TIPO_ECF_31_DOCUMENT_NAME,
        "xsd_present": tipo_ecf_31_xsd_present(),
        "markdown_catalog_present": tipo_ecf_31_markdown_present(),
        "required_fields_count": len(REQUIRED_FIELDS),
        "optional_fields_count": len(OPTIONAL_FIELDS),
        "compliance_claim": "NOT_DGII_COMPLIANT",
    }
