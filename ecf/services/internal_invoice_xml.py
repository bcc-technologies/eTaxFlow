from decimal import Decimal
from xml.etree.ElementTree import Element, SubElement, tostring

from django.core.exceptions import ValidationError


def _format_decimal(value: Decimal, places: int = 2) -> str:
    return f"{value:.{places}f}"


def _safe_text(value) -> str:
    if value is None:
        return ""
    return str(value)


def _append_text(parent: Element, tag: str, value, default_empty: bool = True):
    if value is None:
        if default_empty:
            child = SubElement(parent, tag)
            child.text = ""
        return
    child = SubElement(parent, tag)
    child.text = _safe_text(value)


def _append_decimal(parent: Element, tag: str, value: Decimal, places: int = 2):
    child = SubElement(parent, tag)
    child.text = _format_decimal(value, places)


def build_internal_invoice_xml(invoice) -> str:
    if invoice is None:
        raise ValidationError("Invoice must be provided.")
    if not invoice.issuer:
        raise ValidationError("Invoice issuer is required.")
    if invoice.invoice_direction == "OUTBOUND" and not invoice.customer:
        raise ValidationError("Outbound invoices require a customer.")
    if not invoice.lines.exists():
        raise ValidationError("Invoice must have at least one line.")
    if invoice.grand_total <= Decimal("0.00"):
        raise ValidationError("Invoice must have a positive grand total.")
    if not invoice.fiscal_document_type_ref:
        raise ValidationError("Invoice must have a fiscal document type reference.")

    for line in invoice.lines.all().order_by("line_order", "id"):
        if not line.item_name_snapshot:
            raise ValidationError(f"Invoice line {line.pk} is missing item_name_snapshot.")
        if not line.unit_snapshot:
            raise ValidationError(f"Invoice line {line.pk} is missing unit_snapshot.")
        if not line.tax_rate_snapshot:
            raise ValidationError(f"Invoice line {line.pk} is missing tax_rate_snapshot.")
        if not line.currency_snapshot:
            raise ValidationError(f"Invoice line {line.pk} is missing currency_snapshot.")

    root = Element("InternalInvoiceDraft", {
        "schema_name": "ETAXFLOW_INTERNAL_INVOICE",
        "schema_version": "1.0",
        "purpose": "INTERNAL_DRAFT_ONLY",
        "dgii_compliance": "NOT_DGII_COMPLIANT",
    })

    metadata = SubElement(root, "Metadata")
    _append_text(metadata, "SchemaName", "ETAXFLOW_INTERNAL_INVOICE")
    _append_text(metadata, "SchemaVersion", "1.0")
    _append_text(metadata, "Purpose", "INTERNAL_DRAFT_ONLY")
    _append_text(metadata, "DGIICompliance", "NOT_DGII_COMPLIANT")

    header = SubElement(root, "InvoiceHeader")
    _append_text(header, "InternalCode", invoice.internal_code)
    _append_text(header, "InvoiceDirection", invoice.invoice_direction)
    _append_text(header, "LifecycleStatus", invoice.lifecycle_status)
    _append_text(header, "Currency", invoice.currency)
    issue_date_value = invoice.issue_date.isoformat() if hasattr(invoice.issue_date, "isoformat") else str(invoice.issue_date)
    due_date_value = invoice.due_date.isoformat() if getattr(invoice.due_date, "isoformat", None) else (str(invoice.due_date) if invoice.due_date else "")
    _append_text(header, "IssueDate", issue_date_value)
    _append_text(header, "DueDate", due_date_value)
    _append_text(header, "FiscalDocumentTypeCode", invoice.fiscal_document_type_ref.code)
    _append_text(header, "FiscalDocumentTypeName", invoice.fiscal_document_type_ref.name)
    _append_text(header, "OfficialNCF", invoice.official_ncf or "")
    _append_text(header, "OfficialENCF", invoice.official_encf or "")

    issuer = SubElement(root, "Issuer")
    _append_text(issuer, "LegalName", invoice.issuer.legal_name)
    _append_text(issuer, "CommercialName", invoice.issuer.commercial_name)
    _append_text(issuer, "RNC", getattr(invoice.issuer, "rnc", ""))
    _append_text(issuer, "Address", getattr(invoice.issuer, "address", ""))
    _append_text(issuer, "Phone", getattr(invoice.issuer, "phone", ""))
    _append_text(issuer, "Email", getattr(invoice.issuer, "email", ""))

    customer = SubElement(root, "Customer")
    _append_text(customer, "LegalName", invoice.customer.legal_name if invoice.customer else "")
    _append_text(customer, "CommercialName", invoice.customer.commercial_name if invoice.customer else "")
    _append_text(customer, "RNCOrID", getattr(invoice.customer, "rnc_or_id", "") if invoice.customer else "")
    _append_text(customer, "IDType", getattr(invoice.customer, "id_type", "") if invoice.customer else "")
    _append_text(customer, "Address", getattr(invoice.customer, "address", "") if invoice.customer else "")
    _append_text(customer, "Phone", getattr(invoice.customer, "phone", "") if invoice.customer else "")
    _append_text(customer, "Email", getattr(invoice.customer, "email", "") if invoice.customer else "")

    lines_element = SubElement(root, "Lines")
    for line in invoice.lines.all().order_by("line_order", "id"):
        line_el = SubElement(lines_element, "Line")
        _append_text(line_el, "LineOrder", line.line_order)
        _append_text(line_el, "ProductServiceCode", line.product_service.code if line.product_service else "")
        _append_text(line_el, "ItemCodeSnapshot", line.item_code_snapshot or "")
        _append_text(line_el, "ItemNameSnapshot", line.item_name_snapshot)
        _append_text(line_el, "UnitSnapshot", line.unit_snapshot)
        _append_decimal(line_el, "Quantity", line.quantity)
        _append_decimal(line_el, "UnitPrice", line.unit_price)
        _append_decimal(line_el, "DiscountAmount", line.discount_amount)
        _append_decimal(line_el, "TaxRate", line.tax_rate, places=2)
        _append_text(line_el, "TaxRateSnapshot", line.tax_rate_snapshot)
        _append_decimal(line_el, "TaxAmount", line.tax_amount)
        _append_decimal(line_el, "LineTotal", line.line_total)

    totals = SubElement(root, "Totals")
    _append_decimal(totals, "Subtotal", invoice.subtotal)
    _append_decimal(totals, "DiscountTotal", invoice.discount_total)
    _append_decimal(totals, "TaxTotal", invoice.tax_total)
    _append_decimal(totals, "GrandTotal", invoice.grand_total)

    notice = SubElement(root, "ComplianceNotice")
    notice.text = "This XML is an internal normalized draft and is not a DGII e-CF document."

    xml_bytes = tostring(root, encoding="utf-8", method="xml")
    return xml_bytes.decode("utf-8")
