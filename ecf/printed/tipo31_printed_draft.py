"""Generate a deterministic, non-production PDF representation for Tipo 31."""

from __future__ import annotations

import hashlib
from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile

from audit.models import AuditEvent
from documents.models import Document
from ecf.dgii.field_catalogs.tipo_ecf_31 import COMPLIANCE_CLAIM
from ecf.dgii.xml_preview.tipo_ecf_31_preview import (
    invoice_uses_demo_or_unauthorized_encf,
)
from invoicing.models import Invoice

PRINTED_FILENAME_PREFIX = "tipo31-printed-draft-"
PRINTED_INTERNAL_CODE_PREFIX = "T31PDF"
NON_PRODUCTION_DRAFT = "NON_PRODUCTION_DRAFT"


def _display_date(value: date | None) -> str:
    return value.isoformat() if value else ""


def _display_decimal(value: Decimal | None) -> str:
    return f"{Decimal(value or 0):.2f}"


def _pdf_escape(value: str) -> bytes:
    # Use PDF Latin-1-compatible text and avoid unsupported control characters.
    safe = "".join(char if 32 <= ord(char) <= 255 else "?" for char in str(value))
    return safe.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)").encode(
        "latin-1", errors="replace"
    )


def _content_stream(lines: list[str]) -> bytes:
    commands = [b"BT", b"/F1 11 Tf", b"50 790 Td"]
    for index, line in enumerate(lines):
        commands.append(b"(" + _pdf_escape(line) + b") Tj")
        if index != len(lines) - 1:
            commands.append(b"0 -16 Td")
    commands.append(b"ET")
    return b"\n".join(commands) + b"\n"


def _build_pdf(lines: list[str]) -> bytes:
    """Build a minimal deterministic PDF using only the standard PDF font."""
    page_size = 40
    page_lines = [lines[index : index + page_size] for index in range(0, len(lines), page_size)]
    if not page_lines:
        page_lines = [[]]

    object_specs: dict[int, bytes] = {
        1: b"<< /Type /Catalog /Pages 2 0 R >>",
        3: b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    }
    page_ids: list[int] = []
    next_object = 4
    for page in page_lines:
        page_id = next_object
        content_id = next_object + 1
        next_object += 2
        page_ids.append(page_id)
        content = _content_stream(page)
        object_specs[page_id] = (
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
            f"/Resources << /Font << /F1 3 0 R >> >> /Contents {content_id} 0 R >>"
        ).encode("ascii")
        object_specs[content_id] = (
            f"<< /Length {len(content)} >>\nstream\n".encode("ascii")
            + content
            + b"endstream"
        )
    kids = " ".join(f"{page_id} 0 R" for page_id in page_ids)
    object_specs[2] = f"<< /Type /Pages /Kids [{kids}] /Count {len(page_ids)} >>".encode(
        "ascii"
    )

    max_object = max(object_specs)
    output = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0] * (max_object + 1)
    for object_number in range(1, max_object + 1):
        object_body = object_specs[object_number]
        offsets[object_number] = len(output)
        output.extend(f"{object_number} 0 obj\n".encode("ascii"))
        output.extend(object_body)
        output.extend(b"\nendobj\n")
    xref_offset = len(output)
    output.extend(f"xref\n0 {max_object + 1}\n".encode("ascii"))
    output.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        output.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    output.extend(
        f"trailer\n<< /Size {max_object + 1} /Root 1 0 R >>\n"
        f"startxref\n{xref_offset}\n%%EOF\n".encode("ascii")
    )
    return bytes(output)


def _printed_lines(invoice: Invoice) -> list[str]:
    issuer = invoice.issuer
    customer = invoice.customer
    lines = [
        "eTaxFlow - TIPO 31",
        "REPRESENTACION IMPRESA LOCAL - BORRADOR NO PRODUCCION",
        "NOT_DGII_COMPLIANT - NO APROBADO PARA DGII",
        "",
        f"Numero interno: {invoice.internal_code}",
        f"Tipo e-CF: {getattr(invoice.fiscal_document_type_ref, 'code', '31')}",
        f"eNCF sintetico/local: {invoice.official_encf or '(none)'}",
        f"Fecha emision: {_display_date(invoice.issue_date)}",
        f"Fecha vencimiento: {_display_date(invoice.due_date)}",
        f"Moneda: {invoice.currency}",
        "",
        f"Emisor: {getattr(issuer, 'legal_name', '')}",
        f"RNC emisor: {getattr(issuer, 'rnc', '')}",
        f"Direccion emisor: {getattr(issuer, 'address', '')}",
        f"Comprador: {getattr(customer, 'legal_name', '')}",
        f"RNC/ID comprador: {getattr(customer, 'rnc_or_id', '')}",
        f"Direccion comprador: {getattr(customer, 'address', '')}",
        "",
        "DETALLE",
    ]
    for line in invoice.lines.all().order_by("line_order", "id"):
        description = (line.description or line.item_name_snapshot or "Item")[:70]
        lines.append(
            f"{line.line_order}. {description} | Cant {line.quantity} | "
            f"Precio {_display_decimal(line.unit_price)} | Total {_display_decimal(line.line_total)}"
        )
    lines.extend(
        [
            "",
            f"Subtotal: {_display_decimal(invoice.subtotal)} {invoice.currency}",
            f"ITBIS/impuesto: {_display_decimal(invoice.tax_total)} {invoice.currency}",
            f"Descuento: {_display_decimal(invoice.discount_total)} {invoice.currency}",
            f"Total: {_display_decimal(invoice.grand_total)} {invoice.currency}",
            "",
            "Firma digital: NO IMPLEMENTADA; no se incluye XMLDSig.",
            "QR/codigo de seguridad: OMITIDO; no existe un valor fuente aprobado.",
            "Este PDF es un NON_PRODUCTION_DRAFT para uso interno solamente.",
        ]
    )
    return lines


def build_tipo31_printed_draft_pdf(
    invoice: Invoice,
    *,
    allow_demo_encf: bool = False,
) -> bytes:
    if invoice is None:
        raise ValidationError("Invoice must be provided.")
    if getattr(invoice.fiscal_document_type_ref, "code", None) != "31":
        raise ValidationError("Printed Tipo 31 draft requires fiscal_document_type_ref.code == '31'.")
    if not invoice.official_encf:
        raise ValidationError("Printed Tipo 31 draft requires official_encf.")
    if invoice_uses_demo_or_unauthorized_encf(invoice) and not allow_demo_encf:
        raise ValidationError(
            "Printed Tipo 31 draft requires allow_demo_encf=True for demo/non-authorized eNCF."
        )
    return _build_pdf(_printed_lines(invoice))


def generate_tipo31_printed_draft_document(
    invoice: Invoice,
    *,
    created_by=None,
    allow_demo_encf: bool = False,
) -> tuple[Document, bool]:
    """Build, store, link, and reuse a non-production Tipo 31 PDF draft."""
    pdf_bytes = build_tipo31_printed_draft_pdf(
        invoice,
        allow_demo_encf=allow_demo_encf,
    )
    sha256_hash = hashlib.sha256(pdf_bytes).hexdigest()
    filename = f"{PRINTED_FILENAME_PREFIX}{invoice.internal_code}.pdf"
    existing = Document.objects.filter(
        related_invoice=invoice,
        document_kind="PDF",
        source="GENERATED",
        original_filename=filename,
        sha256_hash=sha256_hash,
    ).first()
    if existing:
        return existing, False

    version = Document.objects.filter(
        related_invoice=invoice,
        document_kind="PDF",
        source="GENERATED",
        original_filename=filename,
    ).count() + 1
    document = Document(
        internal_code=f"{PRINTED_INTERNAL_CODE_PREFIX}-{invoice.internal_code}-{version:03d}",
        document_direction=invoice.invoice_direction,
        document_kind="PDF",
        source="GENERATED",
        original_filename=filename,
        issuer=invoice.issuer,
        related_contact=invoice.customer,
        related_invoice=invoice,
        status="STORED",
        created_by=created_by,
        mime_type="application/pdf",
    )
    document.file.save(filename, ContentFile(pdf_bytes), save=False)
    document.save()

    AuditEvent.objects.create(
        actor=created_by,
        event_type="tipo31_printed_draft_generated",
        entity_type="Invoice",
        entity_id=invoice.pk,
        message=(
            f"Tipo 31 non-production printed draft generated for invoice "
            f"{invoice.internal_code}"
        ),
        metadata={
            "document_id": document.pk,
            "document_internal_code": document.internal_code,
            "sha256": document.sha256_hash,
            "file_size": document.file_size,
            "representation_status": NON_PRODUCTION_DRAFT,
            "compliance_status": COMPLIANCE_CLAIM,
            "dgii_approval_claim": False,
            "signature_status": "NOT_IMPLEMENTED",
            "qr_security_code": "OMITTED_NOT_SOURCE_BACKED",
            "dgii_submission_allowed": False,
            "dgii_track_id": None,
        },
    )
    return document, True
