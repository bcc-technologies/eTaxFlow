import json

from django.core.management.base import BaseCommand, CommandError

from ecf.dgii.mapping import build_invoice_dgii_mapping_report
from invoicing.models import Invoice


class Command(BaseCommand):
    help = (
        "Inspect how an Invoice maps to future DGII e-CF concepts. "
        "Read-only: no XML, Document, ECFDocument, or DGII calls."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--internal-code",
            dest="internal_code",
            help="Invoice internal_code to inspect.",
        )
        parser.add_argument(
            "--invoice-id",
            dest="invoice_id",
            type=int,
            help="Invoice database ID to inspect.",
        )
        parser.add_argument(
            "--json",
            action="store_true",
            dest="as_json",
            help="Print mapping report as JSON.",
        )
        parser.add_argument(
            "--strict",
            action="store_true",
            help="Exit with error when blocking mapping issues exist.",
        )

    def handle(self, *args, **options):
        internal_code = options.get("internal_code")
        invoice_id = options.get("invoice_id")
        as_json = bool(options.get("as_json"))
        strict = bool(options.get("strict"))

        if bool(internal_code) == bool(invoice_id):
            raise CommandError("Provide exactly one of --internal-code or --invoice-id.")

        if invoice_id is not None:
            invoice = Invoice.objects.filter(pk=invoice_id).select_related(
                "issuer", "customer", "fiscal_document_type_ref"
            ).first()
            if not invoice:
                raise CommandError(f"Invoice not found with ID: {invoice_id}")
        else:
            invoice = Invoice.objects.filter(internal_code=internal_code).select_related(
                "issuer", "customer", "fiscal_document_type_ref"
            ).first()
            if not invoice:
                raise CommandError(f"Invoice not found: {internal_code}")

        report = build_invoice_dgii_mapping_report(invoice)

        if as_json:
            self.stdout.write(json.dumps(report.to_dict(), indent=2, default=str))
        else:
            self._print_human(report)

        if strict and report.blocking_issues:
            codes = ", ".join(i.code for i in report.blocking_issues)
            raise CommandError(
                f"Strict mapping failed with {len(report.blocking_issues)} blocking issue(s): {codes}"
            )

    def _print_human(self, report):
        self.stdout.write("DGII concept mapping report (NOT DGII-compliant)")
        self.stdout.write("=" * 50)
        self.stdout.write(f"Invoice ID: {report.invoice_id}")
        self.stdout.write(f"internal_code: {report.internal_code}")
        self.stdout.write(f"official_ncf present: {report.official_ncf_present} value={report.official_ncf!r}")
        self.stdout.write(f"official_encf present: {report.official_encf_present} value={report.official_encf!r}")
        self.stdout.write(
            f"Fiscal type: code={report.fiscal_document_type.internal_code!r} "
            f"name={report.fiscal_document_type.internal_name!r} "
            f"mapped={report.fiscal_document_type.mapped}"
        )
        if report.fiscal_document_type.dgii_tipoe_cf_concept:
            self.stdout.write(f"  TipoeCF concept: {report.fiscal_document_type.dgii_tipoe_cf_concept}")
        self.stdout.write(f"future_catalog: {report.future_catalog}")
        self.stdout.write(f"catalog_status: {report.catalog_status}")
        if report.source_inventory_status:
            self.stdout.write(
                "source_inventory_status: "
                f"{report.source_inventory_status.get('summary')} "
                f"(collected={report.source_inventory_status.get('collected_count')}, "
                f"missing={report.source_inventory_status.get('missing_count')})"
            )

        for title, fields in (
            ("Issuer fields", report.issuer_fields),
            ("Customer fields", report.customer_fields),
            ("Line fields", report.line_fields),
            ("Totals fields", report.totals_fields),
            ("Identity fields", report.identity_fields),
        ):
            self.stdout.write("")
            self.stdout.write(title)
            for item in fields:
                mark = "OK" if item.present else "MISSING"
                self.stdout.write(
                    f"  [{mark}] {item.internal_field} -> {item.dgii_concept}"
                    + (f" ({item.value_preview})" if item.value_preview is not None else "")
                )

        self.stdout.write("")
        self.stdout.write(f"Status: {report.status.value}")
        self.stdout.write(
            f"Enough internal data for future e-CF draft: "
            f"{report.enough_internal_data_for_future_ecf_draft}"
        )
        self.stdout.write(f"Compliance claim: {report.compliance_claim}")

        self.stdout.write("")
        self.stdout.write("Issues:")
        if not report.issues:
            self.stdout.write("  (none)")
        for item in report.issues:
            style = self.style.ERROR if item.severity.value == "BLOCKING" else self.style.WARNING
            if item.severity.value == "INFO":
                style = self.style.NOTICE if hasattr(self.style, "NOTICE") else self.style.SUCCESS
            self.stdout.write(style(f"  [{item.severity.value}] {item.code}: {item.message}"))
