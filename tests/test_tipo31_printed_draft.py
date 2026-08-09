import hashlib

from django.core.management import call_command
from django.test import TestCase
from django.test.utils import captured_stdout

from audit.models import AuditEvent
from core.seed_demo import SEED_INVOICE_MARKER
from documents.models import Document
from ecf.models import ECFDocument
from ecf.printed.tipo31_printed_draft import (
    generate_tipo31_printed_draft_document,
)
from ecf.services.signing_placeholder import prepare_signing_placeholder
from fiscal.services.encf_sequences import allocate_next_encf
from invoicing.models import Invoice


class Tipo31PrintedDraftTests(TestCase):
    def setUp(self):
        call_command("seed_bcc")
        self.invoice = Invoice.objects.filter(notes__icontains=SEED_INVOICE_MARKER).get()
        allocate_next_encf(self.invoice, allow_demo=True, xsd_facet_demo=True)
        self.invoice.refresh_from_db()
        prepare_signing_placeholder(
            self.invoice,
            note="Local placeholder only; no real digital signature",
        )
        self.invoice.refresh_from_db()

    def test_generates_linked_non_production_pdf_with_metadata_and_audit(self):
        before_events = AuditEvent.objects.filter(
            event_type="tipo31_printed_draft_generated"
        ).count()
        document, created = generate_tipo31_printed_draft_document(
            self.invoice,
            allow_demo_encf=True,
        )
        self.assertTrue(created)
        self.assertEqual(document.document_kind, "PDF")
        self.assertEqual(document.source, "GENERATED")
        self.assertEqual(document.status, "STORED")
        self.assertEqual(document.mime_type, "application/pdf")
        self.assertEqual(document.related_invoice_id, self.invoice.pk)
        self.assertEqual(document.issuer_id, self.invoice.issuer_id)
        self.assertTrue(document.file_size > 0)
        self.assertEqual(len(document.sha256_hash), 64)
        document.file.open("rb")
        pdf_bytes = document.file.read()
        document.file.close()
        self.assertTrue(pdf_bytes.startswith(b"%PDF-1.4"))
        self.assertIn(b"NON_PRODUCTION_DRAFT", pdf_bytes)
        self.assertIn(b"NOT_DGII_COMPLIANT", pdf_bytes)
        self.assertIn(self.invoice.internal_code.encode("ascii"), pdf_bytes)
        self.assertIn(b"OMITIDO", pdf_bytes)  # no fake QR/security value
        self.assertEqual(document.sha256_hash, hashlib.sha256(pdf_bytes).hexdigest())
        self.assertEqual(
            AuditEvent.objects.filter(event_type="tipo31_printed_draft_generated").count(),
            before_events + 1,
        )
        audit = AuditEvent.objects.filter(
            event_type="tipo31_printed_draft_generated",
            entity_id=self.invoice.pk,
        ).latest("pk")
        self.assertEqual(audit.metadata["representation_status"], "NON_PRODUCTION_DRAFT")
        self.assertFalse(audit.metadata["dgii_approval_claim"])
        self.assertIsNone(audit.metadata["dgii_track_id"])

    def test_repeated_generation_reuses_byte_identical_document(self):
        first, created_first = generate_tipo31_printed_draft_document(
            self.invoice,
            allow_demo_encf=True,
        )
        first.file.open("rb")
        first_bytes = first.file.read()
        first.file.close()
        second, created_second = generate_tipo31_printed_draft_document(
            self.invoice,
            allow_demo_encf=True,
        )
        second.file.open("rb")
        second_bytes = second.file.read()
        second.file.close()
        self.assertTrue(created_first)
        self.assertFalse(created_second)
        self.assertEqual(first.pk, second.pk)
        self.assertEqual(first_bytes, second_bytes)

    def test_command_generates_pdf_and_preserves_non_production_state(self):
        with captured_stdout() as out:
            call_command(
                "generate_tipo31_printed_draft",
                internal_code=self.invoice.internal_code,
                allow_demo_encf=True,
            )
        output = out.getvalue()
        self.assertIn("Tipo 31 printed draft Document", output)
        self.assertIn("NON_PRODUCTION_DRAFT", output)
        self.assertIn("NOT_DGII_COMPLIANT", output)
        document = Document.objects.get(
            related_invoice=self.invoice,
            document_kind="PDF",
        )
        self.assertEqual(document.status, "STORED")
        ecf = ECFDocument.objects.filter(invoice=self.invoice).first()
        if ecf:
            self.assertIsNone(ecf.dgii_track_id)
