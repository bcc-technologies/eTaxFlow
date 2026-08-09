from io import BytesIO
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from audit.models import AuditEvent
from contacts.models import Contact
from documents.models import Document
from invoicing.models import Invoice, InvoiceLine
from organizations.models import Organization
from fiscal.models import InternalDocumentCode
from core.seed_demo import DEMO_ISSUER_RNC


class ETaxFlowModelTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="tester", password="secret123")
        self.issuer = Organization.objects.create(
            legal_name="BARREIRO CASANOVA CASTILLO TECHNOLOGIES, S.R.L.",
            commercial_name="BCC Technologies",
            rnc=DEMO_ISSUER_RNC,
            address="Santo Domingo",
            phone="809-000-0000",
            email="info@bcc.com",
            is_default_issuer=True,
        )

    def test_internal_code_generation_by_prefix_and_year(self):
        code = InternalDocumentCode.generate_code(prefix="AR", year=2026)
        self.assertEqual(code, "BCC-AR-2026-000001")

        code_two = InternalDocumentCode.generate_code(prefix="AR", year=2026)
        self.assertEqual(code_two, "BCC-AR-2026-000002")

    def test_document_upload_creates_sha_and_size(self):
        upload = SimpleUploadedFile("invoice.pdf", b"hello world", content_type="application/pdf")
        doc = Document.objects.create(
            internal_code="BCC-DOC-2026-000001",
            document_direction="OUTBOUND",
            document_kind="PDF",
            source="MANUAL_UPLOAD",
            original_filename="invoice.pdf",
            file=upload,
            issuer=self.issuer,
            created_by=self.user,
        )

        self.assertEqual(doc.file_size, 11)
        self.assertEqual(doc.sha256_hash, "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9")

    def test_invoice_total_calculation_uses_decimal(self):
        invoice = Invoice.objects.create(
            issuer=self.issuer,
            customer=self._create_contact(),
            invoice_direction="OUTBOUND",
            lifecycle_status="DRAFT",
            currency="DOP",
            issue_date="2026-01-01",
            created_by=self.user,
            internal_code="BCC-AR-2026-000001",
        )
        InvoiceLine.objects.create(
            invoice=invoice,
            description="Consulting",
            quantity=Decimal("2"),
            unit_price=Decimal("100.50"),
            discount_amount=Decimal("10.00"),
            tax_rate=Decimal("18"),
            tax_amount=Decimal("16.29"),
            line_total=Decimal("206.79"),
        )

        invoice.refresh_from_db()
        self.assertEqual(invoice.subtotal, Decimal("201.00"))
        self.assertEqual(invoice.tax_total, Decimal("16.29"))
        self.assertEqual(invoice.grand_total, Decimal("207.29"))

    def test_internal_code_is_separate_from_official_ncf_and_encf(self):
        invoice = Invoice.objects.create(
            issuer=self.issuer,
            customer=self._create_contact(),
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

    def test_audit_event_created_on_document_upload(self):
        upload = SimpleUploadedFile("note.txt", b"hello", content_type="text/plain")
        Document.objects.create(
            internal_code="BCC-DOC-2026-000001",
            document_direction="INTERNAL",
            document_kind="OTHER",
            source="MANUAL_UPLOAD",
            original_filename="note.txt",
            file=upload,
            issuer=self.issuer,
            created_by=self.user,
        )

        self.assertTrue(AuditEvent.objects.filter(event_type="document_uploaded").exists())

    def test_audit_event_created_on_invoice_status_change(self):
        invoice = Invoice.objects.create(
            issuer=self.issuer,
            customer=self._create_contact(),
            invoice_direction="OUTBOUND",
            lifecycle_status="DRAFT",
            currency="DOP",
            issue_date="2026-01-01",
            created_by=self.user,
            internal_code="BCC-AR-2026-000001",
        )
        invoice.lifecycle_status = "REVIEWED"
        invoice.save()

        self.assertTrue(AuditEvent.objects.filter(event_type="invoice_status_changed").exists())

    def _create_contact(self):
        return Contact.objects.create(
            contact_type="CLIENT",
            legal_name="Customer Corp",
            commercial_name="Customer Corp",
            rnc_or_id="123456789",
            id_type="RNC",
            address="Santo Domingo",
            phone="809-111-1111",
            email="customer@example.com",
            tax_category="GENERAL",
            is_active=True,
        )
