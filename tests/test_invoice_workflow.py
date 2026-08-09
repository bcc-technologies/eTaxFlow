from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from audit.models import AuditEvent
from contacts.models import Contact
from ecf.models import ECFDocument
from fiscal.models import FiscalDocumentType, InternalDocumentCode, TaxRate, UnitOfMeasure
from invoicing.models import Invoice, InvoiceLine, ProductService
from organizations.models import Organization


class InvoiceWorkflowTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="tester", password="secret123")
        self.issuer = Organization.objects.create(
            legal_name="BCC Technologies",
            commercial_name="BCC Technologies",
            rnc="1310000000",
        )
        self.customer = Contact.objects.create(
            contact_type="CLIENT",
            legal_name="Customer Corp",
            commercial_name="Customer Corp",
            rnc_or_id="123456789",
        )
        self.invoice = Invoice.objects.create(
            issuer=self.issuer,
            customer=self.customer,
            invoice_direction="OUTBOUND",
            lifecycle_status="DRAFT",
            currency="DOP",
            issue_date="2026-01-01",
            created_by=self.user,
            internal_code="BCC-AR-2026-000100",
        )

    def test_valid_lifecycle_transitions(self):
        self.invoice.mark_reviewed()
        self.assertEqual(self.invoice.lifecycle_status, "REVIEWED")

        self.invoice.approve_invoice(self.user)
        self.assertEqual(self.invoice.lifecycle_status, "APPROVED")
        self.assertEqual(self.invoice.approved_by, self.user)

        InvoiceLine.objects.create(
            invoice=self.invoice,
            description="Consulting",
            quantity=1,
            unit_price=Decimal("100.00"),
            discount_amount=Decimal("0.00"),
            tax_rate=Decimal("18.00"),
            tax_amount=Decimal("18.00"),
            line_total=Decimal("118.00"),
        )

        self.invoice.issue_invoice()
        self.assertEqual(self.invoice.lifecycle_status, "ISSUED")

        self.invoice.archive_invoice()
        self.assertEqual(self.invoice.lifecycle_status, "ARCHIVED")

    def test_invalid_lifecycle_transition_raises(self):
        with self.assertRaises(ValidationError):
            self.invoice.issue_invoice()
        self.invoice.mark_reviewed()
        with self.assertRaises(ValidationError):
            self.invoice.archive_invoice()

    def test_approve_requires_approving_user(self):
        self.invoice.mark_reviewed()
        with self.assertRaises(ValidationError):
            self.invoice.approve_invoice(None)

    def test_issue_requires_line_and_positive_total(self):
        self.invoice.mark_reviewed()
        self.invoice.approve_invoice(self.user)
        with self.assertRaises(ValidationError):
            self.invoice.issue_invoice()

        InvoiceLine.objects.create(
            invoice=self.invoice,
            description="Free item",
            quantity=1,
            unit_price=Decimal("0.00"),
            discount_amount=Decimal("0.00"),
            tax_rate=Decimal("0.00"),
            tax_amount=Decimal("0.00"),
            line_total=Decimal("0.00"),
        )
        with self.assertRaises(ValidationError):
            self.invoice.issue_invoice()

    def test_status_transition_creates_audit_event(self):
        self.invoice.mark_reviewed()
        self.assertTrue(AuditEvent.objects.filter(event_type="invoice_status_changed", entity_id=self.invoice.pk).exists())


class SeedBCCCommandTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="tester", password="secret123")
        self.issuer = Organization.objects.create(
            legal_name="BCC Technologies",
            commercial_name="BCC Technologies",
            rnc="1310000000",
        )
        self.customer = Contact.objects.create(
            contact_type="CLIENT",
            legal_name="Customer Corp",
            commercial_name="Customer Corp",
            rnc_or_id="123456789",
        )
        self.invoice = Invoice.objects.create(
            issuer=self.issuer,
            customer=self.customer,
            invoice_direction="OUTBOUND",
            lifecycle_status="DRAFT",
            currency="DOP",
            issue_date="2026-01-01",
            created_by=self.user,
            internal_code="BCC-AR-2026-000999",
        )

    def test_seed_bcc_is_idempotent(self):
        from django.core.management import call_command

        call_command("seed_bcc")
        first_invoice_count = Invoice.objects.count()
        first_default_org = Organization.objects.filter(rnc="1310000000").count()
        first_fiscal_types = FiscalDocumentType.objects.count()
        first_tax_rates = TaxRate.objects.count()
        first_units = UnitOfMeasure.objects.count()
        first_products = ProductService.objects.count()

        call_command("seed_bcc")
        self.assertEqual(Invoice.objects.count(), first_invoice_count)
        self.assertEqual(Organization.objects.filter(rnc="1310000000").count(), first_default_org)
        self.assertEqual(FiscalDocumentType.objects.count(), first_fiscal_types)
        self.assertEqual(TaxRate.objects.count(), first_tax_rates)
        self.assertEqual(UnitOfMeasure.objects.count(), first_units)
        self.assertEqual(ProductService.objects.count(), first_products)

    def test_seed_bcc_runs_twice_without_duplicate_demo_invoice(self):
        from django.core.management import call_command

        call_command("seed_bcc")
        call_command("seed_bcc")

        seeded_invoices = Invoice.objects.filter(notes__icontains="SEEDED_BCC_DEMO_INVOICE")
        self.assertEqual(seeded_invoices.count(), 1)
        self.assertEqual(seeded_invoices.first().lines.count(), 2)

    def test_seed_bcc_handles_existing_duplicate_demo_contacts(self):
        from django.core.management import call_command
        from io import StringIO

        Contact.objects.create(
            contact_type="CLIENT",
            legal_name="Demo Client S.R.L.",
            commercial_name="Demo Client",
            rnc_or_id="123456789",
        )
        Contact.objects.create(
            contact_type="CLIENT",
            legal_name="Demo Client S.R.L.",
            commercial_name="Demo Client",
            rnc_or_id="123456789",
        )

        out = StringIO()
        call_command("seed_bcc", stdout=out)

        self.assertIn("Multiple Contact records found for {'contact_type': 'CLIENT', 'rnc_or_id': '123456789'}", out.getvalue())
        self.assertEqual(Contact.objects.filter(contact_type="CLIENT", rnc_or_id="123456789").count(), 3)

    def test_seeded_invoice_still_works_with_generate_internal_xml(self):
        from django.core.management import call_command
        from django.core.management import call_command as run_command
        from ecf.services.internal_invoice_xml import build_internal_invoice_xml

        call_command("seed_bcc")
        seeded_invoice = Invoice.objects.filter(notes__icontains="SEEDED_BCC_DEMO_INVOICE").first()
        self.assertIsNotNone(seeded_invoice)
        xml_string = build_internal_invoice_xml(seeded_invoice)
        self.assertIn("<InternalInvoiceDraft", xml_string)

    def test_seed_creates_ecf_placeholder(self):
        from django.core.management import call_command

        call_command("seed_bcc")
        invoice = Invoice.objects.filter(fiscal_document_type_ref__isnull=False).first()
        self.assertIsNotNone(invoice)
        self.assertTrue(ECFDocument.objects.filter(invoice=invoice).exists())

    def test_seed_populates_fiscal_catalog_and_normalized_invoice(self):
        from django.core.management import call_command

        call_command("seed_bcc")

        self.assertEqual(FiscalDocumentType.objects.count(), 10)
        self.assertTrue(FiscalDocumentType.objects.filter(code="31").exists())
        self.assertEqual(TaxRate.objects.count(), 3)
        self.assertTrue(TaxRate.objects.filter(code="ITBIS_18").exists())
        self.assertEqual(UnitOfMeasure.objects.count(), 3)
        self.assertTrue(UnitOfMeasure.objects.filter(code="SERVICE").exists())
        self.assertEqual(ProductService.objects.count(), 2)
        self.assertTrue(ProductService.objects.filter(code="SOFTWARE_DEV_SERVICE").exists())

        invoice = Invoice.objects.filter(fiscal_document_type_ref__isnull=False).first()
        self.assertIsNotNone(invoice)
        self.assertEqual(invoice.fiscal_document_type_ref.code, "31")
        self.assertFalse(bool(invoice.official_ncf))
        self.assertFalse(bool(invoice.official_encf))

        self.assertEqual(invoice.lines.count(), 2)
        for line in invoice.lines.all():
            self.assertIsNotNone(line.product_service)
            self.assertIsNotNone(line.unit)
            self.assertIsNotNone(line.tax_rate_ref)
            self.assertIsNotNone(line.item_code_snapshot)
            self.assertIsNotNone(line.item_name_snapshot)
            self.assertIsNotNone(line.unit_snapshot)
            self.assertIsNotNone(line.tax_rate_snapshot)
            self.assertIsNotNone(line.currency_snapshot)

    def test_invoice_line_snapshots_are_preserved_after_product_service_change(self):
        unit = UnitOfMeasure.objects.create(code="TESTU", name="Test Unit", symbol="TU")
        tax = TaxRate.objects.create(code="TESTTAX", name="Test Tax", rate=Decimal("15.00"), tax_type="OTHER", is_active=True)
        product = ProductService.objects.create(
            code="TEST_SERVICE",
            name="Test Service",
            item_type="SERVICE",
            default_unit=unit,
            default_tax_rate=tax,
            default_unit_price=Decimal("500.00"),
            is_active=True,
        )
        invoice = Invoice.objects.create(
            issuer=self.issuer,
            customer=self.customer,
            invoice_direction="OUTBOUND",
            lifecycle_status="DRAFT",
            currency="DOP",
            issue_date="2026-01-01",
            created_by=self.user,
            internal_code="BCC-AR-2026-000200",
        )

        line = InvoiceLine.objects.create(
            invoice=invoice,
            description="Test service",
            product_service=product,
            unit=unit,
            tax_rate_ref=tax,
            quantity=Decimal("2.00"),
            unit_price=Decimal("500.00"),
            discount_amount=Decimal("0.00"),
            tax_rate=Decimal("15.00"),
        )

        original_item_code = line.item_code_snapshot
        original_tax_rate_snapshot = line.tax_rate_snapshot
        original_unit_snapshot = line.unit_snapshot

        product.name = "Updated Service Name"
        product.save(update_fields=["name"])
        tax.rate = Decimal("18.00")
        tax.save(update_fields=["rate"])
        unit.code = "UPDATED"
        unit.save(update_fields=["code"])

        line.refresh_from_db()
        self.assertEqual(line.item_code_snapshot, original_item_code)
        self.assertEqual(line.tax_rate_snapshot, original_tax_rate_snapshot)
        self.assertEqual(line.unit_snapshot, original_unit_snapshot)

    def test_invoice_total_calculation_uses_tax_rate_ref(self):
        unit = UnitOfMeasure.objects.create(code="TESTUNIT", name="Test Unit", symbol="TU")
        tax = TaxRate.objects.create(code="TEST18", name="Test 18%", rate=Decimal("18.00"), tax_type="ITBIS", is_active=True)
        invoice = Invoice.objects.create(
            issuer=self.issuer,
            customer=self.customer,
            invoice_direction="OUTBOUND",
            lifecycle_status="DRAFT",
            currency="DOP",
            issue_date="2026-01-01",
            created_by=self.user,
            internal_code="BCC-AR-2026-000201",
        )

        InvoiceLine.objects.create(
            invoice=invoice,
            description="Tax ref line",
            unit=unit,
            tax_rate_ref=tax,
            quantity=Decimal("1.00"),
            unit_price=Decimal("100.00"),
            discount_amount=Decimal("0.00"),
        )

        invoice.refresh_from_db()
        self.assertEqual(invoice.tax_total, Decimal("18.00"))
        self.assertEqual(invoice.grand_total, Decimal("118.00"))

    def test_issued_invoice_rejects_line_edits(self):
        line = InvoiceLine.objects.create(
            invoice=self.invoice,
            description="Consulting",
            quantity=Decimal("1.00"),
            unit_price=Decimal("100.00"),
            discount_amount=Decimal("0.00"),
            tax_rate=Decimal("18.00"),
            tax_amount=Decimal("18.00"),
            line_total=Decimal("118.00"),
        )
        self.invoice.mark_reviewed()
        self.invoice.approve_invoice(self.user)
        self.invoice.issue_invoice()

        line.description = "Changed"
        with self.assertRaises(ValidationError):
            line.save()

    def test_issued_invoice_rejects_protected_header_edits(self):
        self.invoice.mark_reviewed()
        self.invoice.approve_invoice(self.user)
        InvoiceLine.objects.create(
            invoice=self.invoice,
            description="Consulting",
            quantity=Decimal("1.00"),
            unit_price=Decimal("100.00"),
            discount_amount=Decimal("0.00"),
            tax_rate=Decimal("18.00"),
            tax_amount=Decimal("18.00"),
            line_total=Decimal("118.00"),
        )
        self.invoice.issue_invoice()

        self.invoice.customer = self.customer
        with self.assertRaises(ValidationError):
            self.invoice.save()

    def test_internal_code_is_separate_from_official_ncf_and_encf(self):
        invoice = Invoice.objects.create(
            issuer=self.issuer,
            customer=self.customer,
            invoice_direction="OUTBOUND",
            lifecycle_status="DRAFT",
            currency="DOP",
            issue_date="2026-01-01",
            created_by=self.user,
            internal_code="BCC-AR-2026-000001",
            official_ncf="B01000000001",
            official_encf="E01000000001",
        )

        self.assertEqual(invoice.internal_code, "BCC-AR-2026-000001")
        self.assertEqual(invoice.official_ncf, "B01000000001")
        self.assertEqual(invoice.official_encf, "E01000000001")
