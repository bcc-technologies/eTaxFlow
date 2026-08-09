from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from audit.models import AuditEvent
from contacts.models import Contact
from documents.models import Document
from invoicing.models import Invoice
from organizations.models import Organization
from core.seed_demo import DEMO_ISSUER_RNC


class DocumentInvoiceLinkTests(TestCase):
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
        self.invoice = Invoice.objects.create(
            issuer=self.issuer,
            customer=self.customer,
            invoice_direction="OUTBOUND",
            lifecycle_status="DRAFT",
            currency="DOP",
            issue_date="2026-01-01",
            created_by=self.user,
            internal_code="BCC-AR-2026-000101",
        )

    def test_linking_document_to_invoice_creates_audit_event(self):
        upload = SimpleUploadedFile("document.pdf", b"hello world", content_type="application/pdf")
        doc = Document.objects.create(
            internal_code="BCC-DOC-2026-000001",
            document_direction="INBOUND",
            document_kind="INVOICE",
            source="MANUAL_UPLOAD",
            original_filename="document.pdf",
            issuer=self.issuer,
            related_contact=self.customer,
            created_by=self.user,
            file=upload,
        )
        self.assertFalse(AuditEvent.objects.filter(event_type="document_linked_to_invoice").exists())

        doc.related_invoice = self.invoice
        doc.save()

        self.assertTrue(AuditEvent.objects.filter(event_type="document_linked_to_invoice", entity_id=doc.pk).exists())
