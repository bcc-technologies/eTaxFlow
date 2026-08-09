"""Non-production signing placeholder / FechaHoraFirma stub.

Does not perform XMLDSig, store certificates/private keys, submit to DGII,
or create TrackId values.
"""

from __future__ import annotations

from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import transaction
from django.utils import timezone

from audit.models import AuditEvent
from ecf.models import ECFDocument
from invoicing.models import Invoice


class SigningPlaceholderError(ValidationError):
    """Raised when signing placeholder preparation cannot proceed."""


def attempt_real_signing(*args, **kwargs):
    """Explicit blocker for real digital signing.

    Reserved for a future phase. Never stores certificates or private keys.
    """
    raise NotImplementedError(
        "Real digital signing is not implemented. "
        "No private keys or certificates are stored by eTaxFlow."
    )


def _require_invoice_ready(invoice: Invoice) -> None:
    if invoice is None:
        raise SigningPlaceholderError("Invoice must be provided.")
    if not getattr(invoice, "official_encf", None):
        raise SigningPlaceholderError(
            "Invoice must have official_encf before preparing a signing placeholder."
        )
    if not getattr(invoice, "sequence_expiration_date", None):
        raise SigningPlaceholderError(
            "Invoice must have sequence_expiration_date before preparing a signing placeholder."
        )
    if not getattr(invoice, "fiscal_document_type_ref_id", None):
        raise SigningPlaceholderError(
            "Invoice must have fiscal_document_type_ref before preparing a signing placeholder."
        )


def preview_signing_placeholder(invoice: Invoice) -> dict:
    """Validate and describe what prepare_signing_placeholder would do."""
    _require_invoice_ready(invoice)
    existing = None
    try:
        existing = invoice.ecf_document
    except ObjectDoesNotExist:
        existing = None
    return {
        "invoice_id": invoice.pk,
        "internal_code": invoice.internal_code,
        "official_encf": invoice.official_encf,
        "sequence_expiration_date": invoice.sequence_expiration_date,
        "ecf_document_id": existing.pk if existing else None,
        "would_create_ecf_document": existing is None,
        "environment": existing.environment if existing else "DEV",
        "signing_status": "SIGNING_PLACEHOLDER",
        "signing_mode": "PLACEHOLDER_ONLY",
        "would_set_signature_datetime": True,
        "would_write_xml_signed_file": False,
        "would_set_track_id": False,
        "note": (
            "Local FechaHoraFirma placeholder only. No real digital signature, "
            "certificates, or private keys."
        ),
    }


@transaction.atomic
def prepare_signing_placeholder(
    invoice: Invoice,
    *,
    actor=None,
    note: str | None = None,
) -> ECFDocument:
    """Create/update ECFDocument in SIGNING_PLACEHOLDER mode.

    Sets signature_datetime for FechaHoraFirma mapping preview only.
    Does not write signed XML, certificates, private keys, or TrackId.
    """
    _require_invoice_ready(invoice)
    invoice = Invoice.objects.select_for_update().get(pk=invoice.pk)
    _require_invoice_ready(invoice)

    now = timezone.now()
    default_note = (
        "Local signing placeholder only. No real digital signature was created. "
        "No certificates or private keys are stored. NOT_DGII_COMPLIANT."
    )
    placeholder_note = (note or "").strip() or default_note

    try:
        ecf = invoice.ecf_document
        created = False
    except ObjectDoesNotExist:
        ecf = ECFDocument(invoice=invoice, environment="DEV")
        created = True

    if not ecf.environment:
        ecf.environment = "DEV"
    if not ecf.ecf_type:
        ecf.ecf_type = getattr(invoice.fiscal_document_type_ref, "code", "") or "DEMO"

    # Never mark as SIGNED in this phase.
    ecf.signing_status = "SIGNING_PLACEHOLDER"
    ecf.signing_mode = "PLACEHOLDER_ONLY"
    ecf.signature_datetime = now
    ecf.signing_attempted_at = now
    ecf.signing_completed_at = None
    ecf.signed_by = actor
    ecf.signature_placeholder_note = placeholder_note
    # Explicitly leave real signing artifacts empty.
    ecf.signature_digest_algorithm = None
    ecf.signature_method = None
    ecf.signature_reference_uri = None
    # Do not touch xml_signed_file / dgii_track_id.
    ecf.save()

    AuditEvent.objects.create(
        actor=actor,
        event_type="signing_placeholder_prepared",
        entity_type="Invoice",
        entity_id=invoice.pk,
        message=(
            f"Prepared signing placeholder for invoice {invoice.internal_code} "
            f"(ECFDocument id={ecf.pk}; status=SIGNING_PLACEHOLDER)."
        ),
        metadata={
            "ecf_document_id": ecf.pk,
            "created_ecf_document": created,
            "signing_status": ecf.signing_status,
            "signing_mode": ecf.signing_mode,
            "signature_datetime": ecf.signature_datetime.isoformat() if ecf.signature_datetime else None,
            "official_encf": invoice.official_encf,
            "xml_signed_file_present": bool(ecf.xml_signed_file),
            "dgii_track_id": ecf.dgii_track_id,
            "compliance_claim": "NOT_DGII_COMPLIANT",
        },
    )
    return ecf
