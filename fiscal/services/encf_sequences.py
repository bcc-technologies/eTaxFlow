"""Controlled local eNCF allocation (non-production).

Does not call DGII, does not sign, does not generate production XML.
Demo / unauthorized ranges require allow_demo=True.
"""

from __future__ import annotations

from datetime import date

from django.core.exceptions import ValidationError
from django.db import transaction

from audit.models import AuditEvent
from fiscal.models import ENCFSequenceRange
from invoicing.models import Invoice


class ENCFAllocationError(ValidationError):
    """Raised when eNCF allocation cannot proceed."""


def _require_invoice_ready(invoice: Invoice) -> None:
    if invoice is None:
        raise ENCFAllocationError("Invoice must be provided.")
    if not getattr(invoice, "issuer_id", None):
        raise ENCFAllocationError("Invoice must have an issuer.")
    if not getattr(invoice, "fiscal_document_type_ref_id", None):
        raise ENCFAllocationError("Invoice must have fiscal_document_type_ref.")
    if invoice.official_encf:
        raise ENCFAllocationError(
            f"Invoice already has official_encf={invoice.official_encf!r}."
        )
    if invoice.lifecycle_status in {"CANCELLED", "ARCHIVED"}:
        raise ENCFAllocationError(
            f"Cannot allocate eNCF for invoice in status {invoice.lifecycle_status}."
        )
    if invoice.lifecycle_status == "ISSUED":
        raise ENCFAllocationError(
            "Cannot allocate eNCF for an ISSUED invoice (official_encf is immutable)."
        )


def _select_range(
    invoice: Invoice,
    *,
    range_id: int | None,
    allow_demo: bool,
) -> ENCFSequenceRange:
    qs = ENCFSequenceRange.objects.select_for_update().filter(
        issuer_id=invoice.issuer_id,
        fiscal_document_type_id=invoice.fiscal_document_type_ref_id,
        is_active=True,
    )
    if range_id is not None:
        seq_range = qs.filter(pk=range_id).first()
        if seq_range is None:
            raise ENCFAllocationError(
                f"No active ENCFSequenceRange id={range_id} matching invoice issuer/type."
            )
    else:
        seq_range = qs.order_by("pk").first()
        if seq_range is None:
            raise ENCFAllocationError(
                "No active ENCFSequenceRange found for this issuer and fiscal document type."
            )

    if seq_range.environment == "PRODUCTION" and not seq_range.is_authorized_by_dgii:
        raise ENCFAllocationError(
            "Refusing PRODUCTION range that is not marked is_authorized_by_dgii=True."
        )
    if seq_range.is_demo_or_unauthorized and not allow_demo:
        raise ENCFAllocationError(
            "Refusing demo/non-authorized eNCF range unless allow_demo=True. "
            "These values are NOT DGII-authorized."
        )
    return seq_range


def _assert_range_allocable(seq_range: ENCFSequenceRange) -> None:
    today = date.today()
    if (
        seq_range.sequence_expiration_date is not None
        and seq_range.sequence_expiration_date < today
    ):
        raise ENCFAllocationError(
            f"ENCFSequenceRange id={seq_range.pk} expired on "
            f"{seq_range.sequence_expiration_date.isoformat()}."
        )
    if seq_range.next_number > seq_range.end_number:
        raise ENCFAllocationError(
            f"ENCFSequenceRange id={seq_range.pk} is exhausted "
            f"(next_number={seq_range.next_number} > end_number={seq_range.end_number})."
        )


def preview_next_encf(
    invoice: Invoice,
    *,
    range_id: int | None = None,
    allow_demo: bool = False,
) -> dict:
    """Return candidate range/eNCF without mutating state."""
    _require_invoice_ready(invoice)
    with transaction.atomic():
        # Use unlocked read for dry-run preview (no mutation).
        qs = ENCFSequenceRange.objects.filter(
            issuer_id=invoice.issuer_id,
            fiscal_document_type_id=invoice.fiscal_document_type_ref_id,
            is_active=True,
        )
        if range_id is not None:
            seq_range = qs.filter(pk=range_id).first()
            if seq_range is None:
                raise ENCFAllocationError(
                    f"No active ENCFSequenceRange id={range_id} matching invoice issuer/type."
                )
        else:
            seq_range = qs.order_by("pk").first()
            if seq_range is None:
                raise ENCFAllocationError(
                    "No active ENCFSequenceRange found for this issuer and fiscal document type."
                )
        if seq_range.environment == "PRODUCTION" and not seq_range.is_authorized_by_dgii:
            raise ENCFAllocationError(
                "Refusing PRODUCTION range that is not marked is_authorized_by_dgii=True."
            )
        if seq_range.is_demo_or_unauthorized and not allow_demo:
            raise ENCFAllocationError(
                "Refusing demo/non-authorized eNCF range unless allow_demo=True. "
                "These values are NOT DGII-authorized."
            )
        _assert_range_allocable(seq_range)
        candidate = seq_range.peek_next_encf()
        return {
            "range_id": seq_range.pk,
            "prefix": seq_range.prefix,
            "next_number": seq_range.next_number,
            "end_number": seq_range.end_number,
            "candidate_encf": candidate,
            "sequence_expiration_date": seq_range.sequence_expiration_date,
            "environment": seq_range.environment,
            "source": seq_range.source,
            "is_authorized_by_dgii": seq_range.is_authorized_by_dgii,
            "is_demo_or_unauthorized": seq_range.is_demo_or_unauthorized,
            "format_note": (
                "Local demo format = prefix + zero-padded number; "
                "not claimed to match DGII-authorized eNCF issuance."
            ),
        }


@transaction.atomic
def allocate_next_encf(
    invoice: Invoice,
    *,
    range_id: int | None = None,
    actor=None,
    allow_demo: bool = False,
) -> str:
    """Allocate next eNCF from a configured range onto the invoice.

    Mutates Invoice.official_encf, Invoice.sequence_expiration_date, and
    ENCFSequenceRange.next_number. Creates an AuditEvent. Does not create
    ECFDocument, XML, signatures, or DGII calls.
    """
    _require_invoice_ready(invoice)
    # Re-fetch invoice under transaction for consistency.
    invoice = Invoice.objects.select_for_update().get(pk=invoice.pk)
    _require_invoice_ready(invoice)

    seq_range = _select_range(invoice, range_id=range_id, allow_demo=allow_demo)
    _assert_range_allocable(seq_range)

    allocated_number = seq_range.next_number
    allocated_encf = seq_range.format_encf(allocated_number)

    invoice.official_encf = allocated_encf
    if seq_range.sequence_expiration_date is not None:
        invoice.sequence_expiration_date = seq_range.sequence_expiration_date
    invoice.save()

    seq_range.next_number = allocated_number + 1
    seq_range.save(update_fields=["next_number", "updated_at"])

    AuditEvent.objects.create(
        actor=actor,
        event_type="encf_allocated",
        entity_type="Invoice",
        entity_id=invoice.pk,
        message=(
            f"Allocated eNCF {allocated_encf} to invoice {invoice.internal_code} "
            f"from range id={seq_range.pk} ({seq_range.environment}/{seq_range.source})."
        ),
        metadata={
            "range_id": seq_range.pk,
            "allocated_encf": allocated_encf,
            "allocated_number": allocated_number,
            "environment": seq_range.environment,
            "source": seq_range.source,
            "is_authorized_by_dgii": seq_range.is_authorized_by_dgii,
            "is_demo_or_unauthorized": seq_range.is_demo_or_unauthorized,
            "allow_demo": allow_demo,
            "sequence_expiration_date": (
                seq_range.sequence_expiration_date.isoformat()
                if seq_range.sequence_expiration_date
                else None
            ),
            "compliance_claim": "NOT_DGII_COMPLIANT",
        },
    )
    return allocated_encf
