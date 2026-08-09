from datetime import date, timedelta
from decimal import Decimal
from io import StringIO

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from audit.models import AuditEvent
from contacts.models import Contact
from documents.models import Document
from ecf.dgii.mapping import build_invoice_dgii_mapping_report
from ecf.models import ECFDocument
from fiscal.models import ENCFSequenceRange, FiscalDocumentType
from fiscal.services.encf_sequences import (
    ENCFAllocationError,
    allocate_next_encf,
    preview_next_encf,
)
from invoicing.models import Invoice, InvoiceLine
from organizations.models import Organization


class ENCFSequenceRangeModelTests(TestCase):
    def setUp(self):
        self.issuer = Organization.objects.create(legal_name="BCC", rnc="1310000100")
        self.fiscal = FiscalDocumentType.objects.create(
            code="31",
            name="Factura de Crédito Fiscal Electrónica",
            document_group="INVOICE",
            direction="OUTBOUND",
        )

    def test_dev_demo_range_can_be_created(self):
        seq = ENCFSequenceRange.objects.create(
            issuer=self.issuer,
            fiscal_document_type=self.fiscal,
            prefix="DEMO-E31-",
            start_number=1,
            end_number=100,
            next_number=1,
            number_pad_width=6,
            sequence_expiration_date=date.today() + timedelta(days=365),
            environment="DEV",
            source="MANUAL_DEMO",
            is_authorized_by_dgii=False,
        )
        self.assertEqual(seq.peek_next_encf(), "DEMO-E31-000001")
        self.assertTrue(seq.is_demo_or_unauthorized)

    def test_production_range_requires_dgii_authorization_flag(self):
        with self.assertRaises(ValidationError):
            ENCFSequenceRange.objects.create(
                issuer=self.issuer,
                fiscal_document_type=self.fiscal,
                prefix="E31",
                start_number=1,
                end_number=10,
                next_number=1,
                sequence_expiration_date=date.today() + timedelta(days=30),
                environment="PRODUCTION",
                source="MANUAL_AUTHORIZED",
                is_authorized_by_dgii=False,
            )


class ENCFAllocationServiceTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="alloc", password="x")
        self.issuer = Organization.objects.create(legal_name="BCC", rnc="1310000101")
        self.customer = Contact.objects.create(
            contact_type="CLIENT",
            legal_name="Client",
            rnc_or_id="123456701",
        )
        self.fiscal = FiscalDocumentType.objects.create(
            code="31",
            name="Factura de Crédito Fiscal Electrónica",
            document_group="INVOICE",
            direction="OUTBOUND",
        )
        self.range = ENCFSequenceRange.objects.create(
            issuer=self.issuer,
            fiscal_document_type=self.fiscal,
            prefix="DEMO-E31-",
            start_number=1,
            end_number=3,
            next_number=1,
            number_pad_width=6,
            sequence_expiration_date=date(2030, 12, 31),
            environment="DEV",
            source="MANUAL_DEMO",
            is_authorized_by_dgii=False,
        )
        self.invoice = Invoice.objects.create(
            issuer=self.issuer,
            customer=self.customer,
            invoice_direction="OUTBOUND",
            lifecycle_status="DRAFT",
            currency="DOP",
            issue_date="2026-01-01",
            created_by=self.user,
            internal_code="BCC-AR-2026-000901",
            fiscal_document_type_ref=self.fiscal,
        )
        InvoiceLine.objects.create(
            invoice=self.invoice,
            description="Service",
            quantity=Decimal("1.00"),
            unit_price=Decimal("100.00"),
            tax_amount=Decimal("18.00"),
            line_total=Decimal("118.00"),
        )

    def test_refuses_invoice_without_issuer(self):
        inv = Invoice(
            customer=self.customer,
            invoice_direction="OUTBOUND",
            lifecycle_status="DRAFT",
            currency="DOP",
            issue_date="2026-01-01",
            created_by=self.user,
            internal_code="BCC-AR-2026-000902",
            fiscal_document_type_ref=self.fiscal,
        )
        # Unsaved invoice with no issuer_id — validation must fail before DB write.
        self.assertIsNone(inv.issuer_id)
        with self.assertRaises(ENCFAllocationError):
            allocate_next_encf(inv, allow_demo=True)

    def test_refuses_invoice_without_fiscal_document_type_ref(self):
        self.invoice.fiscal_document_type_ref = None
        self.invoice.save(update_fields=["fiscal_document_type_ref"])
        with self.assertRaises(ENCFAllocationError):
            allocate_next_encf(self.invoice, allow_demo=True)

    def test_refuses_invoice_that_already_has_official_encf(self):
        self.invoice.official_encf = "DEMO-E31-000099"
        self.invoice.save(update_fields=["official_encf"])
        with self.assertRaises(ENCFAllocationError):
            allocate_next_encf(self.invoice, allow_demo=True)

    def test_refuses_demo_range_without_allow_demo(self):
        with self.assertRaises(ENCFAllocationError):
            allocate_next_encf(self.invoice, allow_demo=False)

    def test_allocates_deterministic_encf_and_increments(self):
        before_docs = Document.objects.count()
        before_ecf = ECFDocument.objects.count()
        value = allocate_next_encf(self.invoice, actor=self.user, allow_demo=True)
        self.assertEqual(value, "DEMO-E31-000001")
        self.invoice.refresh_from_db()
        self.range.refresh_from_db()
        self.assertEqual(self.invoice.official_encf, "DEMO-E31-000001")
        self.assertEqual(self.invoice.sequence_expiration_date, date(2030, 12, 31))
        self.assertEqual(self.range.next_number, 2)
        self.assertTrue(
            AuditEvent.objects.filter(
                event_type="encf_allocated",
                entity_type="Invoice",
                entity_id=self.invoice.pk,
            ).exists()
        )
        self.assertEqual(Document.objects.count(), before_docs)
        self.assertEqual(ECFDocument.objects.count(), before_ecf)

    def test_refuses_exhausted_range(self):
        self.range.next_number = self.range.end_number + 1
        self.range.save()
        with self.assertRaises(ENCFAllocationError):
            allocate_next_encf(self.invoice, allow_demo=True)

    def test_refuses_expired_range(self):
        self.range.sequence_expiration_date = date.today() - timedelta(days=1)
        self.range.save()
        with self.assertRaises(ENCFAllocationError):
            allocate_next_encf(self.invoice, allow_demo=True)


class ENCFAllocationCommandTests(TestCase):
    def setUp(self):
        call_command("seed_bcc")
        self.invoice = Invoice.objects.filter(notes__icontains="SEEDED_BCC_DEMO_INVOICE").get()

    def test_dry_run_does_not_mutate(self):
        before_encf = self.invoice.official_encf
        seq = ENCFSequenceRange.objects.filter(prefix="DEMO-E31-", is_active=True).first()
        self.assertIsNotNone(seq)
        before_next = seq.next_number
        out = StringIO()
        call_command(
            "allocate_demo_encf",
            internal_code=self.invoice.internal_code,
            stdout=out,
        )
        self.invoice.refresh_from_db()
        seq.refresh_from_db()
        self.assertEqual(self.invoice.official_encf, before_encf)
        self.assertEqual(seq.next_number, before_next)
        self.assertIn("Dry-run only", out.getvalue())
        self.assertIn("DEMO-E31-", out.getvalue())

    def test_apply_requires_allow_demo_and_allocates(self):
        with self.assertRaises(CommandError):
            call_command(
                "allocate_demo_encf",
                internal_code=self.invoice.internal_code,
                apply=True,
            )
        out = StringIO()
        call_command(
            "allocate_demo_encf",
            internal_code=self.invoice.internal_code,
            allow_demo=True,
            apply=True,
            stdout=out,
        )
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.official_encf, "DEMO-E31-000001")
        self.assertIn("Allocated eNCF", out.getvalue())


class ENCFSeedAndMappingTests(TestCase):
    def test_seed_creates_demo_range_idempotently_without_allocating(self):
        call_command("seed_bcc")
        call_command("seed_bcc")
        self.assertEqual(
            ENCFSequenceRange.objects.filter(prefix="DEMO-E31-", environment="DEV").count(),
            1,
        )
        seeded = Invoice.objects.filter(notes__icontains="SEEDED_BCC_DEMO_INVOICE").get()
        self.assertIsNone(seeded.official_encf)

    def test_mapping_after_allocation_shows_encf_but_not_compliant(self):
        call_command("seed_bcc")
        seeded = Invoice.objects.filter(notes__icontains="SEEDED_BCC_DEMO_INVOICE").get()
        before_docs = Document.objects.count()
        before_ecf = ECFDocument.objects.count()
        allocate_next_encf(seeded, allow_demo=True)
        seeded.refresh_from_db()
        report = build_invoice_dgii_mapping_report(seeded)
        missing = {item["field"] for item in report.missing_required_fields}
        self.assertNotIn("eNCF", missing)
        self.assertIn("FechaHoraFirma", missing)
        self.assertIn("Signature", missing)
        self.assertIn("NOT_DGII_COMPLIANT", report.compliance_claim)
        codes = {i.code for i in report.issues}
        self.assertIn("DEMO_OR_UNAUTHORIZED_ENCF", codes)
        self.assertEqual(Document.objects.count(), before_docs)
        self.assertEqual(ECFDocument.objects.count(), before_ecf)
