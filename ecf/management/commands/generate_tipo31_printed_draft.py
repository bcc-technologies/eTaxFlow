from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

from ecf.dgii.xml_draft.tipo_ecf_31_unsigned import Tipo31UnsignedDraftError
from ecf.printed.tipo31_printed_draft import generate_tipo31_printed_draft_document
from invoicing.models import Invoice


class Command(BaseCommand):
    help = (
        "Generate/reuse a non-production Tipo 31 printed PDF draft. "
        "No DGII approval, signing, TrackId, or submission."
    )

    def add_arguments(self, parser):
        parser.add_argument("--internal-code", dest="internal_code")
        parser.add_argument("--invoice-id", dest="invoice_id", type=int)
        parser.add_argument(
            "--allow-demo-encf",
            action="store_true",
            dest="allow_demo_encf",
            help="Required for demo/non-authorized eNCF values.",
        )
        parser.add_argument("--created-by", dest="created_by_username")

    def handle(self, *args, **options):
        internal_code = options.get("internal_code")
        invoice_id = options.get("invoice_id")
        if bool(internal_code) == bool(invoice_id):
            raise CommandError("Provide exactly one of --internal-code or --invoice-id.")
        qs = Invoice.objects.select_related(
            "fiscal_document_type_ref", "issuer", "customer"
        )
        if invoice_id is not None:
            invoice = qs.filter(pk=invoice_id).first()
            if not invoice:
                raise CommandError(f"Invoice not found with ID: {invoice_id}")
        else:
            invoice = qs.filter(internal_code=internal_code).first()
            if not invoice:
                raise CommandError(f"Invoice not found: {internal_code}")

        created_by = None
        username = options.get("created_by_username")
        if username:
            created_by = get_user_model().objects.filter(username=username).first()
            if created_by is None:
                raise CommandError(f"User not found: {username}")
        try:
            document, created = generate_tipo31_printed_draft_document(
                invoice,
                created_by=created_by,
                allow_demo_encf=bool(options.get("allow_demo_encf")),
            )
        except (ValidationError, Tipo31UnsignedDraftError) as exc:
            msgs = getattr(exc, "messages", None) or [str(exc)]
            raise CommandError("; ".join(msgs)) from exc

        verb = "Created" if created else "Reused"
        style = self.style.SUCCESS if created else self.style.WARNING
        self.stdout.write(
            style(
                f"{verb} Tipo 31 printed draft Document {document.internal_code} "
                f"sha256={document.sha256_hash}"
            )
        )
        self.stdout.write(f"invoice: {invoice.internal_code}")
        self.stdout.write(f"document_id: {document.pk}")
        self.stdout.write(f"original_filename: {document.original_filename}")
        self.stdout.write(f"file_size: {document.file_size}")
        self.stdout.write("representation_status: NON_PRODUCTION_DRAFT")
        self.stdout.write("compliance_status: NOT_DGII_COMPLIANT")
        self.stdout.write("dgii_approval_claim: false")
        self.stdout.write("signature_status: NOT_IMPLEMENTED")
        self.stdout.write("qr_security_code: omitted (not source-backed)")
        self.stdout.write("No DGII call. No TrackId. No production approval.")
