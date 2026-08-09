import json
from decimal import Decimal
from io import StringIO
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from contacts.models import Contact
from documents.models import Document
from ecf.dgii.field_catalogs.tipo_ecf_31 import (
    TIPO_ECF_31_CATALOG_STATUS,
    TIPO_ECF_31_FUTURE_CATALOG,
)
from ecf.dgii.mapping import build_invoice_dgii_mapping_report
from ecf.dgii.types import DGIIMappingStatus
from ecf.models import ECFDocument
from fiscal.models import FiscalDocumentType
from invoicing.models import Invoice, InvoiceLine
from organizations.models import Organization


class DGIIMappingReportTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="mapper", password="x")
        self.issuer = Organization.objects.create(
            legal_name="BCC Technologies",
            commercial_name="BCC",
            rnc="1310000000",
            address="Santo Domingo",
            email="info@bcc.com",
        )
        self.customer = Contact.objects.create(
            contact_type="CLIENT",
            legal_name="Demo Client S.R.L.",
            commercial_name="Demo Client",
            rnc_or_id="123456789",
            id_type="RNC",
            address="Santo Domingo",
        )
        self.fiscal_type = FiscalDocumentType.objects.create(
            code="31",
            name="Factura de Crédito Fiscal Electrónica",
            document_group="INVOICE",
            direction="OUTBOUND",
        )
        self.invoice = Invoice.objects.create(
            issuer=self.issuer,
            customer=self.customer,
            invoice_direction="OUTBOUND",
            lifecycle_status="DRAFT",
            currency="DOP",
            issue_date="2026-01-01",
            created_by=self.user,
            internal_code="BCC-AR-2026-000501",
            fiscal_document_type="31",
            fiscal_document_type_ref=self.fiscal_type,
            official_ncf=None,
            official_encf=None,
        )
        InvoiceLine.objects.create(
            invoice=self.invoice,
            line_order=1,
            description="Consulting",
            quantity=Decimal("1.00"),
            unit_price=Decimal("100.00"),
            discount_amount=Decimal("0.00"),
            tax_rate=Decimal("18.00"),
            tax_amount=Decimal("18.00"),
            line_total=Decimal("118.00"),
            item_code_snapshot="CONSULT",
            item_name_snapshot="Consulting",
            unit_snapshot="SERVICE",
            tax_rate_snapshot="ITBIS_18",
            currency_snapshot="DOP",
        )
        self.invoice.refresh_from_db()

    def test_mapping_report_does_not_mutate_invoice(self):
        before = {
            "internal_code": self.invoice.internal_code,
            "official_ncf": self.invoice.official_ncf,
            "official_encf": self.invoice.official_encf,
            "lifecycle_status": self.invoice.lifecycle_status,
            "updated_at": self.invoice.updated_at,
            "grand_total": self.invoice.grand_total,
        }
        build_invoice_dgii_mapping_report(self.invoice)
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.internal_code, before["internal_code"])
        self.assertEqual(self.invoice.official_ncf, before["official_ncf"])
        self.assertEqual(self.invoice.official_encf, before["official_encf"])
        self.assertEqual(self.invoice.lifecycle_status, before["lifecycle_status"])
        self.assertEqual(self.invoice.updated_at, before["updated_at"])
        self.assertEqual(self.invoice.grand_total, before["grand_total"])

    def test_report_distinguishes_internal_code_from_official_ids(self):
        self.invoice.official_ncf = "B01000000001"
        self.invoice.official_encf = "E310000000001"
        self.invoice.save()
        report = build_invoice_dgii_mapping_report(self.invoice)
        self.assertEqual(report.internal_code, "BCC-AR-2026-000501")
        self.assertNotEqual(report.internal_code, report.official_ncf)
        self.assertNotEqual(report.internal_code, report.official_encf)
        self.assertTrue(report.official_ncf_present)
        self.assertTrue(report.official_encf_present)
        identity = {f.internal_field: f for f in report.identity_fields}
        self.assertIn("internal_code", identity)
        self.assertIn("official_ncf", identity)
        self.assertIn("official_encf", identity)

    def test_seeded_invoice_has_fiscal_document_type_ref_mapped(self):
        from django.core.management import call_command

        call_command("seed_bcc")
        seeded = Invoice.objects.filter(notes__icontains="SEEDED_BCC_DEMO_INVOICE").first()
        self.assertIsNotNone(seeded)
        self.assertIsNotNone(seeded.fiscal_document_type_ref)
        report = build_invoice_dgii_mapping_report(seeded)
        self.assertTrue(report.fiscal_document_type.mapped)
        self.assertEqual(report.fiscal_document_type.internal_code, "31")
        self.assertEqual(report.future_catalog, TIPO_ECF_31_FUTURE_CATALOG)
        self.assertEqual(report.catalog_status, TIPO_ECF_31_CATALOG_STATUS)
        codes = {i.code for i in report.issues}
        self.assertIn("TIPO_ECF_31_CATALOG_PENDING_SOURCE_REVIEW", codes)

    def test_report_identifies_missing_issuer_or_customer_rnc(self):
        self.issuer.rnc = ""
        self.issuer.save(update_fields=["rnc"])
        self.customer.rnc_or_id = ""
        self.customer.save(update_fields=["rnc_or_id"])
        self.invoice.refresh_from_db()

        report = build_invoice_dgii_mapping_report(self.invoice)
        codes = {i.code for i in report.blocking_issues}
        self.assertIn("MISSING_ISSUER_RNC", codes)
        self.assertIn("MISSING_CUSTOMER_RNC_OR_ID", codes)
        self.assertFalse(report.enough_internal_data_for_future_ecf_draft)

    def test_report_includes_line_snapshot_availability(self):
        report = build_invoice_dgii_mapping_report(self.invoice)
        by_field = {f.internal_field: f for f in report.line_fields}
        self.assertTrue(by_field["lines[].item_code_snapshot"].present)
        self.assertTrue(by_field["lines[].item_name_snapshot"].present)
        self.assertTrue(by_field["lines[].unit_snapshot"].present)
        self.assertTrue(by_field["lines[].tax_rate_snapshot"].present)

    def test_report_includes_totals(self):
        report = build_invoice_dgii_mapping_report(self.invoice)
        by_field = {f.internal_field: f for f in report.totals_fields}
        self.assertTrue(by_field["subtotal"].present)
        self.assertTrue(by_field["tax_total"].present)
        self.assertTrue(by_field["grand_total"].present)
        self.assertEqual(by_field["grand_total"].value_preview, "118.00")

    def test_report_returns_blocking_issues_for_incomplete_invoice(self):
        incomplete = Invoice.objects.create(
            issuer=self.issuer,
            customer=self.customer,
            invoice_direction="OUTBOUND",
            lifecycle_status="DRAFT",
            currency="DOP",
            issue_date="2026-01-01",
            created_by=self.user,
            internal_code="BCC-AR-2026-000502",
        )
        report = build_invoice_dgii_mapping_report(incomplete)
        self.assertTrue(report.blocking_issues)
        codes = {i.code for i in report.blocking_issues}
        self.assertIn("MISSING_FISCAL_DOCUMENT_TYPE", codes)
        self.assertIn("MISSING_INVOICE_LINES", codes)
        self.assertIn("NON_POSITIVE_GRAND_TOTAL", codes)
        self.assertIn(report.status, {DGIIMappingStatus.PARTIAL, DGIIMappingStatus.BLOCKED})
        self.assertFalse(report.enough_internal_data_for_future_ecf_draft)


class InspectDGIIMappingCommandTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="inspector", password="x")
        self.issuer = Organization.objects.create(
            legal_name="BCC Technologies",
            rnc="1310000000",
        )
        self.customer = Contact.objects.create(
            contact_type="CLIENT",
            legal_name="Client",
            rnc_or_id="123456789",
        )
        self.fiscal_type = FiscalDocumentType.objects.create(
            code="31",
            name="Factura de Crédito Fiscal Electrónica",
            document_group="INVOICE",
            direction="OUTBOUND",
        )
        self.invoice = Invoice.objects.create(
            issuer=self.issuer,
            customer=self.customer,
            invoice_direction="OUTBOUND",
            lifecycle_status="DRAFT",
            currency="DOP",
            issue_date="2026-01-01",
            created_by=self.user,
            internal_code="BCC-AR-2026-000601",
            fiscal_document_type_ref=self.fiscal_type,
        )
        InvoiceLine.objects.create(
            invoice=self.invoice,
            description="Service",
            quantity=Decimal("1.00"),
            unit_price=Decimal("50.00"),
            tax_amount=Decimal("9.00"),
            line_total=Decimal("59.00"),
            item_code_snapshot="SVC",
            item_name_snapshot="Service",
            unit_snapshot="SERVICE",
            tax_rate_snapshot="ITBIS_18",
            currency_snapshot="DOP",
        )

    def test_human_output_works(self):
        out = StringIO()
        call_command(
            "inspect_dgii_mapping",
            internal_code=self.invoice.internal_code,
            stdout=out,
        )
        output = out.getvalue()
        self.assertIn("DGII concept mapping report", output)
        self.assertIn("internal_code", output)
        self.assertIn("NOT DGII-compliant", output)
        self.assertIn(self.invoice.internal_code, output)

    def test_json_output_is_parseable(self):
        out = StringIO()
        call_command(
            "inspect_dgii_mapping",
            internal_code=self.invoice.internal_code,
            as_json=True,
            stdout=out,
        )
        payload = json.loads(out.getvalue())
        self.assertEqual(payload["internal_code"], self.invoice.internal_code)
        self.assertIn("fiscal_document_type", payload)
        self.assertIn("issues", payload)
        self.assertIn("enough_internal_data_for_future_ecf_draft", payload)
        self.assertEqual(payload["future_catalog"], TIPO_ECF_31_FUTURE_CATALOG)
        self.assertEqual(payload["catalog_status"], TIPO_ECF_31_CATALOG_STATUS)
        self.assertIn("source_inventory_status", payload)

    def test_strict_fails_on_blocking_issues(self):
        broken = Invoice.objects.create(
            issuer=self.issuer,
            customer=self.customer,
            invoice_direction="OUTBOUND",
            lifecycle_status="DRAFT",
            currency="DOP",
            issue_date="2026-01-01",
            created_by=self.user,
            internal_code="BCC-AR-2026-000602",
        )
        with self.assertRaises(CommandError):
            call_command(
                "inspect_dgii_mapping",
                internal_code=broken.internal_code,
                strict=True,
            )

    def test_command_creates_no_document_or_ecfdocument(self):
        before_docs = Document.objects.count()
        before_ecf = ECFDocument.objects.count()
        call_command("inspect_dgii_mapping", internal_code=self.invoice.internal_code)
        self.assertEqual(Document.objects.count(), before_docs)
        self.assertEqual(ECFDocument.objects.count(), before_ecf)


class DGIISourceAndCatalogScaffoldTests(TestCase):
    def test_dgii_inventory_file_exists(self):
        self.assertTrue(Path("docs/dgii/DGII_ECF_DOCUMENT_INVENTORY.md").exists())

    def test_sources_readme_exists(self):
        self.assertTrue(Path("docs/dgii/sources/README.md").exists())

    def test_tipo_ecf_31_catalog_markdown_exists(self):
        self.assertTrue(Path("docs/dgii/mapping/TIPO_ECF_31_FIELD_CATALOG.md").exists())

    def test_tipo_ecf_31_python_catalog_marked_pending(self):
        self.assertEqual(
            TIPO_ECF_31_CATALOG_STATUS,
            "SKELETON_PENDING_OFFICIAL_SOURCE_REVIEW",
        )

    def test_type_31_report_includes_catalog_fields_and_warning(self):
        user = get_user_model().objects.create_user(username="cat", password="x")
        issuer = Organization.objects.create(legal_name="BCC", rnc="1310000000")
        customer = Contact.objects.create(
            contact_type="CLIENT",
            legal_name="Client",
            rnc_or_id="123456789",
        )
        fiscal = FiscalDocumentType.objects.create(
            code="31",
            name="Factura de Crédito Fiscal Electrónica",
            document_group="INVOICE",
            direction="OUTBOUND",
        )
        invoice = Invoice.objects.create(
            issuer=issuer,
            customer=customer,
            invoice_direction="OUTBOUND",
            lifecycle_status="DRAFT",
            currency="DOP",
            issue_date="2026-01-01",
            created_by=user,
            internal_code="BCC-AR-2026-000701",
            fiscal_document_type_ref=fiscal,
        )
        InvoiceLine.objects.create(
            invoice=invoice,
            description="Service",
            quantity=Decimal("1.00"),
            unit_price=Decimal("10.00"),
            tax_amount=Decimal("1.80"),
            line_total=Decimal("11.80"),
        )
        report = build_invoice_dgii_mapping_report(invoice)
        self.assertEqual(report.future_catalog, "TIPO_ECF_31")
        self.assertEqual(report.catalog_status, "SKELETON_PENDING_OFFICIAL_SOURCE_REVIEW")
        self.assertTrue(
            any(i.code == "TIPO_ECF_31_CATALOG_PENDING_SOURCE_REVIEW" for i in report.issues)
        )
        self.assertIsNotNone(report.source_inventory_status)
        self.assertIn("summary", report.source_inventory_status)
