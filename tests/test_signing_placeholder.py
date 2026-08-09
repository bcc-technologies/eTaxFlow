from datetime import date
from decimal import Decimal
from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from audit.models import AuditEvent
from contacts.models import Contact
from documents.models import Document
from ecf.dgii.mapping import build_invoice_dgii_mapping_report
from ecf.models import ECFDocument
from ecf.services.signing_placeholder import (
    SigningPlaceholderError,
    attempt_real_signing,
    prepare_signing_placeholder,
)
from fiscal.models import ENCFSequenceRange, FiscalDocumentType
from fiscal.services.encf_sequences import allocate_next_encf
from invoicing.models import Invoice, InvoiceLine
from organizations.models import Organization


class ECFDocumentSigningDefaultsTests(TestCase):
    def test_defaults_to_unsigned_none(self):
        user = get_user_model().objects.create_user(username="sigdef", password="x")
        issuer = Organization.objects.create(legal_name="BCC", rnc="1310000200")
        customer = Contact.objects.create(
            contact_type="CLIENT", legal_name="Client", rnc_or_id="123456711"
        )
        invoice = Invoice.objects.create(
            issuer=issuer,
            customer=customer,
            invoice_direction="OUTBOUND",
            lifecycle_status="DRAFT",
            currency="DOP",
            issue_date="2026-01-01",
            created_by=user,
            internal_code="BCC-AR-2026-001001",
        )
        ecf = ECFDocument.objects.create(invoice=invoice)
        self.assertEqual(ecf.signing_status, "UNSIGNED")
        self.assertEqual(ecf.signing_mode, "NONE")
        self.assertIsNone(ecf.signature_datetime)
        self.assertFalse(ecf.has_real_signed_artifact)


class SigningPlaceholderServiceTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="sigsvc", password="x")
        self.issuer = Organization.objects.create(legal_name="BCC", rnc="1310000201")
        self.customer = Contact.objects.create(
            contact_type="CLIENT", legal_name="Client", rnc_or_id="123456712"
        )
        self.fiscal = FiscalDocumentType.objects.create(
            code="31",
            name="Factura de Crédito Fiscal Electrónica",
            document_group="INVOICE",
            direction="OUTBOUND",
        )
        ENCFSequenceRange.objects.create(
            issuer=self.issuer,
            fiscal_document_type=self.fiscal,
            prefix="DEMO-E31-",
            start_number=1,
            end_number=100,
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
            internal_code="BCC-AR-2026-001002",
            fiscal_document_type_ref=self.fiscal,
        )
        InvoiceLine.objects.create(
            invoice=self.invoice,
            description="Service",
            quantity=Decimal("1.00"),
            unit_price=Decimal("10.00"),
            tax_amount=Decimal("1.80"),
            line_total=Decimal("11.80"),
        )

    def test_refuses_without_official_encf(self):
        self.invoice.sequence_expiration_date = date(2030, 12, 31)
        self.invoice.save(update_fields=["sequence_expiration_date"])
        with self.assertRaises(SigningPlaceholderError):
            prepare_signing_placeholder(self.invoice)

    def test_refuses_without_sequence_expiration_date(self):
        self.invoice.official_encf = "DEMO-E31-000010"
        self.invoice.sequence_expiration_date = None
        self.invoice.save(update_fields=["official_encf", "sequence_expiration_date"])
        with self.assertRaises(SigningPlaceholderError):
            prepare_signing_placeholder(self.invoice)

    def test_prepare_creates_ecf_placeholder_without_signed_xml_or_trackid(self):
        allocate_next_encf(self.invoice, allow_demo=True)
        self.invoice.refresh_from_db()
        before_docs = Document.objects.count()
        before_status = self.invoice.lifecycle_status

        ecf = prepare_signing_placeholder(
            self.invoice,
            actor=self.user,
            note="Local placeholder only; no real digital signature",
        )
        self.invoice.refresh_from_db()
        ecf.refresh_from_db()

        self.assertEqual(ecf.signing_status, "SIGNING_PLACEHOLDER")
        self.assertEqual(ecf.signing_mode, "PLACEHOLDER_ONLY")
        self.assertIsNotNone(ecf.signature_datetime)
        self.assertIsNotNone(ecf.signing_attempted_at)
        self.assertIsNone(ecf.signing_completed_at)
        self.assertFalse(bool(ecf.xml_signed_file))
        self.assertIsNone(ecf.dgii_track_id)
        self.assertIn("no real digital signature", ecf.signature_placeholder_note.lower())
        self.assertEqual(self.invoice.lifecycle_status, before_status)
        self.assertTrue(
            AuditEvent.objects.filter(
                event_type="signing_placeholder_prepared",
                entity_type="Invoice",
                entity_id=self.invoice.pk,
            ).exists()
        )
        self.assertEqual(Document.objects.count(), before_docs)

    def test_attempt_real_signing_is_blocked(self):
        with self.assertRaises(NotImplementedError) as ctx:
            attempt_real_signing(self.invoice)
        self.assertIn("not implemented", str(ctx.exception).lower())
        self.assertIn("private keys", str(ctx.exception).lower())


class SigningPlaceholderCommandTests(TestCase):
    def setUp(self):
        call_command("seed_bcc")
        self.invoice = Invoice.objects.filter(notes__icontains="SEEDED_BCC_DEMO_INVOICE").get()
        # Ensure prerequisites for placeholder (seed does not allocate eNCF / may reset signing).
        if not self.invoice.official_encf:
            allocate_next_encf(self.invoice, allow_demo=True)
            self.invoice.refresh_from_db()

    def test_dry_run_does_not_mutate(self):
        before_ecf = ECFDocument.objects.filter(invoice=self.invoice).first()
        before_status = before_ecf.signing_status if before_ecf else None
        before_dt = before_ecf.signature_datetime if before_ecf else None
        out = StringIO()
        call_command(
            "prepare_signing_placeholder",
            internal_code=self.invoice.internal_code,
            dry_run=True,
            stdout=out,
        )
        after = ECFDocument.objects.filter(invoice=self.invoice).first()
        self.assertEqual(getattr(after, "signing_status", None), before_status)
        self.assertEqual(getattr(after, "signature_datetime", None), before_dt)
        self.assertIn("Dry-run only", out.getvalue())

    def test_apply_creates_placeholder(self):
        out = StringIO()
        call_command(
            "prepare_signing_placeholder",
            internal_code=self.invoice.internal_code,
            apply=True,
            note="Local placeholder only; no real digital signature",
            stdout=out,
        )
        ecf = ECFDocument.objects.get(invoice=self.invoice)
        self.assertEqual(ecf.signing_status, "SIGNING_PLACEHOLDER")
        self.assertEqual(ecf.signing_mode, "PLACEHOLDER_ONLY")
        self.assertIsNotNone(ecf.signature_datetime)
        self.assertIn("Prepared signing placeholder", out.getvalue())

    def test_apply_refuses_without_encf(self):
        self.invoice.official_encf = None
        self.invoice.save(update_fields=["official_encf"])
        with self.assertRaises(CommandError):
            call_command(
                "prepare_signing_placeholder",
                internal_code=self.invoice.internal_code,
                apply=True,
            )


class SigningPlaceholderMappingTests(TestCase):
    def test_mapping_after_placeholder_fecha_available_signature_missing(self):
        call_command("seed_bcc")
        invoice = Invoice.objects.filter(notes__icontains="SEEDED_BCC_DEMO_INVOICE").get()
        if not invoice.official_encf:
            allocate_next_encf(invoice, allow_demo=True)
            invoice.refresh_from_db()

        before_docs = Document.objects.count()
        before_ecf_count = ECFDocument.objects.count()
        prepare_signing_placeholder(invoice, note="test placeholder")
        invoice.refresh_from_db()

        report = build_invoice_dgii_mapping_report(invoice)
        missing = {item["field"] for item in report.missing_required_fields}
        self.assertNotIn("FechaHoraFirma", missing)
        self.assertIn("Signature", missing)
        self.assertIn("NOT_DGII_COMPLIANT", report.compliance_claim)
        codes = {i.code for i in report.issues}
        self.assertIn("SIGNING_PLACEHOLDER_ONLY", codes)
        identity = {f.internal_field: f for f in report.identity_fields}
        self.assertTrue(identity["ecf_document.signature_datetime"].present)
        self.assertFalse(identity["ecf_document.xml_signed_file"].present)
        self.assertEqual(Document.objects.count(), before_docs)
        self.assertEqual(ECFDocument.objects.count(), before_ecf_count)
