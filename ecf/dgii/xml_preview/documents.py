"""Persist Tipo 31 XML structure previews as internal Document records.

Does not create ECFDocument, signed XML, TrackId, or call DGII.
"""

from __future__ import annotations

import hashlib

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile

from audit.models import AuditEvent
from documents.models import Document
from ecf.dgii.field_catalogs.tipo_ecf_31 import COMPLIANCE_CLAIM
from ecf.dgii.xml_preview.tipo_ecf_31_preview import build_tipo31_xml_preview
from invoicing.models import Invoice

PREVIEW_FILENAME_PREFIX = "tipo31-preview-"
PREVIEW_INTERNAL_CODE_PREFIX = "T31PREV"


def generate_tipo31_preview_document(
    invoice: Invoice,
    *,
    created_by=None,
    allow_demo_encf: bool = False,
    require_signing_placeholder: bool = True,
) -> tuple[Document, bool]:
    """Build Tipo 31 preview XML and save/reuse a Document.

    Returns (document, created) where created is False when an identical
    preview Document (same invoice + hash + filename) already exists.
    """
    if invoice is None:
        raise ValidationError("Invoice must be provided.")

    xml_bytes = build_tipo31_xml_preview(
        invoice,
        allow_demo_encf=allow_demo_encf,
        require_signing_placeholder=require_signing_placeholder,
    )
    sha256_hash = hashlib.sha256(xml_bytes).hexdigest()
    filename = f"{PREVIEW_FILENAME_PREFIX}{invoice.internal_code}.xml"

    existing = Document.objects.filter(
        related_invoice=invoice,
        document_kind="XML",
        source="GENERATED",
        original_filename=filename,
        sha256_hash=sha256_hash,
    ).first()
    if existing:
        return existing, False

    existing_docs = Document.objects.filter(
        related_invoice=invoice,
        document_kind="XML",
        source="GENERATED",
        original_filename=filename,
    ).count()
    version = existing_docs + 1
    internal_code = f"{PREVIEW_INTERNAL_CODE_PREFIX}-{invoice.internal_code}-{version:03d}"

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
        event_type="tipo31_xml_preview_generated",
        entity_type="Invoice",
        entity_id=invoice.pk,
        message=(
            f"Tipo 31 XML structure preview generated for invoice {invoice.internal_code}"
        ),
        metadata={
            "document_id": document.pk,
            "document_internal_code": document.internal_code,
            "sha256": document.sha256_hash,
            "allow_demo_encf": allow_demo_encf,
            "require_signing_placeholder": require_signing_placeholder,
            "compliance_status": COMPLIANCE_CLAIM,
            "preview_type": "STRUCTURE_PREVIEW_ONLY",
            "xml_signature": "NOT_IMPLEMENTED",
        },
    )
    return document, True
