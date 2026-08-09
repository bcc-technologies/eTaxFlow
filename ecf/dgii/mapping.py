"""Pure Invoice -> DGII concept mapping report (no XML, no side effects)."""

from __future__ import annotations

from decimal import Decimal

from django.core.exceptions import ObjectDoesNotExist, ValidationError

from ecf.dgii.field_catalogs.tipo_ecf_31 import (
    TIPO_ECF_31_CATALOG_STATUS,
    TIPO_ECF_31_DOCUMENT_TYPE,
    TIPO_ECF_31_FUTURE_CATALOG,
    get_tipo_ecf_31_catalog_metrics,
)
from ecf.dgii.inventory_status import source_inventory_status
from ecf.dgii.types import (
    DGIIDocumentTypeMapping,
    DGIIFieldMapping,
    DGIIIssueSeverity,
    DGIIMappingReport,
    DGIIMappingStatus,
)
from ecf.dgii.validators import is_blank, issue
from invoicing.models import Invoice


KNOWN_TIPOE_CF = {
    "31": "Factura de Crédito Fiscal Electrónica (concept)",
    "32": "Factura de Consumo Electrónica (concept)",
    "33": "Nota de Débito Electrónica (concept)",
    "34": "Nota de Crédito Electrónica (concept)",
    "41": "Compras Electrónico (concept)",
    "43": "Gastos Menores Electrónico (concept)",
    "44": "Regímenes Especiales Electrónico (concept)",
    "45": "Gubernamental Electrónico (concept)",
    "46": "Exportaciones Electrónico (concept)",
    "47": "Pagos al Exterior Electrónico (concept)",
}


def _preview(value, *, max_len: int = 80) -> str | None:
    if value is None:
        return None
    text = str(value)
    if len(text) > max_len:
        return text[: max_len - 3] + "..."
    return text


def _field(
    area: str,
    internal_field: str,
    dgii_concept: str,
    value,
    *,
    notes: str = "",
    present: bool | None = None,
) -> DGIIFieldMapping:
    if present is None:
        if isinstance(value, bool):
            present = value
        elif isinstance(value, Decimal):
            present = True
        elif isinstance(value, (int, float)):
            present = True
        else:
            present = not is_blank(value)
    return DGIIFieldMapping(
        area=area,
        internal_field=internal_field,
        dgii_concept=dgii_concept,
        present=present,
        value_preview=_preview(value) if present else None,
        notes=notes,
    )


def build_invoice_dgii_mapping_report(invoice: Invoice) -> DGIIMappingReport:
    """Inspect an Invoice and return a read-only DGII concept mapping report.

    Does not create XML, Document, or ECFDocument. Does not mutate invoice.
    Does not call DGII.
    """
    if invoice is None:
        raise ValidationError("Invoice must be provided.")

    # Capture immutable snapshots before any read-only traversal.
    before = {
        "internal_code": invoice.internal_code,
        "official_ncf": invoice.official_ncf,
        "official_encf": invoice.official_encf,
        "lifecycle_status": invoice.lifecycle_status,
        "updated_at": invoice.updated_at,
        "subtotal": invoice.subtotal,
        "tax_total": invoice.tax_total,
        "grand_total": invoice.grand_total,
    }

    issues = []
    fiscal_ref = getattr(invoice, "fiscal_document_type_ref", None)
    fiscal_code = None
    fiscal_name = None
    if fiscal_ref is not None:
        fiscal_code = fiscal_ref.code
        fiscal_name = fiscal_ref.name
    elif invoice.fiscal_document_type:
        fiscal_code = invoice.fiscal_document_type

    tipoe_concept = KNOWN_TIPOE_CF.get(str(fiscal_code)) if fiscal_code else None
    fiscal_mapping = DGIIDocumentTypeMapping(
        internal_code=fiscal_code,
        internal_name=fiscal_name,
        dgii_tipoe_cf_concept=tipoe_concept,
        mapped=bool(fiscal_code and tipoe_concept),
        notes=(
            "Mapped to known TipoeCF concept catalog placeholder; "
            "official XSD/format review still required."
            if tipoe_concept
            else "No FiscalDocumentType mapping available."
        ),
    )
    if not fiscal_mapping.mapped:
        issues.append(
            issue(
                "MISSING_FISCAL_DOCUMENT_TYPE",
                "Invoice lacks a mapped fiscal document type (TipoeCF concept).",
                severity=DGIIIssueSeverity.BLOCKING,
                area="header",
            )
        )

    issuer = getattr(invoice, "issuer", None)
    issuer_fields = [
        _field("issuer", "issuer.rnc", "Emisor RNC", getattr(issuer, "rnc", None)),
        _field("issuer", "issuer.legal_name", "Emisor Nombre/Razón Social", getattr(issuer, "legal_name", None)),
        _field("issuer", "issuer.commercial_name", "Emisor Nombre Comercial", getattr(issuer, "commercial_name", None)),
        _field("issuer", "issuer.address", "Emisor Dirección", getattr(issuer, "address", None)),
        _field("issuer", "issuer.phone", "Emisor Teléfono", getattr(issuer, "phone", None)),
        _field("issuer", "issuer.email", "Emisor Correo", getattr(issuer, "email", None)),
    ]
    if is_blank(getattr(issuer, "rnc", None)):
        issues.append(
            issue(
                "MISSING_ISSUER_RNC",
                "Issuer RNC is missing; required for any future e-CF Emisor block.",
                severity=DGIIIssueSeverity.BLOCKING,
                area="issuer",
            )
        )
    if is_blank(getattr(issuer, "legal_name", None)):
        issues.append(
            issue(
                "MISSING_ISSUER_LEGAL_NAME",
                "Issuer legal name is missing.",
                severity=DGIIIssueSeverity.BLOCKING,
                area="issuer",
            )
        )

    customer = getattr(invoice, "customer", None)
    customer_fields = [
        _field("customer", "customer.rnc_or_id", "Comprador RNC/Cédula/ID", getattr(customer, "rnc_or_id", None)),
        _field("customer", "customer.id_type", "Comprador Tipo ID", getattr(customer, "id_type", None)),
        _field("customer", "customer.legal_name", "Comprador Nombre/Razón Social", getattr(customer, "legal_name", None)),
        _field("customer", "customer.commercial_name", "Comprador Nombre Comercial", getattr(customer, "commercial_name", None)),
        _field("customer", "customer.address", "Comprador Dirección", getattr(customer, "address", None)),
        _field("customer", "customer.email", "Comprador Correo", getattr(customer, "email", None)),
    ]
    if is_blank(getattr(customer, "rnc_or_id", None)):
        issues.append(
            issue(
                "MISSING_CUSTOMER_RNC_OR_ID",
                "Customer RNC/ID is missing; required for credito fiscal style e-CF buyer identification.",
                severity=DGIIIssueSeverity.BLOCKING,
                area="customer",
            )
        )
    if is_blank(getattr(customer, "legal_name", None)):
        issues.append(
            issue(
                "MISSING_CUSTOMER_LEGAL_NAME",
                "Customer legal name is missing.",
                severity=DGIIIssueSeverity.BLOCKING,
                area="customer",
            )
        )

    lines = list(invoice.lines.all().order_by("line_order", "pk"))
    line_fields = [
        _field("lines", "lines.count", "Detalle items count", len(lines)),
    ]
    if not lines:
        issues.append(
            issue(
                "MISSING_INVOICE_LINES",
                "Invoice has no lines; future e-CF draft cannot be built.",
                severity=DGIIIssueSeverity.BLOCKING,
                area="lines",
            )
        )
    else:
        # Aggregate snapshot availability across lines (report-level, not per-XML).
        def any_line_attr(attr):
            return any(not is_blank(getattr(line, attr, None)) for line in lines)

        line_fields.extend(
            [
                _field("lines", "lines[].description", "Item descripción", any_line_attr("description")),
                _field("lines", "lines[].quantity", "Item cantidad", True),
                _field("lines", "lines[].unit_price", "Item precio unitario", True),
                _field("lines", "lines[].tax_amount", "Item monto ITBIS/impuesto", True),
                _field("lines", "lines[].line_total", "Item monto total", True),
                _field(
                    "lines",
                    "lines[].item_code_snapshot",
                    "Item código (snapshot)",
                    any_line_attr("item_code_snapshot"),
                ),
                _field(
                    "lines",
                    "lines[].item_name_snapshot",
                    "Item nombre (snapshot)",
                    any_line_attr("item_name_snapshot"),
                ),
                _field(
                    "lines",
                    "lines[].unit_snapshot",
                    "Item unidad (snapshot)",
                    any_line_attr("unit_snapshot"),
                ),
                _field(
                    "lines",
                    "lines[].tax_rate_snapshot",
                    "Item tasa impuesto (snapshot)",
                    any_line_attr("tax_rate_snapshot"),
                ),
                _field(
                    "lines",
                    "lines[].currency_snapshot",
                    "Item moneda (snapshot)",
                    any_line_attr("currency_snapshot"),
                ),
            ]
        )
        if not any_line_attr("item_code_snapshot"):
            issues.append(
                issue(
                    "MISSING_LINE_ITEM_CODE_SNAPSHOT",
                    "No line item_code_snapshot values found.",
                    severity=DGIIIssueSeverity.WARNING,
                    area="lines",
                )
            )

    totals_fields = [
        _field("totals", "subtotal", "Monto gravado/subtotal (internal)", invoice.subtotal),
        _field("totals", "discount_total", "Total descuentos (internal)", invoice.discount_total),
        _field("totals", "tax_total", "Total ITBIS/impuestos (internal)", invoice.tax_total),
        _field("totals", "grand_total", "Monto total (internal)", invoice.grand_total),
        _field("totals", "currency", "Moneda", invoice.currency),
        _field("totals", "issue_date", "Fecha emisión", invoice.issue_date),
    ]
    if invoice.grand_total is None or invoice.grand_total <= Decimal("0.00"):
        issues.append(
            issue(
                "NON_POSITIVE_GRAND_TOTAL",
                "Grand total is missing or not positive.",
                severity=DGIIIssueSeverity.BLOCKING,
                area="totals",
            )
        )

    official_ncf = invoice.official_ncf
    official_encf = invoice.official_encf
    income_type = getattr(invoice, "income_type", None)
    payment_type = getattr(invoice, "payment_type", None)
    identity_fields = [
        _field(
            "identity",
            "internal_code",
            "Internal vault code (NOT DGII e-NCF)",
            invoice.internal_code,
            notes="eTaxFlow internal identifier only.",
        ),
        _field(
            "identity",
            "official_ncf",
            "Official NCF (legacy/fiscal number if any)",
            official_ncf,
            notes="Distinct from internal_code and official_encf.",
        ),
        _field(
            "identity",
            "official_encf",
            "Official e-NCF / TipoeCF sequence (future DGII eNCF)",
            official_encf,
            notes="Distinct from internal_code and official_ncf. Not auto-generated.",
        ),
        _field(
            "identity",
            "sequence_expiration_date",
            "FechaVencimientoSecuencia (internal)",
            getattr(invoice, "sequence_expiration_date", None),
            notes="Nullable model field; demo values are not authorized DGII sequence ranges.",
        ),
        _field(
            "identity",
            "income_type",
            "TipoIngresos (internal FiscalIncomeType)",
            getattr(income_type, "code", None),
            notes=(
                f"{getattr(income_type, 'name', '')}".strip()
                or "Preliminary internal catalog mapping only."
            ),
        ),
        _field(
            "identity",
            "payment_type",
            "TipoPago (internal PaymentType)",
            getattr(payment_type, "code", None),
            notes=(
                f"{getattr(payment_type, 'name', '')}".strip()
                or "Preliminary internal catalog mapping only. Not a payments module."
            ),
        ),
    ]

    lines_have_billing = bool(lines) and all(
        getattr(line, "billing_indicator_id", None) for line in lines
    )
    line_fields.append(
        _field(
            "lines",
            "lines[].billing_indicator",
            "IndicadorFacturacion (internal BillingIndicator)",
            lines_have_billing,
            notes="Required Tipo 31 line indicator; catalog codes 0-4 are preliminary.",
        )
    )

    signature_dt = None
    signing_status = None
    signing_mode = None
    has_signed_xml = False
    try:
        ecf_doc = invoice.ecf_document
    except ObjectDoesNotExist:
        ecf_doc = None
    if ecf_doc is not None:
        signature_dt = getattr(ecf_doc, "signature_datetime", None)
        signing_status = getattr(ecf_doc, "signing_status", None)
        signing_mode = getattr(ecf_doc, "signing_mode", None)
        has_signed_xml = bool(getattr(ecf_doc, "xml_signed_file", None))
    identity_fields.append(
        _field(
            "identity",
            "ecf_document.signature_datetime",
            "FechaHoraFirma placeholder (NOT real signing)",
            signature_dt,
            notes=(
                f"signing_status={signing_status!r}, signing_mode={signing_mode!r}. "
                "Placeholder only; not a real digital signature timestamp."
            ),
        )
    )
    identity_fields.append(
        _field(
            "identity",
            "ecf_document.xml_signed_file",
            "Signature / signed XML artifact (future)",
            has_signed_xml,
            notes="Real Signature remains missing until a future XMLDSig/signing service exists.",
        )
    )
    issues.append(
        issue(
            "IDENTITY_FIELDS_DISTINGUISHED",
            (
                f"internal_code={invoice.internal_code!r} is separate from "
                f"official_ncf={official_ncf!r} and official_encf={official_encf!r}."
            ),
            severity=DGIIIssueSeverity.INFO,
            area="identity",
        )
    )
    if is_blank(official_encf):
        issues.append(
            issue(
                "MISSING_OFFICIAL_ENCF",
                "official_encf is empty; future DGII emission will require an assigned e-NCF.",
                severity=DGIIIssueSeverity.WARNING,
                area="identity",
            )
        )
    else:
        from fiscal.models import ENCFSequenceRange

        demo_encf = False
        encf_text = str(official_encf)
        if encf_text.startswith("DEMO-") or encf_text.startswith("DEMO"):
            demo_encf = True
        ranges = ENCFSequenceRange.objects.filter(
            issuer_id=getattr(invoice, "issuer_id", None),
            fiscal_document_type_id=getattr(invoice, "fiscal_document_type_ref_id", None),
            is_active=True,
        )
        for seq_range in ranges:
            if encf_text.startswith(seq_range.prefix) and seq_range.is_demo_or_unauthorized:
                demo_encf = True
                break
        if demo_encf:
            issues.append(
                issue(
                    "DEMO_OR_UNAUTHORIZED_ENCF",
                    (
                        f"official_encf={official_encf!r} appears to come from a "
                        "demo/non-authorized local sequence range. "
                        "NOT DGII-authorized and NOT_DGII_COMPLIANT."
                    ),
                    severity=DGIIIssueSeverity.WARNING,
                    area="identity",
                )
            )

    if ecf_doc is not None and getattr(ecf_doc, "signing_status", None) == "SIGNING_PLACEHOLDER":
        issues.append(
            issue(
                "SIGNING_PLACEHOLDER_ONLY",
                (
                    "ECFDocument.signing_status=SIGNING_PLACEHOLDER: FechaHoraFirma may be "
                    "represented via signature_datetime, but no real digital signature "
                    "(Signature/XMLDSig) was created. NOT_DGII_COMPLIANT."
                ),
                severity=DGIIIssueSeverity.WARNING,
                area="signing",
            )
        )

    future_catalog = None
    catalog_status = None
    source_files_reviewed = None
    available_field_count = None
    partially_available_field_count = None
    derived_field_count = None
    missing_required_field_count = None
    missing_required_fields = None
    inventory = source_inventory_status()
    if str(fiscal_code) == TIPO_ECF_31_DOCUMENT_TYPE:
        future_catalog = TIPO_ECF_31_FUTURE_CATALOG
        catalog_status = TIPO_ECF_31_CATALOG_STATUS
        metrics = get_tipo_ecf_31_catalog_metrics(invoice=invoice)
        source_files_reviewed = metrics["source_files_reviewed"]
        available_field_count = metrics["available_field_count"]
        partially_available_field_count = metrics["partially_available_field_count"]
        derived_field_count = metrics["derived_field_count"]
        missing_required_field_count = metrics["missing_required_field_count"]
        missing_required_fields = metrics["missing_required_fields"]
        if catalog_status == "SKELETON_PENDING_OFFICIAL_SOURCE_REVIEW":
            issues.append(
                issue(
                    "TIPO_ECF_31_CATALOG_PENDING_SOURCE_REVIEW",
                    (
                        "Tipo e-CF 31 field catalog is still "
                        "SKELETON_PENDING_OFFICIAL_SOURCE_REVIEW; "
                        "do not treat mapping as DGII-compliant."
                    ),
                    severity=DGIIIssueSeverity.WARNING,
                    area="catalog",
                )
            )
        elif catalog_status == "REVIEWED_FIELD_MATRIX_NOT_XML_COMPLIANT":
            issues.append(
                issue(
                    "TIPO_ECF_31_FIELD_MATRIX_REVIEWED_NOT_COMPLIANT",
                    (
                        "Tipo e-CF 31 obligation matrix was reviewed from local "
                        "Formato/XSD sources, but this is still "
                        "NOT_DGII_COMPLIANT (no official XML/signing/submission)."
                    ),
                    severity=DGIIIssueSeverity.WARNING,
                    area="catalog",
                )
            )
            if missing_required_field_count:
                names = ", ".join(item["field"] for item in missing_required_fields[:12])
                issues.append(
                    issue(
                        "TIPO_ECF_31_REQUIRED_FIELDS_MISSING_IN_MODEL",
                        (
                            f"{missing_required_field_count} required Tipo 31 catalog "
                            f"field(s) are missing in eTaxFlow models/workflows "
                            f"(e.g. {names}). Does not by itself block future "
                            f"internal draft readiness."
                        ),
                        severity=DGIIIssueSeverity.WARNING,
                        area="catalog",
                    )
                )

    blocking = [i for i in issues if i.severity == DGIIIssueSeverity.BLOCKING]
    enough = len(blocking) == 0
    if enough:
        status = DGIIMappingStatus.READY_FOR_FUTURE_DRAFT
    elif fiscal_mapping.mapped or len(lines) > 0:
        status = DGIIMappingStatus.PARTIAL
    else:
        status = DGIIMappingStatus.BLOCKED

    report = DGIIMappingReport(
        invoice_id=invoice.pk,
        internal_code=invoice.internal_code,
        official_ncf=official_ncf,
        official_encf=official_encf,
        official_ncf_present=not is_blank(official_ncf),
        official_encf_present=not is_blank(official_encf),
        fiscal_document_type=fiscal_mapping,
        issuer_fields=issuer_fields,
        customer_fields=customer_fields,
        line_fields=line_fields,
        totals_fields=totals_fields,
        identity_fields=identity_fields,
        issues=issues,
        status=status,
        enough_internal_data_for_future_ecf_draft=enough,
        future_catalog=future_catalog,
        catalog_status=catalog_status,
        source_inventory_status={
            "summary": inventory["summary"],
            "collected_count": inventory["collected_count"],
            "missing_count": inventory["missing_count"],
            "expected_count": inventory["expected_count"],
        },
        source_files_reviewed=source_files_reviewed,
        available_field_count=available_field_count,
        partially_available_field_count=partially_available_field_count,
        derived_field_count=derived_field_count,
        missing_required_field_count=missing_required_field_count,
        missing_required_fields=missing_required_fields,
    )

    # Guard: report generation must not mutate invoice in-memory or in DB.
    after = {
        "internal_code": invoice.internal_code,
        "official_ncf": invoice.official_ncf,
        "official_encf": invoice.official_encf,
        "lifecycle_status": invoice.lifecycle_status,
        "updated_at": invoice.updated_at,
        "subtotal": invoice.subtotal,
        "tax_total": invoice.tax_total,
        "grand_total": invoice.grand_total,
    }
    if before != after:
        raise RuntimeError("build_invoice_dgii_mapping_report mutated invoice state.")
    if invoice.pk:
        db_row = (
            Invoice.objects.filter(pk=invoice.pk)
            .values(
                "internal_code",
                "official_ncf",
                "official_encf",
                "lifecycle_status",
                "updated_at",
                "subtotal",
                "tax_total",
                "grand_total",
            )
            .get()
        )
        if db_row != before:
            raise RuntimeError("build_invoice_dgii_mapping_report mutated persisted invoice state.")

    return report
