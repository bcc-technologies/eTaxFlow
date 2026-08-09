"""Schema-aligned unsigned Tipo e-CF 31 XML draft builder.

Uses local XSD / reviewed field matrix tags and order only.
Omits Signature (XSD xs:any / Formato <Signature>). NOT_DGII_COMPLIANT.
Does not emit XMLDSig, certificates, TrackId, or DGII submission artifacts.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from decimal import Decimal
from xml.etree.ElementTree import Element, SubElement, tostring

from django.core.exceptions import ObjectDoesNotExist, ValidationError

from ecf.dgii.field_catalogs.tipo_ecf_31 import (
    COMPLIANCE_CLAIM,
    TIPO_ECF_31_CATALOG_STATUS,
    TIPO_ECF_31_DOCUMENT_TYPE,
    get_tipo_ecf_31_catalog_metrics,
)
from ecf.dgii.mapping import build_invoice_dgii_mapping_report
from ecf.dgii.types import DGIIIssueSeverity
from ecf.dgii.xml_preview.tipo_ecf_31_preview import (
    invoice_uses_demo_or_unauthorized_encf,
)
from ecf.dgii.xsd.tipo_ecf_31_structure import (
    DEFAULT_XSD_PATH,
    extract_tipo31_root_name,
    extract_tipo31_top_level_sequence,
    get_tipo31_xsd_structure_summary,
)
from invoicing.models import Invoice


class Tipo31UnsignedDraftError(ValidationError):
    """Raised when an unsigned Tipo 31 draft cannot be built."""


@dataclass
class Tipo31UnsignedDraftDiagnostics:
    compliance_status: str = COMPLIANCE_CLAIM
    draft_type: str = "UNSIGNED_SCHEMA_ALIGNED_DRAFT"
    source_xsd: str = DEFAULT_XSD_PATH.as_posix()
    source_catalog_status: str = TIPO_ECF_31_CATALOG_STATUS
    missing_required_fields: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    uses_demo_encf: bool = False
    signing_status: str | None = None
    signature_present: bool = False
    dgii_submission_allowed: bool = False
    root_name: str = "ECF"
    top_level_sequence: list[str] = field(default_factory=list)
    available_field_count: int | None = None
    local_xsd_validation_available: bool = False
    local_xsd_validation_expected_to_fail: bool = True
    expected_failure_reason: str = (
        "Signature missing / unsigned draft"
    )
    notes: str = (
        "Unsigned schema-aligned local draft only. Signature omitted. "
        "Not valid for DGII submission."
    )

    def to_dict(self) -> dict:
        return asdict(self)


def _format_decimal(value: Decimal, places: int = 2) -> str:
    return f"{Decimal(value):.{places}f}"


def _format_decimal_unit_price(value: Decimal) -> str:
    # XSD allows up to 4 fraction digits; keep trailing trim of zeros after 2+.
    quantized = Decimal(value).quantize(Decimal("0.0001"))
    text = f"{quantized:.4f}".rstrip("0").rstrip(".")
    if "." not in text:
        text = f"{text}.00"
    elif len(text.split(".")[1]) == 1:
        text = f"{text}0"
    return text


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


def _truncate(text: str, max_len: int) -> str:
    if text is None:
        return ""
    value = str(text)
    if len(value) <= max_len:
        return value
    return value[:max_len]


def _indicador_bien_o_servicio(line) -> str:
    """Derive IndicadorBienoServicio: 1=PRODUCT, 2=SERVICE (XSD enums)."""
    product = getattr(line, "product_service", None)
    item_type = getattr(product, "item_type", None) if product is not None else None
    if item_type == "PRODUCT":
        return "1"
    if item_type == "SERVICE":
        return "2"
    # XSD requires the element; prefer SERVICE when unlinked (catalog-derived default).
    return "2"


def validate_tipo31_unsigned_draft_invoice(
    invoice: Invoice,
    *,
    allow_demo_encf: bool = False,
    require_signing_placeholder: bool = True,
) -> None:
    """Validate invoice prerequisites for unsigned Tipo 31 draft generation."""
    errors: list[str] = []

    if invoice is None:
        raise Tipo31UnsignedDraftError("Invoice must be provided.")

    fiscal_ref = getattr(invoice, "fiscal_document_type_ref", None)
    if fiscal_ref is None:
        errors.append("Invoice must have fiscal_document_type_ref.")
    elif str(fiscal_ref.code) != TIPO_ECF_31_DOCUMENT_TYPE:
        errors.append(
            "Tipo 31 unsigned draft requires fiscal_document_type_ref.code == "
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
        errors.append("Invoice must have official_encf before unsigned Tipo 31 draft.")

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
        raise Tipo31UnsignedDraftError(errors)


def build_tipo31_unsigned_draft_diagnostics(
    invoice: Invoice,
    *,
    allow_demo_encf: bool = False,
    require_signing_placeholder: bool = True,
) -> Tipo31UnsignedDraftDiagnostics:
    """Compute diagnostics for an unsigned draft (validates prerequisites)."""
    validate_tipo31_unsigned_draft_invoice(
        invoice,
        allow_demo_encf=allow_demo_encf,
        require_signing_placeholder=require_signing_placeholder,
    )

    summary = get_tipo31_xsd_structure_summary()
    metrics = get_tipo_ecf_31_catalog_metrics(invoice=invoice)
    report = build_invoice_dgii_mapping_report(invoice)

    try:
        ecf_doc = invoice.ecf_document
    except ObjectDoesNotExist:
        ecf_doc = None

    missing = [item["field"] for item in (metrics.get("missing_required_fields") or [])]
    if "Signature" not in missing:
        missing.append("Signature")

    warning_codes = sorted(
        {
            i.code
            for i in report.issues
            if i.severity == DGIIIssueSeverity.WARNING and i.code
        }
    )
    uses_demo = invoice_uses_demo_or_unauthorized_encf(invoice)
    if uses_demo and "DEMO_OR_UNAUTHORIZED_ENCF" not in warning_codes:
        warning_codes.append("DEMO_OR_UNAUTHORIZED_ENCF")
        warning_codes.sort()
    if "UNSIGNED_DRAFT_SIGNATURE_OMITTED" not in warning_codes:
        warning_codes.append("UNSIGNED_DRAFT_SIGNATURE_OMITTED")
        warning_codes.sort()

    # Lazy import avoids circular import with xsd.tipo31_unsigned_validation.
    from ecf.dgii.xsd.validation import lxml_available

    return Tipo31UnsignedDraftDiagnostics(
        compliance_status=COMPLIANCE_CLAIM,
        draft_type="UNSIGNED_SCHEMA_ALIGNED_DRAFT",
        source_xsd=summary["xsd_path"],
        source_catalog_status=TIPO_ECF_31_CATALOG_STATUS,
        missing_required_fields=missing,
        warnings=warning_codes,
        uses_demo_encf=uses_demo,
        signing_status=getattr(ecf_doc, "signing_status", None) if ecf_doc else None,
        signature_present=False,
        dgii_submission_allowed=False,
        root_name=summary["root_name"],
        top_level_sequence=list(summary["top_level_sequence"]),
        available_field_count=metrics.get("available_field_count"),
        local_xsd_validation_available=lxml_available() and DEFAULT_XSD_PATH.is_file(),
        local_xsd_validation_expected_to_fail=True,
        expected_failure_reason="Signature missing / unsigned draft",
    )


def build_tipo31_unsigned_xml_draft(
    invoice: Invoice,
    *,
    allow_demo_encf: bool = False,
    require_signing_placeholder: bool = True,
) -> bytes:
    """Build schema-aligned unsigned Tipo 31 XML draft bytes.

    Root is the XSD element ``ECF``. Signature (xs:any / Formato Signature) is
    omitted intentionally; diagnostics report it missing.
    """
    validate_tipo31_unsigned_draft_invoice(
        invoice,
        allow_demo_encf=allow_demo_encf,
        require_signing_placeholder=require_signing_placeholder,
    )

    root_name = extract_tipo31_root_name()
    top_level = extract_tipo31_top_level_sequence()
    expected_top = [p.get("name") for p in top_level if p.get("name")]
    # Sanity: builder emits Encabezado, DetallesItems, FechaHoraFirma in XSD order.
    for required_name in ("Encabezado", "DetallesItems", "FechaHoraFirma"):
        if required_name not in expected_top:
            raise Tipo31UnsignedDraftError(
                f"Local XSD top-level sequence missing expected {required_name!r}."
            )

    try:
        ecf_doc = invoice.ecf_document
    except ObjectDoesNotExist:
        ecf_doc = None
    signature_dt = getattr(ecf_doc, "signature_datetime", None) if ecf_doc else None

    # Schema-shaped root: no preview-only compliance attributes.
    root = Element(root_name)

    encabezado = SubElement(root, "Encabezado")
    _append_text(encabezado, "Version", "1.0")

    id_doc = SubElement(encabezado, "IdDoc")
    _append_text(id_doc, "TipoeCF", TIPO_ECF_31_DOCUMENT_TYPE)
    _append_text(id_doc, "eNCF", invoice.official_encf)
    _append_text(
        id_doc,
        "FechaVencimientoSecuencia",
        _format_date_dd_mm_yyyy(invoice.sequence_expiration_date),
    )
    _append_text(id_doc, "TipoIngresos", invoice.income_type.code)
    _append_text(id_doc, "TipoPago", invoice.payment_type.code)
    if invoice.due_date is not None:
        _append_text(
            id_doc,
            "FechaLimitePago",
            _format_date_dd_mm_yyyy(invoice.due_date),
        )

    issuer = invoice.issuer
    emisor = SubElement(encabezado, "Emisor")
    _append_text(emisor, "RNCEmisor", getattr(issuer, "rnc", ""))
    _append_text(emisor, "RazonSocialEmisor", getattr(issuer, "legal_name", ""))
    commercial = (getattr(issuer, "commercial_name", None) or "").strip()
    if commercial:
        _append_text(emisor, "NombreComercial", _truncate(commercial, 150))
    _append_text(
        emisor,
        "DireccionEmisor",
        _truncate(getattr(issuer, "address", "") or "", 100),
    )
    email = (getattr(issuer, "email", None) or "").strip()
    if email:
        _append_text(emisor, "CorreoEmisor", email)
    internal_code = invoice.internal_code or ""
    if 0 < len(internal_code) <= 20:
        _append_text(emisor, "NumeroFacturaInterna", internal_code)
    _append_text(emisor, "FechaEmision", _format_date_dd_mm_yyyy(invoice.issue_date))

    customer = invoice.customer
    comprador = SubElement(encabezado, "Comprador")
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
    customer_email = (getattr(customer, "email", None) or "").strip() if customer else ""
    if customer_email:
        _append_text(comprador, "CorreoComprador", customer_email)
    customer_address = (
        (getattr(customer, "address", None) or "").strip() if customer else ""
    )
    if customer_address:
        _append_text(
            comprador,
            "DireccionComprador",
            _truncate(customer_address, 100),
        )

    totales = SubElement(encabezado, "Totales")
    # Optional Totales members emitted only when we have mapped source values.
    if invoice.subtotal is not None:
        _append_decimal(totales, "MontoGravadoTotal", invoice.subtotal)
    if invoice.tax_total is not None:
        _append_decimal(totales, "TotalITBIS", invoice.tax_total)
    _append_decimal(totales, "MontoTotal", invoice.grand_total)
    if invoice.grand_total is not None:
        _append_decimal(totales, "ValorPagar", invoice.grand_total)

    detalles = SubElement(root, "DetallesItems")
    for line in invoice.lines.all().order_by("line_order", "id"):
        item = SubElement(detalles, "Item")
        _append_text(item, "NumeroLinea", line.line_order)
        _append_text(
            item,
            "IndicadorFacturacion",
            line.billing_indicator.code if line.billing_indicator_id else "",
        )
        _append_text(
            item,
            "NombreItem",
            _truncate(line.item_name_snapshot or "", 80),
        )
        _append_text(item, "IndicadorBienoServicio", _indicador_bien_o_servicio(line))
        if line.description:
            _append_text(item, "DescripcionItem", _truncate(line.description, 1000))
        _append_decimal(item, "CantidadItem", line.quantity)
        unit_price_el = SubElement(item, "PrecioUnitarioItem")
        unit_price_el.text = _format_decimal_unit_price(line.unit_price)
        if line.discount_amount and line.discount_amount > Decimal("0.00"):
            _append_decimal(item, "DescuentoMonto", line.discount_amount)
        _append_decimal(item, "MontoItem", line.line_total)

    # Optional InformacionReferencia omitted for ordinary Tipo 31 sales (catalog N/A).
    if signature_dt is not None:
        _append_text(
            root,
            "FechaHoraFirma",
            _format_datetime_dd_mm_yyyy_hh_mm_ss(signature_dt),
        )
    else:
        # XSD requires FechaHoraFirma; emit empty only if placeholder not required.
        # When require_signing_placeholder=True validation already ensured datetime.
        _append_text(root, "FechaHoraFirma", "")

    # Signature / xs:any intentionally omitted — report via diagnostics only.
    return tostring(root, encoding="utf-8", method="xml")
