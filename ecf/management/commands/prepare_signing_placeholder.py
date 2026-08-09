from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from ecf.services.signing_placeholder import (
    SigningPlaceholderError,
    prepare_signing_placeholder,
    preview_signing_placeholder,
)
from invoicing.models import Invoice


class Command(BaseCommand):
    help = (
        "Prepare a non-production signing placeholder (FechaHoraFirma stub) for an invoice. "
        "Does not digitally sign, store certificates/private keys, or call DGII. "
        "Dry-run by default; pass --apply to mutate."
    )

    def add_arguments(self, parser):
        parser.add_argument("--internal-code", dest="internal_code")
        parser.add_argument("--invoice-id", dest="invoice_id", type=int)
        parser.add_argument("--actor", dest="actor_username", help="Optional username for audit.")
        parser.add_argument("--note", dest="note", default="", help="Optional placeholder note.")
        parser.add_argument(
            "--dry-run",
            action="store_true",
            dest="dry_run",
            help="Preview only (default when --apply is not passed).",
        )
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Create/update ECFDocument signing placeholder.",
        )

    def handle(self, *args, **options):
        internal_code = options.get("internal_code")
        invoice_id = options.get("invoice_id")
        apply = bool(options.get("apply"))
        dry_run = bool(options.get("dry_run"))
        note = options.get("note") or None
        actor_username = options.get("actor_username")

        if apply and dry_run:
            raise CommandError("Use either --dry-run or --apply, not both.")
        if bool(internal_code) == bool(invoice_id):
            raise CommandError("Provide exactly one of --internal-code or --invoice-id.")

        qs = Invoice.objects.select_related("fiscal_document_type_ref", "issuer")
        if invoice_id is not None:
            invoice = qs.filter(pk=invoice_id).first()
            if not invoice:
                raise CommandError(f"Invoice not found with ID: {invoice_id}")
        else:
            invoice = qs.filter(internal_code=internal_code).first()
            if not invoice:
                raise CommandError(f"Invoice not found: {internal_code}")

        actor = None
        if actor_username:
            actor = get_user_model().objects.filter(username=actor_username).first()
            if actor is None:
                raise CommandError(f"Actor user not found: {actor_username}")

        try:
            preview = preview_signing_placeholder(invoice)
        except SigningPlaceholderError as exc:
            raise CommandError("; ".join(exc.messages)) from exc

        self.stdout.write("Signing placeholder preview (NOT real digital signing / NOT DGII-compliant)")
        self.stdout.write("=" * 70)
        self.stdout.write(f"invoice: {preview['internal_code']} (id={preview['invoice_id']})")
        self.stdout.write(f"official_encf: {preview['official_encf']!r}")
        self.stdout.write(f"sequence_expiration_date: {preview['sequence_expiration_date']}")
        self.stdout.write(f"ecf_document_id: {preview['ecf_document_id']}")
        self.stdout.write(f"would_create_ecf_document: {preview['would_create_ecf_document']}")
        self.stdout.write(f"environment: {preview['environment']}")
        self.stdout.write(f"signing_status: {preview['signing_status']}")
        self.stdout.write(f"signing_mode: {preview['signing_mode']}")
        self.stdout.write(f"would_set_signature_datetime: {preview['would_set_signature_datetime']}")
        self.stdout.write(f"would_write_xml_signed_file: {preview['would_write_xml_signed_file']}")
        self.stdout.write(f"would_set_track_id: {preview['would_set_track_id']}")
        self.stdout.write(f"note: {preview['note']}")

        if not apply:
            self.stdout.write(
                self.style.WARNING("Dry-run only — no changes applied. Pass --apply to prepare placeholder.")
            )
            return

        try:
            ecf = prepare_signing_placeholder(invoice, actor=actor, note=note)
        except SigningPlaceholderError as exc:
            raise CommandError("; ".join(exc.messages)) from exc

        self.stdout.write(self.style.SUCCESS(f"Prepared signing placeholder for {invoice.internal_code}"))
        self.stdout.write(f"ECFDocument id: {ecf.pk}")
        self.stdout.write(f"signing_status: {ecf.signing_status}")
        self.stdout.write(f"signing_mode: {ecf.signing_mode}")
        self.stdout.write(f"signature_datetime: {ecf.signature_datetime}")
        self.stdout.write(f"xml_signed_file: {bool(ecf.xml_signed_file)}")
        self.stdout.write(f"dgii_track_id: {ecf.dgii_track_id!r}")
        self.stdout.write("No real signature. No certificates/private keys. NOT_DGII_COMPLIANT.")
