from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

from ecf.services.internal_invoice_xml import build_internal_invoice_xml
from ecf.services.internal_xml_documents import generate_internal_xml_document
from invoicing.models import Invoice


class Command(BaseCommand):
    help = "Generate internal XML draft documents for invoices."

    def add_arguments(self, parser):
        parser.add_argument(
            "--invoice",
            dest="invoice_code",
            help="Generate an internal XML draft for the invoice with the given internal code."
        )
        parser.add_argument(
            "--internal-code",
            dest="invoice_code",
            help="Generate an internal XML draft for the invoice with the given internal code."
        )
        parser.add_argument(
            "--invoice-id",
            dest="invoice_id",
            type=int,
            help="Generate an internal XML draft for the invoice with the given database ID.",
        )
        parser.add_argument(
            "--all",
            action="store_true",
            dest="generate_all",
            help="Generate internal XML drafts for all invoices.",
        )
        parser.add_argument(
            "--stdout",
            action="store_true",
            dest="stdout_flag",
            help="Print the internal XML to stdout instead of saving it.",
        )
        parser.add_argument(
            "--created-by",
            dest="created_by_username",
            help="Assign a creator username when saving generated documents.",
        )

    def handle(self, *args, **options):
        invoice_code = options.get("invoice_code")
        invoice_id = options.get("invoice_id")
        generate_all = options.get("generate_all")
        stdout_flag = options.get("stdout_flag")
        created_by_username = options.get("created_by_username")

        selection_count = bool(invoice_code) + bool(invoice_id) + bool(generate_all)
        if selection_count == 0:
            raise CommandError("Provide --internal-code, --invoice-id, or --all to generate internal XML drafts.")
        if selection_count > 1:
            raise CommandError("Use only one of --internal-code, --invoice-id, or --all.")
        if stdout_flag and generate_all:
            raise CommandError("--stdout cannot be used with --all.")

        created_by = None
        if created_by_username:
            user_model = get_user_model()
            created_by = user_model.objects.filter(username=created_by_username).first()
            if not created_by:
                raise CommandError(f"User not found: {created_by_username}")

        if invoice_id is not None:
            invoice = Invoice.objects.filter(pk=invoice_id).first()
            if not invoice:
                raise CommandError(f"Invoice not found with ID: {invoice_id}")
            invoices = [invoice]
        elif invoice_code:
            invoice = Invoice.objects.filter(internal_code=invoice_code).first()
            if not invoice:
                raise CommandError(f"Invoice not found: {invoice_code}")
            invoices = [invoice]
        else:
            invoices = list(Invoice.objects.all().order_by("internal_code"))

        if stdout_flag:
            if len(invoices) != 1:
                raise CommandError("--stdout requires a single invoice selection by --internal-code or --invoice-id.")
            try:
                xml_string = build_internal_invoice_xml(invoices[0])
            except ValidationError as exc:
                raise CommandError(str(exc))
            self.stdout.write(xml_string)
            return

        created_count = 0
        reused_count = 0
        errors = []

        for invoice in invoices:
            try:
                document, created = generate_internal_xml_document(invoice, created_by=created_by)
                if created:
                    created_count += 1
                    self.stdout.write(self.style.SUCCESS(
                        f"Saved internal XML draft {document.internal_code} with sha256 {document.sha256_hash}."
                    ))
                else:
                    reused_count += 1
                    self.stdout.write(self.style.WARNING(
                        f"Reused existing internal XML draft {document.internal_code} with sha256 {document.sha256_hash}."
                    ))
            except ValidationError as exc:
                errors.append(f"{invoice.internal_code}: {exc.message}")

        if created_count:
            self.stdout.write(self.style.SUCCESS(f"Generated {created_count} internal XML draft document(s)."))
        if reused_count:
            self.stdout.write(self.style.WARNING(f"{reused_count} invoice(s) already had an identical internal XML draft."))
        if errors:
            for error in errors:
                self.stderr.write(error)
            raise CommandError("Some invoices could not generate internal XML drafts.")
