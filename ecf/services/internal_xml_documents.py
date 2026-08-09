import hashlib

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile

from audit.models import AuditEvent
from documents.models import Document
from .internal_invoice_xml import build_internal_invoice_xml


def generate_internal_xml_document(invoice, created_by=None):
    if invoice is None:
        raise ValidationError("Invoice must be provided.")

    xml_string = build_internal_invoice_xml(invoice)
    xml_bytes = xml_string.encode("utf-8")
    sha256_hash = hashlib.sha256(xml_bytes).hexdigest()

    existing = Document.objects.filter(
        related_invoice=invoice,
        document_kind="XML",
        source="GENERATED",
        sha256_hash=sha256_hash,
    ).first()
    if existing:
        return existing, False

    existing_docs = Document.objects.filter(
        related_invoice=invoice,
        document_kind="XML",
        source="GENERATED",
    ).count()
    version = existing_docs + 1
    internal_code = f"INTXML-{invoice.internal_code}-{version:03d}"
    filename = f"internal-invoice-draft-{invoice.internal_code}.xml"

    document = Document(
        internal_code=internal_code,
        document_direction=invoice.invoice_direction,
        document_kind="XML",
        source="GENERATED",
        original_filename=filename,
        issuer=invoice.issuer,
        related_contact=invoice.customer,
        related_invoice=invoice,
        status="STORED",
        created_by=created_by,
        mime_type="application/xml",
    )
    document.file.save(filename, ContentFile(xml_bytes), save=False)
    document.save()

    AuditEvent.objects.create(
        actor=created_by,
        event_type="internal_xml_draft_generated",
        entity_type="Invoice",
        entity_id=invoice.pk,
        message=f"Internal XML draft generated for invoice {invoice.internal_code}",
        metadata={"document_id": document.pk, "sha256": document.sha256_hash},
    )
    return document, True
