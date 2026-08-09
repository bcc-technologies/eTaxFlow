from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from fiscal.services.encf_sequences import (
    ENCFAllocationError,
    allocate_next_encf,
    preview_next_encf,
)
from invoicing.models import Invoice


class Command(BaseCommand):
    help = (
        "Preview or allocate a local/demo eNCF for an invoice from ENCFSequenceRange. "
        "Does not call DGII, sign, or generate production XML. "
        "Dry-run by default; pass --apply to mutate."
    )

    def add_arguments(self, parser):
        parser.add_argument("--internal-code", dest="internal_code", help="Invoice internal_code.")
        parser.add_argument("--invoice-id", dest="invoice_id", type=int, help="Invoice ID.")
        parser.add_argument("--range-id", dest="range_id", type=int, help="Optional ENCFSequenceRange ID.")
        parser.add_argument(
            "--allow-demo",
            action="store_true",
            help="Required to allocate from demo/non-authorized ranges.",
        )
        parser.add_argument(
            "--actor",
            dest="actor_username",
            help="Optional username recorded on the AuditEvent.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            dest="dry_run",
            help="Preview only (default when --apply is not passed).",
        )
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Actually allocate. Without this flag the command is dry-run only.",
        )

    def handle(self, *args, **options):
        internal_code = options.get("internal_code")
        invoice_id = options.get("invoice_id")
        range_id = options.get("range_id")
        allow_demo = bool(options.get("allow_demo"))
        apply = bool(options.get("apply"))
        dry_run = bool(options.get("dry_run"))
        actor_username = options.get("actor_username")

        if apply and dry_run:
            raise CommandError("Use either --dry-run or --apply, not both.")
        if bool(internal_code) == bool(invoice_id):
            raise CommandError("Provide exactly one of --internal-code or --invoice-id.")

        qs = Invoice.objects.select_related(
            "issuer", "fiscal_document_type_ref", "ecf_document"
        )
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

        # Dry-run may inspect demo ranges without --allow-demo (no mutation).
        # Apply still requires --allow-demo for demo/non-authorized ranges.
        try:
            preview = preview_next_encf(
                invoice,
                range_id=range_id,
                allow_demo=True if not apply else allow_demo,
            )
        except ENCFAllocationError as exc:
            raise CommandError("; ".join(exc.messages)) from exc

        self.stdout.write("eNCF allocation preview (NOT DGII-authorized / NOT DGII-compliant)")
        self.stdout.write("=" * 60)
        self.stdout.write(f"invoice: {invoice.internal_code} (id={invoice.pk})")
        self.stdout.write(f"range_id: {preview['range_id']}")
        self.stdout.write(f"prefix: {preview['prefix']}")
        self.stdout.write(f"next_number: {preview['next_number']} / end={preview['end_number']}")
        self.stdout.write(f"candidate_encf: {preview['candidate_encf']}")
        self.stdout.write(f"sequence_expiration_date: {preview['sequence_expiration_date']}")
        self.stdout.write(f"environment: {preview['environment']}")
        self.stdout.write(f"source: {preview['source']}")
        self.stdout.write(f"is_authorized_by_dgii: {preview['is_authorized_by_dgii']}")
        self.stdout.write(f"is_demo_or_unauthorized: {preview['is_demo_or_unauthorized']}")
        self.stdout.write(f"format_note: {preview['format_note']}")
        if preview["is_demo_or_unauthorized"] and not allow_demo:
            self.stdout.write(
                self.style.WARNING(
                    "This range is demo/non-authorized. Apply requires --allow-demo."
                )
            )

        if not apply:
            self.stdout.write(self.style.WARNING("Dry-run only — no changes applied. Pass --apply to allocate."))
            return

        if preview["is_demo_or_unauthorized"] and not allow_demo:
            raise CommandError("Refusing apply on demo/non-authorized range without --allow-demo.")

        before_encf = invoice.official_encf
        try:
            allocated = allocate_next_encf(
                invoice,
                range_id=range_id,
                actor=actor,
                allow_demo=allow_demo,
            )
        except ENCFAllocationError as exc:
            raise CommandError("; ".join(exc.messages)) from exc

        invoice.refresh_from_db()
        self.stdout.write(self.style.SUCCESS(f"Allocated eNCF: {allocated}"))
        self.stdout.write(f"previous official_encf: {before_encf!r}")
        self.stdout.write(f"invoice.official_encf: {invoice.official_encf!r}")
        self.stdout.write(f"invoice.sequence_expiration_date: {invoice.sequence_expiration_date}")
        self.stdout.write("No ECFDocument created. No XML generated. No DGII call. NOT_DGII_COMPLIANT.")
