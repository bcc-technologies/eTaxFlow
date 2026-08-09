from io import StringIO

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from audit.models import AuditEvent
from contacts.models import Contact
from core.seed_demo import DEMO_CLIENT_RNC, SEED_INVOICE_MARKER
from documents.models import Document
from ecf.services.internal_invoice_xml import build_internal_invoice_xml
from invoicing.models import Invoice
from organizations.models import Organization
from core.seed_demo import DEMO_ISSUER_RNC


class MergeDuplicateContactsTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="merger", password="x")
        self.issuer = Organization.objects.create(
            legal_name="BCC Technologies",
            rnc=DEMO_ISSUER_RNC,
        )
        self.keeper = Contact.objects.create(
            contact_type="CLIENT",
            legal_name="Demo Client S.R.L.",
            commercial_name="Demo Client",
            email="demo.client@example.com",
            rnc_or_id=DEMO_CLIENT_RNC,
            is_active=True,
        )
        self.dup_a = Contact.objects.create(
            contact_type="CLIENT",
            legal_name="Customer",
            commercial_name="Customer",
            rnc_or_id=DEMO_CLIENT_RNC,
            is_active=True,
        )
        self.dup_b = Contact.objects.create(
            contact_type="CLIENT",
            legal_name="C",
            commercial_name="C",
            rnc_or_id=DEMO_CLIENT_RNC,
            is_active=True,
        )

    def test_dry_run_changes_nothing(self):
        invoice = Invoice.objects.create(
            issuer=self.issuer,
            customer=self.dup_a,
            invoice_direction="OUTBOUND",
            lifecycle_status="DRAFT",
            currency="DOP",
            issue_date="2026-01-01",
            created_by=self.user,
            internal_code="BCC-AR-2026-000401",
        )

        out = StringIO()
        call_command(
            "merge_duplicate_contacts",
            contact_type="CLIENT",
            rnc_or_id=DEMO_CLIENT_RNC,
            keep_pk=self.keeper.pk,
            stdout=out,
        )

        invoice.refresh_from_db()
        self.dup_a.refresh_from_db()
        self.assertEqual(invoice.customer_id, self.dup_a.pk)
        self.assertTrue(self.dup_a.is_active)
        self.assertIn("DRY-RUN", out.getvalue())
        self.assertIn("DRY-RUN only", out.getvalue())

    def test_apply_repoints_invoice_customer(self):
        invoice = Invoice.objects.create(
            issuer=self.issuer,
            customer=self.dup_a,
            invoice_direction="OUTBOUND",
            lifecycle_status="DRAFT",
            currency="DOP",
            issue_date="2026-01-01",
            created_by=self.user,
            internal_code="BCC-AR-2026-000402",
        )

        call_command(
            "merge_duplicate_contacts",
            contact_type="CLIENT",
            rnc_or_id=DEMO_CLIENT_RNC,
            keep_pk=self.keeper.pk,
            apply=True,
            reason="test merge invoices",
        )

        invoice.refresh_from_db()
        self.assertEqual(invoice.customer_id, self.keeper.pk)

    def test_apply_repoints_document_related_contact(self):
        upload = SimpleUploadedFile("doc.pdf", b"hello", content_type="application/pdf")
        doc = Document.objects.create(
            internal_code="BCC-DOC-2026-000401",
            document_direction="INBOUND",
            document_kind="OTHER",
            source="MANUAL_UPLOAD",
            original_filename="doc.pdf",
            issuer=self.issuer,
            related_contact=self.dup_b,
            created_by=self.user,
            file=upload,
        )

        call_command(
            "merge_duplicate_contacts",
            contact_type="CLIENT",
            rnc_or_id=DEMO_CLIENT_RNC,
            keep_pk=self.keeper.pk,
            apply=True,
        )

        doc.refresh_from_db()
        self.assertEqual(doc.related_contact_id, self.keeper.pk)

    def test_apply_soft_deactivates_duplicates(self):
        call_command(
            "merge_duplicate_contacts",
            contact_type="CLIENT",
            rnc_or_id=DEMO_CLIENT_RNC,
            keep_pk=self.keeper.pk,
            apply=True,
        )

        self.keeper.refresh_from_db()
        self.dup_a.refresh_from_db()
        self.dup_b.refresh_from_db()
        self.assertTrue(Contact.objects.filter(pk=self.dup_a.pk).exists())
        self.assertTrue(Contact.objects.filter(pk=self.dup_b.pk).exists())
        self.assertTrue(self.keeper.is_active)
        self.assertFalse(self.dup_a.is_active)
        self.assertFalse(self.dup_b.is_active)
        self.assertTrue(
            AuditEvent.objects.filter(
                event_type="contact_duplicate_merged",
                entity_id=self.keeper.pk,
            ).exists()
        )

    def test_refuses_invalid_keep_pk(self):
        outsider = Contact.objects.create(
            contact_type="CLIENT",
            legal_name="Other",
            rnc_or_id="555555555",
        )
        with self.assertRaises(CommandError):
            call_command(
                "merge_duplicate_contacts",
                contact_type="CLIENT",
                rnc_or_id=DEMO_CLIENT_RNC,
                keep_pk=outsider.pk,
                apply=True,
            )

    def test_refuses_mismatched_contact_type(self):
        # keep-pk is a CLIENT; target group is SUPPLIER demo key.
        Contact.objects.create(
            contact_type="SUPPLIER",
            legal_name="Demo Supplier S.R.L.",
            commercial_name="Demo Supplier",
            email="demo.supplier@example.com",
            rnc_or_id="987654321",
        )
        Contact.objects.create(
            contact_type="SUPPLIER",
            legal_name="Demo Supplier Dup",
            commercial_name="Demo Supplier",
            email="demo.supplier@example.com",
            rnc_or_id="987654321",
        )
        with self.assertRaises(CommandError):
            call_command(
                "merge_duplicate_contacts",
                contact_type="SUPPLIER",
                rnc_or_id="987654321",
                keep_pk=self.keeper.pk,
                apply=True,
            )

    def test_merge_is_idempotent(self):
        Invoice.objects.create(
            issuer=self.issuer,
            customer=self.dup_a,
            invoice_direction="OUTBOUND",
            lifecycle_status="DRAFT",
            currency="DOP",
            issue_date="2026-01-01",
            created_by=self.user,
            internal_code="BCC-AR-2026-000403",
        )

        call_command(
            "merge_duplicate_contacts",
            contact_type="CLIENT",
            rnc_or_id=DEMO_CLIENT_RNC,
            keep_pk=self.keeper.pk,
            apply=True,
        )
        audits_after_first = AuditEvent.objects.filter(
            event_type="contact_duplicate_merged"
        ).count()

        out = StringIO()
        call_command(
            "merge_duplicate_contacts",
            contact_type="CLIENT",
            rnc_or_id=DEMO_CLIENT_RNC,
            keep_pk=self.keeper.pk,
            apply=True,
            stdout=out,
        )

        self.assertIn("No changes needed", out.getvalue())
        self.assertEqual(
            AuditEvent.objects.filter(event_type="contact_duplicate_merged").count(),
            audits_after_first,
        )

    def test_diagnose_prints_suggested_merge_command(self):
        out = StringIO()
        call_command("diagnose_seed_duplicates", stdout=out)
        output = out.getvalue()
        self.assertIn("Suggested merge", output)
        self.assertIn("merge_duplicate_contacts", output)
        self.assertIn(f"--contact-type CLIENT", output)
        self.assertIn(f"--rnc-or-id {DEMO_CLIENT_RNC}", output)
        self.assertIn(f"--keep-pk {self.keeper.pk}", output)
        self.assertIn("--dry-run", output)

    def test_seed_bcc_after_merge_no_longer_warns(self):
        call_command(
            "merge_duplicate_contacts",
            contact_type="CLIENT",
            rnc_or_id=DEMO_CLIENT_RNC,
            keep_pk=self.keeper.pk,
            apply=True,
        )

        out = StringIO()
        call_command("seed_bcc", stdout=out)
        output = out.getvalue()
        self.assertIn("Demo BCC data seeded.", output)
        self.assertNotIn(
            f"duplicate Contact records for {{'contact_type': 'CLIENT', 'rnc_or_id': '{DEMO_CLIENT_RNC}'}}",
            output,
        )
        self.assertEqual(
            Invoice.objects.filter(notes__icontains=SEED_INVOICE_MARKER).count(),
            1,
        )

    def test_generate_internal_xml_still_works_after_merge(self):
        call_command("seed_bcc")
        call_command(
            "merge_duplicate_contacts",
            contact_type="CLIENT",
            rnc_or_id=DEMO_CLIENT_RNC,
            keep_pk=self.keeper.pk,
            apply=True,
        )

        seeded = Invoice.objects.filter(notes__icontains=SEED_INVOICE_MARKER).first()
        self.assertIsNotNone(seeded)
        self.assertEqual(seeded.customer_id, self.keeper.pk)
        xml_string = build_internal_invoice_xml(seeded)
        self.assertIn("<InternalInvoiceDraft", xml_string)

        call_command("generate_internal_xml", invoice_code=seeded.internal_code)
        self.assertTrue(
            Document.objects.filter(
                document_kind="XML",
                source="GENERATED",
                related_invoice=seeded,
            ).exists()
        )

    def test_refuses_non_demo_without_allow_flag(self):
        Contact.objects.create(
            contact_type="CLIENT",
            legal_name="Real A",
            rnc_or_id="555555555",
        )
        real_b = Contact.objects.create(
            contact_type="CLIENT",
            legal_name="Real B",
            rnc_or_id="555555555",
        )
        with self.assertRaises(CommandError):
            call_command(
                "merge_duplicate_contacts",
                contact_type="CLIENT",
                rnc_or_id="555555555",
                keep_pk=real_b.pk,
                apply=True,
            )
