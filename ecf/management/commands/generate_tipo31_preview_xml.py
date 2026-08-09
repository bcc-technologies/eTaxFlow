from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

from ecf.dgii.xml_preview.documents import generate_tipo31_preview_document
from ecf.dgii.xml_preview.tipo_ecf_31_preview import (
    Tipo31XmlPreviewError,
    build_tipo31_xml_preview,
)
from invoicing.models import Invoice


class Command(BaseCommand):
    help = (
        "Generate a non-production Tipo e-CF 31 XML structure preview. "
        "NOT_DGII_COMPLIANT. Does not sign, create TrackId, or call DGII. "
        "Default mode saves/reuses a Document unless --stdout is used."
    )

    def add_arguments(self, parser):
        parser.add_argument("--internal-code", dest="internal_code")
        parser.add_argument("--invoice-id", dest="invoice_id", type=int)
        parser.add_argument(
            "--stdout",
            action="store_true",
            dest="stdout_flag",
            help="Print preview XML to stdout and do not create a Document.",
        )
        parser.add_argument(
            "--save",
            action="store_true",
            dest="save_flag",
            help="Save/reuse Document (default when --stdout is not used).",
        )
        parser.add_argument(
            "--allow-demo-encf",
            action="store_true",
            dest="allow_demo_encf",
            help="Required when invoice official_encf is demo/non-authorized.",
        )
        parser.add_argument(
            "--no-require-signing-placeholder",
            action="store_true",
            dest="no_require_signing_placeholder",
            help="Skip requiring ECFDocument signing placeholder / signature_datetime.",
        )
        parser.add_argument(
            "--created-by",
            dest="created_by_username",
            help="Optional username for Document.created_by / audit actor.",
        )

    def handle(self, *args, **options):
        internal_code = options.get("internal_code")
        invoice_id = options.get("invoice_id")
        stdout_flag = bool(options.get("stdout_flag"))
        save_flag = bool(options.get("save_flag"))
        allow_demo_encf = bool(options.get("allow_demo_encf"))
        require_signing_placeholder = not bool(options.get("no_require_signing_placeholder"))
        created_by_username = options.get("created_by_username")

        if bool(internal_code) == bool(invoice_id):
            raise CommandError("Provide exactly one of --internal-code or --invoice-id.")
        if stdout_flag and save_flag:
            raise CommandError("Use either --stdout or --save, not both.")

        qs = Invoice.objects.select_related(
            "fiscal_document_type_ref",
            "issuer",
            "customer",
            "income_type",
            "payment_type",
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
        if created_by_username:
            created_by = get_user_model().objects.filter(username=created_by_username).first()
            if created_by is None:
                raise CommandError(f"User not found: {created_by_username}")

        # Default: save unless --stdout.
        if stdout_flag:
            try:
                xml_bytes = build_tipo31_xml_preview(
                    invoice,
                    allow_demo_encf=allow_demo_encf,
                    require_signing_placeholder=require_signing_placeholder,
                )
            except (ValidationError, Tipo31XmlPreviewError) as exc:
                msgs = getattr(exc, "messages", None) or [str(exc)]
                raise CommandError("; ".join(msgs)) from exc
            self.stdout.write(xml_bytes.decode("utf-8"))
            self.stdout.write(
                self.style.WARNING(
                    "Stdout mode: no Document created. NOT_DGII_COMPLIANT; "
                    "Signature missing; no signing/submission."
                )
            )
            return

        try:
            document, created = generate_tipo31_preview_document(
                invoice,
                created_by=created_by,
                allow_demo_encf=allow_demo_encf,
                require_signing_placeholder=require_signing_placeholder,
            )
        except (ValidationError, Tipo31XmlPreviewError) as exc:
            msgs = getattr(exc, "messages", None) or [str(exc)]
            raise CommandError("; ".join(msgs)) from exc

        verb = "Created" if created else "Reused"
        style = self.style.SUCCESS if created else self.style.WARNING
        self.stdout.write(
            style(
                f"{verb} Tipo 31 XML preview Document {document.internal_code} "
                f"sha256={document.sha256_hash}"
            )
        )
        self.stdout.write(f"invoice: {invoice.internal_code}")
        self.stdout.write(f"document_id: {document.pk}")
        self.stdout.write(f"original_filename: {document.original_filename}")
        self.stdout.write(
            "NOT_DGII_COMPLIANT. No ECFDocument created by this command. "
            "No Signature/XMLDSig. No TrackId. No DGII submission."
        )
