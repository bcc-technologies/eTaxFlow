"""Deterministic non-production Tipo e-CF 31 XML structure preview.

Does not emit production DGII e-CF XML, XMLDSig, certificates, TrackId,
or fake Signature content. Always marked NOT_DGII_COMPLIANT.
"""

from __future__ import annotations

from decimal import Decimal
from xml.etree.ElementTree import Element, SubElement, tostring

from django.core.exceptions import ObjectDoesNotExist, ValidationError

from ecf.dgii.field_catalogs.tipo_ecf_31 import (
    COMPLIANCE_CLAIM,
    SOURCE_FILES_REVIEWED,
    TIPO_ECF_31_CATALOG_STATUS,
    TIPO_ECF_31_DOCUMENT_TYPE,
    get_tipo_ecf_31_catalog_metrics,
)
from ecf.dgii.mapping import build_invoice_dgii_mapping_report
from ecf.dgii.types import DGIIIssueSeverity
from fiscal.models import ENCFSequenceRange
from invoicing.models import Invoice


class Tipo31XmlPreviewError(ValidationError):
    """Raised when Tipo 31 XML preview cannot be built."""


def _format_decimal(value: Decimal, places: int = 2) -> str:
    return f"{Decimal(value):.{places}f}"


def _safe_text(value) -> str:
    if value is None:
        return ""
    return str(value)


def _append_text(parent: Element, tag: str, value) -> Element:
    child = SubElement(parent, tag)
    child.text = _safe_text(value)
    return child


def _append_decimal(parent: Element, tag: str, value: Decimal, places: int = 2) -> Element:
    child = SubElement(parent, tag)
    child.text = _format_decimal(value, places)
    return child


def _format_date_dd_mm_yyyy(value) -> str:
    if value is None:
        return ""
    if hasattr(value, "strftime"):
        return value.strftime("%d-%m-%Y")
    return str(value)


def _format_datetime_dd_mm_yyyy_hh_mm_ss(value) -> str:
    if value is None:
        return ""
    if hasattr(value, "strftime"):
        return value.strftime("%d-%m-%Y %H:%M:%S")
    return str(value)


def invoice_uses_demo_or_unauthorized_encf(invoice: Invoice) -> bool:
    """Return True when official_encf appears demo/non-authorized."""
    official_encf = getattr(invoice, "official_encf", None)
    if not official_encf:
        return False
    encf_text = str(official_encf)
    if encf_text.startswith("DEMO-") or encf_text.startswith("DEMO"):
        return True
    ranges = ENCFSequenceRange.objects.filter(
        issuer_id=getattr(invoice, "issuer_id", None),
        fiscal_document_type_id=getattr(invoice, "fiscal_document_type_ref_id", None),
        is_active=True,
    )
    for seq_range in ranges:
        if encf_text.startswith(seq_range.prefix) and seq_range.is_demo_or_unauthorized:
            return True
    return False


def validate_tipo31_xml_preview_invoice(
    invoice: Invoice,
    *,
    allow_demo_encf: bool = False,
    require_signing_placeholder: bool = True,
) -> None:
    """Validate invoice prerequisites for Tipo 31 structure preview."""
    errors: list[str] = []

    if invoice is None:
        raise Tipo31XmlPreviewError("Invoice must be provided.")

    fiscal_ref = getattr(invoice, "fiscal_document_type_ref", None)
    if fiscal_ref is None:
        errors.append("Invoice must have fiscal_document_type_ref.")
    elif str(fiscal_ref.code) != TIPO_ECF_31_DOCUMENT_TYPE:
        errors.append(
            "Tipo 31 XML preview requires fiscal_document_type_ref.code == "
            f"{TIPO_ECF_31_DOCUMENT_TYPE!r} (got {fiscal_ref.code!r})."
        )

    if not getattr(invoice, "issuer_id", None):
        errors.append("Invoice must have an issuer.")

    if getattr(invoice, "invoice_direction", None) == "OUTBOUND" and not getattr(
        invoice, "customer_id", None
    ):
        errors.append("Outbound invoices require a customer.")

    lines = list(invoice.lines.all().order_by("line_order", "id"))
    if not lines:
        errors.append("Invoice must have at least one line.")

    grand_total = getattr(invoice, "grand_total", None)
    if grand_total is None or grand_total <= Decimal("0.00"):
        errors.append("Invoice must have a positive grand_total.")

    if not getattr(invoice, "official_encf", None):
        errors.append("Invoice must have official_encf before Tipo 31 XML preview.")

    if not getattr(invoice, "sequence_expiration_date", None):
        errors.append("Invoice must have sequence_expiration_date.")

    if not getattr(invoice, "income_type_id", None):
        errors.append("Invoice must have income_type.")

    if not getattr(invoice, "payment_type_id", None):
        errors.append("Invoice must have payment_type.")

    for line in lines:
        if not getattr(line, "billing_indicator_id", None):
            errors.append(f"Invoice line {line.pk} is missing billing_indicator.")
        if not line.item_name_snapshot:
            errors.append(f"Invoice line {line.pk} is missing item_name_snapshot.")
        if not line.unit_snapshot:
            errors.append(f"Invoice line {line.pk} is missing unit_snapshot.")
        if not line.tax_rate_snapshot:
            errors.append(f"Invoice line {line.pk} is missing tax_rate_snapshot.")
        if not line.currency_snapshot:
            errors.append(f"Invoice line {line.pk} is missing currency_snapshot.")

    if invoice_uses_demo_or_unauthorized_encf(invoice) and not allow_demo_encf:
        errors.append(
            "Demo/non-authorized eNCF requires allow_demo_encf=True. "
            "These values are NOT DGII-authorized."
        )

    if require_signing_placeholder:
        try:
            ecf_doc = invoice.ecf_document
        except ObjectDoesNotExist:
            ecf_doc = None
        if (
            ecf_doc is None
            or getattr(ecf_doc, "signing_status", None) != "SIGNING_PLACEHOLDER"
            or not getattr(ecf_doc, "signature_datetime", None)
        ):
            errors.append(
                "Signing placeholder is required: ECFDocument must exist with "
                "signing_status=SIGNING_PLACEHOLDER and signature_datetime set."
            )

    if errors:
        raise Tipo31XmlPreviewError(errors)


def build_tipo31_xml_preview(
    invoice: Invoice,
    *,
    allow_demo_encf: bool = False,
    require_signing_placeholder: bool = True,
) -> bytes:
    """Build deterministic Tipo 31 structure-preview XML bytes.

    Signature remains missing for compliance purposes and is represented only
    as a diagnostic SignaturePreview section (not a DGII Signature / XMLDSig).
    """
    validate_tipo31_xml_preview_invoice(
        invoice,
        allow_demo_encf=allow_demo_encf,
        require_signing_placeholder=require_signing_placeholder,
    )

    metrics = get_tipo_ecf_31_catalog_metrics(invoice=invoice)
    report = build_invoice_dgii_mapping_report(invoice)

    try:
        ecf_doc = invoice.ecf_document
    except ObjectDoesNotExist:
        ecf_doc = None

    signature_dt = getattr(ecf_doc, "signature_datetime", None) if ecf_doc else None
    signing_status = getattr(ecf_doc, "signing_status", None) if ecf_doc else None

    warning_codes = sorted(
        {
            i.code
            for i in report.issues
            if i.severity == DGIIIssueSeverity.WARNING and i.code
        }
    )
    missing_required = [
        item["field"] for item in (metrics.get("missing_required_fields") or [])
    ]
    # Signature must always appear as a missing required compliance field in preview.
    if "Signature" not in missing_required:
        missing_required.append("Signature")

    root = Element(
        "ETaxFlowTipo31EcfPreview",
        {
            "document_type": TIPO_ECF_31_DOCUMENT_TYPE,
            "preview_type": "STRUCTURE_PREVIEW_ONLY",
            "dgii_compliance": COMPLIANCE_CLAIM,
            "production_submission": "FORBIDDEN",
            "xml_signature": "NOT_IMPLEMENTED",
            "signature_field": "MISSING",
            "schema_basis": "TIPO_ECF_31_FIELD_MATRIX",
            "catalog_status": TIPO_ECF_31_CATALOG_STATUS,
        },
    )

    metadata = SubElement(root, "PreviewMetadata")
    _append_text(metadata, "ComplianceStatus", COMPLIANCE_CLAIM)
    _append_text(
        metadata,
        "PreviewPurpose",
        "Non-production deterministic structure preview of mapped Tipo 31 fields. "
        "Not a DGII e-CF submission document.",
    )
    _append_text(metadata, "CatalogStatus", TIPO_ECF_31_CATALOG_STATUS)

    sources_el = SubElement(metadata, "SourceFilesReviewed")
    for name in SOURCE_FILES_REVIEWED:
        _append_text(sources_el, "SourceFile", name)

    missing_el = SubElement(metadata, "MissingRequiredFields")
    for field_name in missing_required:
        _append_text(missing_el, "Field", field_name)

    warnings_el = SubElement(metadata, "Warnings")
    for code in warning_codes:
        _append_text(warnings_el, "Warning", code)
    if invoice_uses_demo_or_unauthorized_encf(invoice):
        # Ensure DEMO warning is visible even if mapping severity changes later.
        if "DEMO_OR_UNAUTHORIZED_ENCF" not in warning_codes:
            _append_text(warnings_el, "Warning", "DEMO_OR_UNAUTHORIZED_ENCF")

    encabezado = SubElement(root, "EncabezadoPreview")
    _append_text(encabezado, "Version", "1.0")
    _append_text(encabezado, "TipoeCF", TIPO_ECF_31_DOCUMENT_TYPE)
    _append_text(encabezado, "eNCF", invoice.official_encf)
    _append_text(
        encabezado,
        "FechaVencimientoSecuencia",
        _format_date_dd_mm_yyyy(invoice.sequence_expiration_date),
    )
    _append_text(
        encabezado,
        "TipoIngresos",
        getattr(invoice.income_type, "code", "") if invoice.income_type_id else "",
    )
    _append_text(
        encabezado,
        "TipoPago",
        getattr(invoice.payment_type, "code", "") if invoice.payment_type_id else "",
    )
    _append_text(
        encabezado,
        "FechaLimitePago",
        _format_date_dd_mm_yyyy(invoice.due_date) if invoice.due_date else "",
    )
    _append_text(encabezado, "NumeroFacturaInterna", invoice.internal_code)
    _append_text(encabezado, "Currency", invoice.currency)

    issuer = invoice.issuer
    emisor = SubElement(root, "EmisorPreview")
    _append_text(emisor, "RNCEmisor", getattr(issuer, "rnc", ""))
    _append_text(emisor, "RazonSocialEmisor", getattr(issuer, "legal_name", ""))
    _append_text(emisor, "NombreComercial", getattr(issuer, "commercial_name", ""))
    _append_text(emisor, "DireccionEmisor", getattr(issuer, "address", ""))
    _append_text(emisor, "TelefonoEmisor", getattr(issuer, "phone", ""))
    _append_text(emisor, "CorreoEmisor", getattr(issuer, "email", ""))
    _append_text(emisor, "FechaEmision", _format_date_dd_mm_yyyy(invoice.issue_date))

    customer = invoice.customer
    comprador = SubElement(root, "CompradorPreview")
    _append_text(
        comprador,
        "RNCComprador",
        getattr(customer, "rnc_or_id", "") if customer else "",
    )
    _append_text(
        comprador,
        "RazonSocialComprador",
        getattr(customer, "legal_name", "") if customer else "",
    )
    _append_text(
        comprador,
        "CorreoComprador",
        getattr(customer, "email", "") if customer else "",
    )
    _append_text(
        comprador,
        "DireccionComprador",
        getattr(customer, "address", "") if customer else "",
    )
    _append_text(
        comprador,
        "IDType",
        getattr(customer, "id_type", "") if customer else "",
    )

    totales = SubElement(root, "TotalesPreview")
    _append_decimal(totales, "Subtotal", invoice.subtotal)
    _append_decimal(totales, "DiscountTotal", invoice.discount_total)
    _append_decimal(totales, "TotalITBIS", invoice.tax_total)
    _append_decimal(totales, "MontoTotal", invoice.grand_total)

    detalles = SubElement(root, "DetallesItemsPreview")
    for line in invoice.lines.all().order_by("line_order", "id"):
        item = SubElement(detalles, "ItemPreview")
        _append_text(item, "NumeroLinea", line.line_order)
        _append_text(item, "CodigoItem", line.item_code_snapshot or "")
        _append_text(item, "NombreItem", line.item_name_snapshot or "")
        _append_text(item, "DescripcionItem", line.description or "")
        _append_text(
            item,
            "IndicadorFacturacion",
            getattr(line.billing_indicator, "code", "")
            if line.billing_indicator_id
            else "",
        )
        _append_text(item, "UnidadMedida", line.unit_snapshot or "")
        _append_decimal(item, "CantidadItem", line.quantity)
        _append_decimal(item, "PrecioUnitarioItem", line.unit_price)
        _append_decimal(item, "DescuentoMonto", line.discount_amount)
        _append_text(item, "TaxRateSnapshot", line.tax_rate_snapshot or "")
        _append_decimal(item, "TaxAmount", line.tax_amount)
        _append_decimal(item, "MontoItem", line.line_total)
        _append_text(item, "CurrencySnapshot", line.currency_snapshot or "")

    fecha_firma = SubElement(root, "FechaHoraFirmaPreview")
    if signature_dt is not None:
        _append_text(
            fecha_firma,
            "FechaHoraFirma",
            _format_datetime_dd_mm_yyyy_hh_mm_ss(signature_dt),
        )
        _append_text(fecha_firma, "Source", "ECFDocument.signature_datetime")
        _append_text(fecha_firma, "SigningStatus", signing_status or "")
        _append_text(
            fecha_firma,
            "Note",
            "Placeholder FechaHoraFirma only. Not a real digital signature timestamp.",
        )
    else:
        _append_text(fecha_firma, "FechaHoraFirma", "")
        _append_text(fecha_firma, "Status", "MISSING")
        _append_text(
            fecha_firma,
            "Note",
            "No ECFDocument.signature_datetime available for this preview.",
        )

    signature_preview = SubElement(root, "SignaturePreview")
    _append_text(signature_preview, "Status", "MISSING")
    _append_text(signature_preview, "Implemented", "false")
    _append_text(signature_preview, "XMLDSig", "NOT_IMPLEMENTED")
    _append_text(signature_preview, "DGIISignaturePresent", "false")
    _append_text(
        signature_preview,
        "Note",
        "Signature is a required DGII compliance field but is not implemented and "
        "is not present. This SignaturePreview section is diagnostic only and is "
        "NOT a DGII Signature element. No XMLDSig namespace or signature value is emitted.",
    )

    diagnostics = SubElement(root, "MappingDiagnostics")
    _append_text(
        diagnostics,
        "AvailableFieldCount",
        metrics.get("available_field_count", 0),
    )
    _append_text(
        diagnostics,
        "PartiallyAvailableFieldCount",
        metrics.get("partially_available_field_count", 0),
    )
    _append_text(
        diagnostics,
        "DerivedFieldCount",
        metrics.get("derived_field_count", 0),
    )
    diag_missing = SubElement(diagnostics, "MissingRequiredFields")
    for field_name in missing_required:
        _append_text(diag_missing, "Field", field_name)
    diag_warnings = SubElement(diagnostics, "Warnings")
    for code in warning_codes:
        _append_text(diag_warnings, "Warning", code)
    if invoice_uses_demo_or_unauthorized_encf(invoice):
        if "DEMO_OR_UNAUTHORIZED_ENCF" not in warning_codes:
            _append_text(diag_warnings, "Warning", "DEMO_OR_UNAUTHORIZED_ENCF")
    _append_text(diagnostics, "ComplianceClaim", COMPLIANCE_CLAIM)
    _append_text(diagnostics, "MappingStatus", report.status.value if hasattr(report.status, "value") else str(report.status))

    return tostring(root, encoding="utf-8", method="xml")
