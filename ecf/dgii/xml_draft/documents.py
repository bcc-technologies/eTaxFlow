"""Persist schema-aligned unsigned Tipo 31 drafts as internal Documents.

Does not create ECFDocument, signed XML, TrackId, or call DGII.
"""

from __future__ import annotations

import hashlib

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile

from audit.models import AuditEvent
from documents.models import Document
from ecf.dgii.field_catalogs.tipo_ecf_31 import COMPLIANCE_CLAIM
from ecf.dgii.xml_draft.tipo_ecf_31_unsigned import (
    build_tipo31_unsigned_draft_diagnostics,
    build_tipo31_unsigned_xml_draft,
)
from invoicing.models import Invoice

DRAFT_FILENAME_PREFIX = "tipo31-unsigned-draft-"
DRAFT_INTERNAL_CODE_PREFIX = "T31USGN"


def generate_tipo31_unsigned_draft_document(
    invoice: Invoice,
    *,
    created_by=None,
    allow_demo_encf: bool = False,
    require_signing_placeholder: bool = True,
) -> tuple[Document, bool]:
    """Build unsigned Tipo 31 draft XML and save/reuse a Document.

    Returns (document, created).
    """
    if invoice is None:
        raise ValidationError("Invoice must be provided.")

    xml_bytes = build_tipo31_unsigned_xml_draft(
        invoice,
        allow_demo_encf=allow_demo_encf,
        require_signing_placeholder=require_signing_placeholder,
    )
    diagnostics = build_tipo31_unsigned_draft_diagnostics(
        invoice,
        allow_demo_encf=allow_demo_encf,
        require_signing_placeholder=require_signing_placeholder,
    )
    sha256_hash = hashlib.sha256(xml_bytes).hexdigest()
    filename = f"{DRAFT_FILENAME_PREFIX}{invoice.internal_code}.xml"

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
    internal_code = f"{DRAFT_INTERNAL_CODE_PREFIX}-{invoice.internal_code}-{version:03d}"

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
        event_type="tipo31_unsigned_draft_generated",
        entity_type="Invoice",
        entity_id=invoice.pk,
        message=(
            f"Tipo 31 unsigned schema-aligned draft generated for "
            f"invoice {invoice.internal_code}"
        ),
        metadata={
            "document_id": document.pk,
            "document_internal_code": document.internal_code,
            "sha256": document.sha256_hash,
            "allow_demo_encf": allow_demo_encf,
            "require_signing_placeholder": require_signing_placeholder,
            "compliance_status": COMPLIANCE_CLAIM,
            "draft_type": diagnostics.draft_type,
            "missing_required_fields": diagnostics.missing_required_fields,
            "signature_present": False,
            "dgii_submission_allowed": False,
        },
    )
    return document, True
