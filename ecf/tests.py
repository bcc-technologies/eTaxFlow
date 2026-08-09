from decimal import Decimal
from io import StringIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from audit.models import AuditEvent
from contacts.models import Contact
from documents.models import Document
from ecf.models import ECFDocument
from ecf.services.internal_invoice_xml import build_internal_invoice_xml
from ecf.services.internal_xml_documents import generate_internal_xml_document
from fiscal.models import FiscalDocumentType, TaxRate, UnitOfMeasure
from invoicing.models import Invoice, InvoiceLine, ProductService
from organizations.models import Organization
from core.seed_demo import DEMO_ISSUER_RNC


class InternalInvoiceXMLTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="tester", password="secret123")
        self.issuer = Organization.objects.create(
            legal_name="BCC Technologies",
            commercial_name="BCC Technologies",
            rnc=DEMO_ISSUER_RNC,
        )
        self.customer = Contact.objects.create(
            contact_type="CLIENT",
            legal_name="Customer Corp",
            commercial_name="Customer Corp",
            rnc_or_id="123456789",
        )
        self.tax_rate = TaxRate.objects.create(
            code="TEST18",
            name="Test 18%",
            rate=Decimal("18.00"),
            tax_type="ITBIS",
            is_active=True,
        )
        self.unit = UnitOfMeasure.objects.create(code="SERVICE", name="Service", symbol="SRV", is_active=True)
        self.fiscal_type = FiscalDocumentType.objects.create(
            code="31",
            name="Factura de Crédito Fiscal Electrónica",
            description="Demo fiscal document type placeholder.",
            document_group="INVOICE",
            direction="OUTBOUND",
            is_electronic=True,
            is_active=True,
            requires_customer_rnc=True,
            requires_printed_representation=False,
            affects_accounts_receivable=True,
            affects_accounts_payable=True,
        )

        self.invoice = Invoice.objects.create(
            issuer=self.issuer,
            customer=self.customer,
            invoice_direction="OUTBOUND",
            lifecycle_status="DRAFT",
            currency="DOP",
            issue_date="2026-01-01",
            created_by=self.user,
            internal_code="BCC-AR-2026-000150",
            fiscal_document_type_ref=self.fiscal_type,
        )

        self.line = InvoiceLine.objects.create(
            invoice=self.invoice,
            line_order=1,
            description="Consulting",
            product_service=ProductService.objects.create(
                code="TEST_SERVICE",
                name="Test Service",
                item_type="SERVICE",
                default_unit=self.unit,
                default_tax_rate=self.tax_rate,
                default_unit_price=Decimal("100.00"),
                is_active=True,
            ),
            unit=self.unit,
            tax_rate_ref=self.tax_rate,
            quantity=Decimal("2.00"),
            unit_price=Decimal("100.00"),
            discount_amount=Decimal("0.00"),
            tax_rate=Decimal("18.00"),
            tax_amount=Decimal("36.00"),
            line_total=Decimal("236.00"),
        )

    def test_build_internal_invoice_xml_returns_valid_string(self):
        xml_string = build_internal_invoice_xml(self.invoice)
        self.assertIn("<InternalInvoiceDraft", xml_string)
        self.assertIn("<InternalCode>BCC-AR-2026-000150</InternalCode>", xml_string)
        self.assertIn("<TaxRateSnapshot>TEST18</TaxRateSnapshot>", xml_string)
        self.assertIn("This XML is an internal normalized draft", xml_string)

    def test_generate_internal_xml_document_creates_document(self):
        document, created = generate_internal_xml_document(self.invoice, created_by=self.user)
        self.assertTrue(created)
        self.assertEqual(document.document_kind, "XML")
        self.assertEqual(document.source, "GENERATED")
        self.assertEqual(document.related_invoice, self.invoice)
        self.assertEqual(document.mime_type, "application/xml")
        self.assertTrue(document.sha256_hash)
        self.assertTrue(Document.objects.filter(pk=document.pk).exists())
        self.assertTrue(AuditEvent.objects.filter(event_type="internal_xml_draft_generated", entity_id=self.invoice.pk).exists())

    def test_generate_internal_xml_document_is_idempotent(self):
        first_document, first_created = generate_internal_xml_document(self.invoice, created_by=self.user)
        second_document, second_created = generate_internal_xml_document(self.invoice, created_by=self.user)
        self.assertTrue(first_created)
        self.assertFalse(second_created)
        self.assertEqual(first_document.pk, second_document.pk)

    def test_generate_internal_xml_document_requires_invoice(self):
        with self.assertRaises(ValidationError):
            generate_internal_xml_document(None, created_by=self.user)

    def test_build_internal_invoice_xml_root_attributes_and_order(self):
        xml_string = build_internal_invoice_xml(self.invoice)
        self.assertIn('schema_name="ETAXFLOW_INTERNAL_INVOICE"', xml_string)
        self.assertIn('schema_version="1.0"', xml_string)
        self.assertIn('purpose="INTERNAL_DRAFT_ONLY"', xml_string)
        self.assertIn('dgii_compliance="NOT_DGII_COMPLIANT"', xml_string)
        self.assertLess(xml_string.index("<InternalCode>"), xml_string.index("<InvoiceDirection>"))
        self.assertLess(xml_string.index("<ProductServiceCode>"), xml_string.index("<ItemCodeSnapshot>"))

    def test_generate_internal_xml_document_does_not_create_ecf_document(self):
        self.assertEqual(ECFDocument.objects.count(), 0)
        document, created = generate_internal_xml_document(self.invoice, created_by=self.user)
        self.assertTrue(created)
        self.assertEqual(ECFDocument.objects.count(), 0)

    def test_generate_internal_xml_document_creates_new_document_for_changed_invoice(self):
        first_document, first_created = generate_internal_xml_document(self.invoice, created_by=self.user)
        self.assertTrue(first_created)
        line = self.invoice.lines.first()
        line.item_name_snapshot = "Modified Service Name"
        line.save()
        second_document, second_created = generate_internal_xml_document(self.invoice, created_by=self.user)
        self.assertTrue(second_created)
        self.assertNotEqual(first_document.pk, second_document.pk)

    def test_generate_internal_xml_manage_command_stdout_and_invalid_code(self):
        out = StringIO()
        with patch("sys.stdout", new=out):
            call_command(
                "generate_internal_xml",
                internal_code=self.invoice.internal_code,
                stdout_flag=True,
            )
        output = out.getvalue()
        self.assertIn("<InternalInvoiceDraft", output)
        self.assertIn(self.invoice.internal_code, output)

        with self.assertRaises(CommandError):
            with patch("sys.stdout", new=out):
                call_command(
                    "generate_internal_xml",
                    internal_code="DOES_NOT_EXIST",
                    stdout_flag=True,
                )

    def test_generate_internal_xml_manage_command_invoice_id(self):
        out = StringIO()
        with patch("sys.stdout", new=out):
            call_command(
                "generate_internal_xml",
                invoice_id=self.invoice.pk,
                stdout_flag=True,
            )
        self.assertIn("<InternalInvoiceDraft", out.getvalue())

    def test_generate_internal_xml_manage_command_saves_document(self):
        out = StringIO()
        with patch("sys.stdout", new=out):
            call_command("generate_internal_xml", internal_code=self.invoice.internal_code)
        output = out.getvalue()
        self.assertIn("Saved internal XML draft", output)
        self.assertTrue(Document.objects.filter(related_invoice=self.invoice, document_kind="XML", source="GENERATED").exists())

    def test_generate_internal_xml_manage_command_reuses_existing_document(self):
        with patch("sys.stdout", new=StringIO()):
            call_command("generate_internal_xml", internal_code=self.invoice.internal_code)
        out = StringIO()
        with patch("sys.stdout", new=out):
            call_command("generate_internal_xml", internal_code=self.invoice.internal_code)
        self.assertIn("Reused existing internal XML draft", out.getvalue())

    def test_build_internal_invoice_xml_rejects_missing_required_line_fields(self):
        line = self.invoice.lines.first()
        InvoiceLine.objects.filter(pk=line.pk).update(tax_rate_snapshot=None)
        with self.assertRaises(ValidationError):
            build_internal_invoice_xml(self.invoice)
