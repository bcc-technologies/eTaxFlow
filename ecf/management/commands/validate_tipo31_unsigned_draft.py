import json

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

from ecf.dgii.xml_draft.tipo_ecf_31_unsigned import Tipo31UnsignedDraftError
from ecf.dgii.xsd.tipo31_unsigned_validation import (
    validate_tipo31_unsigned_draft,
    write_tipo31_unsigned_validation_report,
)
from invoicing.models import Invoice


class Command(BaseCommand):
    help = (
        "Validate an unsigned Tipo e-CF 31 draft against the local XSD. "
        "Expected to be invalid (Signature missing / unsigned). "
        "NOT_DGII_COMPLIANT. Does not mutate data, sign, or call DGII."
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
            "--no-require-signing-placeholder",
            action="store_true",
            dest="no_require_signing_placeholder",
        )
        parser.add_argument(
            "--json",
            action="store_true",
            dest="json_flag",
            help="Print structured JSON report.",
        )
        parser.add_argument(
            "--write-report",
            dest="write_report",
            help="Write Markdown report to this filesystem path.",
        )
        parser.add_argument(
            "--no-schema-repair",
            action="store_true",
            dest="no_schema_repair",
            help=(
                "Do not apply experimental in-memory stub for missing "
                "IndicadorServicioTodoIncluidoType."
            ),
        )

    def handle(self, *args, **options):
        internal_code = options.get("internal_code")
        invoice_id = options.get("invoice_id")
        allow_demo_encf = bool(options.get("allow_demo_encf"))
        require_signing_placeholder = not bool(
            options.get("no_require_signing_placeholder")
        )
        json_flag = bool(options.get("json_flag"))
        write_report = options.get("write_report")
        allow_repair = not bool(options.get("no_schema_repair"))

        if bool(internal_code) == bool(invoice_id):
            raise CommandError("Provide exactly one of --internal-code or --invoice-id.")

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
            report = validate_tipo31_unsigned_draft(
                invoice,
                allow_demo_encf=allow_demo_encf,
                require_signing_placeholder=require_signing_placeholder,
                allow_local_schema_repair=allow_repair,
            )
        except (ValidationError, Tipo31UnsignedDraftError) as exc:
            msgs = getattr(exc, "messages", None) or [str(exc)]
            raise CommandError("; ".join(msgs)) from exc

        if write_report:
            path = write_tipo31_unsigned_validation_report(report, write_report)
            self.stdout.write(self.style.SUCCESS(f"Wrote Markdown report: {path}"))

        if json_flag:
            self.stdout.write(json.dumps(report.to_dict(), indent=2, sort_keys=True))
        else:
            self.stdout.write("Local Tipo 31 unsigned draft XSD validation")
            self.stdout.write("=" * 60)
            self.stdout.write(f"invoice: {report.invoice_internal_code}")
            self.stdout.write(f"xsd_path: {report.xsd_path}")
            self.stdout.write(f"validator_engine: {report.validator_engine}")
            self.stdout.write(f"schema_mode: {report.schema_mode}")
            self.stdout.write(f"schema_repair_applied: {report.schema_repair_applied}")
            self.stdout.write(f"is_valid: {report.is_valid}")
            self.stdout.write(f"expected_validity: {report.expected_validity}")
            self.stdout.write(f"error_count: {report.error_count}")
            self.stdout.write(f"total_error_count: {report.total_error_count}")
            self.stdout.write(
                f"intentional_unsigned_error_count: {report.intentional_unsigned_error_count}"
            )
            self.stdout.write(
                f"avoidable_demo_facet_error_count: {report.avoidable_demo_facet_error_count}"
            )
            self.stdout.write(
                f"local_xsd_stub_error_count: {report.local_xsd_stub_error_count}"
            )
            self.stdout.write(
                f"structural_mismatch_count: {report.structural_mismatch_count}"
            )
            self.stdout.write(f"unknown_error_count: {report.unknown_error_count}")
            self.stdout.write(f"compliance_status: {report.compliance_status}")
            self.stdout.write(
                "known_missing_required_fields: "
                + ", ".join(report.known_missing_required_fields)
            )
            self.stdout.write("error_groups:")
            for group_name, items in (report.error_groups or {}).items():
                self.stdout.write(f"  {group_name}: {len(items)}")
                for err in items[:10]:
                    self.stdout.write(f"    - {err.get('message')}")
            self.stdout.write("expected_failure_reasons:")
            for reason in report.expected_failure_reasons:
                self.stdout.write(f"  - {reason}")
            self.stdout.write("structural_mismatches:")
            for item in report.structural_mismatches:
                self.stdout.write(f"  - {item}")
            if report.validation_errors:
                self.stdout.write("validation_errors (first 20):")
                for err in report.validation_errors[:20]:
                    loc = ""
                    if err.get("line") is not None:
                        loc = f"L{err['line']}"
                        if err.get("column") is not None:
                            loc += f":C{err['column']}"
                        loc += " "
                    group = err.get("error_group") or ""
                    self.stdout.write(f"  - [{group}] {loc}{err.get('message')}")

        notice_stream = self.stderr if json_flag else self.stdout
        if report.expected_invalid_unsigned_draft and not report.is_valid:
            notice_stream.write(
                self.style.WARNING(
                    "Expected invalid unsigned draft — Signature missing / unsigned "
                    "limitations. NOT_DGII_COMPLIANT. Not certification evidence. "
                    "Command exits successfully for this expected failure."
                )
            )
        elif report.is_valid:
            # Unexpected for current phase; still no compliance claim.
            notice_stream.write(
                self.style.WARNING(
                    "Instance reported valid against local experimental validation, "
                    "but eTaxFlow still claims NOT_DGII_COMPLIANT "
                    "(no signing/submission)."
                )
            )
