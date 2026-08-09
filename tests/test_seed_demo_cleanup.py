from decimal import Decimal
from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase

from contacts.models import Contact
from contacts.natural_keys import resolve_contact_by_natural_key
from core.seed_demo import DEMO_CLIENT_RNC, SEED_INVOICE_MARKER
from documents.models import Document
from ecf.services.internal_invoice_xml import build_internal_invoice_xml
from invoicing.models import Invoice, InvoiceLine
from organizations.models import Organization
from core.seed_demo import DEMO_ISSUER_RNC


class DiagnoseSeedDuplicatesTests(TestCase):
    def test_diagnose_reports_duplicates_without_failing(self):
        Contact.objects.create(
            contact_type="CLIENT",
            legal_name="Demo Client S.R.L.",
            commercial_name="Demo Client",
            rnc_or_id=DEMO_CLIENT_RNC,
        )
        Contact.objects.create(
            contact_type="CLIENT",
            legal_name="Demo Client S.R.L.",
            commercial_name="Demo Client",
            rnc_or_id=DEMO_CLIENT_RNC,
        )

        out = StringIO()
        call_command("diagnose_seed_duplicates", stdout=out)
        output = out.getvalue()

        self.assertIn("DUPLICATE", output)
        self.assertIn(DEMO_CLIENT_RNC, output)
        self.assertNotIn("Traceback", output)

    def test_diagnose_reports_clean_state_when_no_duplicates(self):
        Contact.objects.create(
            contact_type="CLIENT",
            legal_name="Only Client",
            rnc_or_id="111111111",
        )

        out = StringIO()
        call_command("diagnose_seed_duplicates", stdout=out)
        self.assertIn("No duplicate seed records detected", out.getvalue())


class CleanupSeedDemoDataTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="cleaner", password="x")
        self.issuer = Organization.objects.create(
            legal_name="BCC Technologies",
            rnc=DEMO_ISSUER_RNC,
        )

    def test_dry_run_changes_nothing(self):
        keeper = Contact.objects.create(
            contact_type="CLIENT",
            legal_name="Demo Client S.R.L.",
            commercial_name="Demo Client",
            email="demo.client@example.com",
            rnc_or_id=DEMO_CLIENT_RNC,
            is_active=True,
        )
        dup = Contact.objects.create(
            contact_type="CLIENT",
            legal_name="Demo Client S.R.L.",
            commercial_name="Demo Client",
            email="demo.client@example.com",
            rnc_or_id=DEMO_CLIENT_RNC,
            is_active=True,
        )

        out = StringIO()
        call_command("cleanup_seed_demo_data", stdout=out)
        output = out.getvalue()

        keeper.refresh_from_db()
        dup.refresh_from_db()
        self.assertTrue(keeper.is_active)
        self.assertTrue(dup.is_active)
        self.assertIn("DRY-RUN", output)
        self.assertIn("WOULD:", output)
        self.assertIn("Soft-deactivate", output)

    def test_apply_handles_duplicate_demo_contacts_safely(self):
        keeper = Contact.objects.create(
            contact_type="CLIENT",
            legal_name="Demo Client S.R.L.",
            commercial_name="Demo Client",
            email="demo.client@example.com",
            rnc_or_id=DEMO_CLIENT_RNC,
            is_active=True,
        )
        dup = Contact.objects.create(
            contact_type="CLIENT",
            legal_name="Demo Client S.R.L.",
            commercial_name="Demo Client",
            email="demo.client@example.com",
            rnc_or_id=DEMO_CLIENT_RNC,
            is_active=True,
        )

        call_command("cleanup_seed_demo_data", apply=True)

        keeper.refresh_from_db()
        dup.refresh_from_db()
        self.assertTrue(keeper.is_active)
        self.assertFalse(dup.is_active)
        self.assertEqual(
            Contact.objects.filter(contact_type="CLIENT", rnc_or_id=DEMO_CLIENT_RNC).count(),
            2,
        )

    def test_apply_is_idempotent(self):
        Contact.objects.create(
            contact_type="CLIENT",
            legal_name="Demo Client S.R.L.",
            commercial_name="Demo Client",
            email="demo.client@example.com",
            rnc_or_id=DEMO_CLIENT_RNC,
        )
        Contact.objects.create(
            contact_type="CLIENT",
            legal_name="Demo Client S.R.L.",
            commercial_name="Demo Client",
            email="demo.client@example.com",
            rnc_or_id=DEMO_CLIENT_RNC,
        )

        call_command("cleanup_seed_demo_data", apply=True)
        out = StringIO()
        call_command("cleanup_seed_demo_data", apply=True, stdout=out)
        output = out.getvalue()

        self.assertTrue(
            "No demo cleanup actions needed." in output
            or "No mutable demo cleanup actions" in output
        )
        self.assertEqual(
            Contact.objects.filter(
                contact_type="CLIENT",
                rnc_or_id=DEMO_CLIENT_RNC,
                is_active=True,
            ).count(),
            1,
        )

    def test_does_not_delete_non_demo_contacts(self):
        real = Contact.objects.create(
            contact_type="CLIENT",
            legal_name="Real Customer Corp",
            commercial_name="Real Customer",
            rnc_or_id="555555555",
            email="real@customer.com",
            is_active=True,
        )
        Contact.objects.create(
            contact_type="CLIENT",
            legal_name="Demo Client S.R.L.",
            commercial_name="Demo Client",
            email="demo.client@example.com",
            rnc_or_id=DEMO_CLIENT_RNC,
        )
        Contact.objects.create(
            contact_type="CLIENT",
            legal_name="Demo Client S.R.L.",
            commercial_name="Demo Client",
            email="demo.client@example.com",
            rnc_or_id=DEMO_CLIENT_RNC,
        )

        call_command("cleanup_seed_demo_data", apply=True)

        real.refresh_from_db()
        self.assertTrue(Contact.objects.filter(pk=real.pk).exists())
        self.assertTrue(real.is_active)
        self.assertEqual(real.legal_name, "Real Customer Corp")

    def test_skips_ambiguous_duplicates_of_demo_rnc(self):
        Contact.objects.create(
            contact_type="CLIENT",
            legal_name="Demo Client S.R.L.",
            commercial_name="Demo Client",
            email="demo.client@example.com",
            rnc_or_id=DEMO_CLIENT_RNC,
        )
        ambiguous = Contact.objects.create(
            contact_type="CLIENT",
            legal_name="Customer",
            commercial_name="Customer",
            rnc_or_id=DEMO_CLIENT_RNC,
            is_active=True,
        )

        out = StringIO()
        call_command("cleanup_seed_demo_data", apply=True, stdout=out)

        ambiguous.refresh_from_db()
        self.assertTrue(ambiguous.is_active)
        self.assertIn("SKIP Contact", out.getvalue())

    def test_seed_bcc_still_passes_after_cleanup(self):
        Contact.objects.create(
            contact_type="CLIENT",
            legal_name="Demo Client S.R.L.",
            commercial_name="Demo Client",
            email="demo.client@example.com",
            rnc_or_id=DEMO_CLIENT_RNC,
        )
        Contact.objects.create(
            contact_type="CLIENT",
            legal_name="Demo Client S.R.L.",
            commercial_name="Demo Client",
            email="demo.client@example.com",
            rnc_or_id=DEMO_CLIENT_RNC,
        )

        call_command("cleanup_seed_demo_data", apply=True)
        out = StringIO()
        call_command("seed_bcc", stdout=out)

        self.assertIn("Demo BCC data seeded.", out.getvalue())
        self.assertEqual(
            Invoice.objects.filter(notes__icontains=SEED_INVOICE_MARKER).count(),
            1,
        )

    def test_generate_internal_xml_still_works_after_cleanup(self):
        call_command("seed_bcc")
        Contact.objects.create(
            contact_type="CLIENT",
            legal_name="Demo Client S.R.L.",
            commercial_name="Demo Client",
            email="demo.client@example.com",
            rnc_or_id=DEMO_CLIENT_RNC,
        )
        call_command("cleanup_seed_demo_data", apply=True)

        seeded = Invoice.objects.filter(notes__icontains=SEED_INVOICE_MARKER).first()
        self.assertIsNotNone(seeded)
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

    def test_cleanup_retires_duplicate_seed_invoice_markers(self):
        customer = Contact.objects.create(
            contact_type="CLIENT",
            legal_name="Demo Client S.R.L.",
            rnc_or_id=DEMO_CLIENT_RNC,
        )
        inv1 = Invoice.objects.create(
            issuer=self.issuer,
            customer=customer,
            invoice_direction="OUTBOUND",
            lifecycle_status="DRAFT",
            currency="DOP",
            issue_date="2026-01-01",
            created_by=self.user,
            internal_code="BCC-AR-2026-000301",
            notes=SEED_INVOICE_MARKER,
        )
        inv2 = Invoice.objects.create(
            issuer=self.issuer,
            customer=customer,
            invoice_direction="OUTBOUND",
            lifecycle_status="DRAFT",
            currency="DOP",
            issue_date="2026-01-01",
            created_by=self.user,
            internal_code="BCC-AR-2026-000302",
            notes=SEED_INVOICE_MARKER,
        )
        InvoiceLine.objects.create(
            invoice=inv1,
            line_order=1,
            description="Line 1",
            quantity=Decimal("1.00"),
            unit_price=Decimal("10.00"),
        )
        InvoiceLine.objects.create(
            invoice=inv1,
            line_order=2,
            description="Line 2",
            quantity=Decimal("1.00"),
            unit_price=Decimal("20.00"),
        )
        InvoiceLine.objects.create(
            invoice=inv1,
            line_order=3,
            description="Extra",
            quantity=Decimal("1.00"),
            unit_price=Decimal("1.00"),
        )

        call_command("cleanup_seed_demo_data", apply=True)

        inv1.refresh_from_db()
        inv2.refresh_from_db()
        self.assertIn(SEED_INVOICE_MARKER, inv1.notes)
        self.assertNotIn(SEED_INVOICE_MARKER, inv2.notes)
        self.assertEqual(inv1.lines.count(), 2)


class ContactNaturalKeyHelperTests(TestCase):
    def test_resolve_contact_by_natural_key_is_deterministic(self):
        first = Contact.objects.create(
            contact_type="CLIENT",
            legal_name="A",
            rnc_or_id="999000111",
        )
        Contact.objects.create(
            contact_type="CLIENT",
            legal_name="B",
            rnc_or_id="999000111",
        )

        resolved, created, warnings = resolve_contact_by_natural_key(
            "CLIENT",
            "999000111",
            defaults={"legal_name": "Resolved"},
        )
        self.assertFalse(created)
        self.assertEqual(resolved.pk, first.pk)
        self.assertEqual(resolved.legal_name, "Resolved")
        self.assertEqual(len(warnings), 1)

    def test_model_natural_key_warnings(self):
        Contact.objects.create(
            contact_type="CLIENT",
            legal_name="A",
            rnc_or_id="999000222",
        )
        contact = Contact.objects.create(
            contact_type="CLIENT",
            legal_name="B",
            rnc_or_id="999000222",
        )
        warnings = contact.natural_key_warnings()
        self.assertEqual(len(warnings), 1)
        self.assertIn("Soft uniqueness only", warnings[0])
