import json

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

from ecf.dgii.xml_draft.tipo_ecf_31_unsigned import Tipo31UnsignedDraftError
from ecf.dgii.xsd.tipo31_signed_sandbox_validation import (
    validate_tipo31_signed_sandbox,
)
from ecf.services.signing_sandbox import SandboxSigningError
from invoicing.models import Invoice


class Command(BaseCommand):
    help = (
        "Validate a test-only sandbox-signed Tipo e-CF 31 draft against the local XSD. "
        "No DGII call, TrackId, production certificate, or submission."
    )

    def add_arguments(self, parser):
        parser.add_argument("--internal-code", dest="internal_code")
        parser.add_argument("--invoice-id", dest="invoice_id", type=int)
        parser.add_argument(
            "--allow-demo-encf",
            action="store_true",
            dest="allow_demo_encf",
            help="Required when invoice official_encf is demo/non-authorized.",
        )
        parser.add_argument(
            "--test-only",
            action="store_true",
            dest="test_only",
            help="Required explicit opt-in for synthetic sandbox signing.",
        )
        parser.add_argument("--json", action="store_true", dest="json_flag")
        parser.add_argument(
            "--no-require-signing-placeholder",
            action="store_true",
            dest="no_require_signing_placeholder",
        )
        parser.add_argument(
            "--no-schema-repair",
            action="store_true",
            dest="no_schema_repair",
        )

    def handle(self, *args, **options):
        internal_code = options.get("internal_code")
        invoice_id = options.get("invoice_id")
        if bool(internal_code) == bool(invoice_id):
            raise CommandError("Provide exactly one of --internal-code or --invoice-id.")
        if not options.get("test_only"):
            raise CommandError(
                "Refusing sandbox signing without explicit --test-only. "
                "Production signing remains blocked."
            )

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

        try:
            report = validate_tipo31_signed_sandbox(
                invoice,
                allow_demo_encf=bool(options.get("allow_demo_encf")),
                test_only=True,
                require_signing_placeholder=not bool(
                    options.get("no_require_signing_placeholder")
                ),
                allow_local_schema_repair=not bool(options.get("no_schema_repair")),
            )
        except (ValidationError, Tipo31UnsignedDraftError, SandboxSigningError) as exc:
            msgs = getattr(exc, "messages", None) or [str(exc)]
            raise CommandError("; ".join(msgs)) from exc

        if options.get("json_flag"):
            self.stdout.write(json.dumps(report.to_dict(), indent=2, sort_keys=True))
            return

        self.stdout.write("Local Tipo 31 signed sandbox XSD validation")
        self.stdout.write("=" * 60)
        self.stdout.write(f"invoice: {report.invoice_internal_code}")
        self.stdout.write(f"xsd_path: {report.xsd_path}")
        self.stdout.write(f"xsd_valid: {report.xsd_valid}")
        self.stdout.write(f"signed_sandbox_valid: {report.signed_sandbox_valid}")
        self.stdout.write(f"signature_status: {report.signature_status}")
        self.stdout.write(f"signature_present: {report.signature_present}")
        self.stdout.write(f"signature_verified: {report.signature_verified}")
        self.stdout.write(f"remaining_error_count: {len(report.remaining_errors)}")
        self.stdout.write(f"signature_error_count: {len(report.signature_errors)}")
        self.stdout.write(f"schema_mode: {report.schema_mode}")
        self.stdout.write(f"compliance_status: {report.compliance_status}")
        self.stdout.write(f"dgii_submission_allowed: {report.dgii_submission_allowed}")
        self.stdout.write(f"not_certification_evidence: {report.not_certification_evidence}")
        self.stdout.write("remaining_errors:")
        for error in report.remaining_errors:
            self.stdout.write(
                f"  - [{error.get('error_group')}] {error.get('message')}"
            )
        self.stdout.write("signature_errors:")
        for error in report.signature_errors:
            self.stdout.write(f"  - {error}")
        self.stdout.write("schema_stub_limitations:")
        for limitation in report.schema_stub_limitations:
            self.stdout.write(f"  - {limitation}")
        self.stdout.write("notes:")
        for note in report.notes:
            self.stdout.write(f"  - {note}")
