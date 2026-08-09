import json

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from django.test.utils import captured_stdout

from core.seed_demo import SEED_INVOICE_MARKER
from ecf.dgii.xsd.tipo31_signed_sandbox_validation import (
    validate_tipo31_signed_sandbox,
)
from ecf.services.signing_placeholder import prepare_signing_placeholder
from fiscal.services.encf_sequences import allocate_next_encf
from invoicing.models import Invoice


class SignedSandboxValidationTests(TestCase):
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

    def test_signed_sandbox_validates_locally_but_is_not_compliant(self):
        report = validate_tipo31_signed_sandbox(
            self.invoice,
            allow_demo_encf=True,
            test_only=True,
        )
        self.assertTrue(report.xsd_valid)
        self.assertTrue(report.signed_sandbox_valid)
        self.assertTrue(report.signature_present)
        self.assertTrue(report.signature_verified)
        self.assertEqual(report.remaining_errors, [])
        self.assertEqual(report.signature_errors, [])
        self.assertEqual(report.signature_status, "TEST_ONLY_SIGNATURE")
        self.assertEqual(report.compliance_status, "NOT_DGII_COMPLIANT")
        self.assertFalse(report.dgii_submission_allowed)
        self.assertFalse(report.dgii_call_made)
        self.assertIsNone(report.track_id)
        self.assertTrue(report.not_certification_evidence)

    def test_command_json_is_parseable_and_has_safety_markers(self):
        with captured_stdout() as out:
            call_command(
                "validate_tipo31_signed_sandbox",
                internal_code=self.invoice.internal_code,
                allow_demo_encf=True,
                test_only=True,
                json_flag=True,
            )
        payload = json.loads(out.getvalue())
        self.assertTrue(payload["xsd_valid"])
        self.assertTrue(payload["signature_verified"])
        self.assertEqual(payload["signature_status"], "TEST_ONLY_SIGNATURE")
        self.assertEqual(payload["compliance_status"], "NOT_DGII_COMPLIANT")
        self.assertFalse(payload["dgii_submission_allowed"])
        self.assertIsNone(payload["track_id"])

    def test_command_requires_explicit_test_only(self):
        with self.assertRaises(CommandError):
            call_command(
                "validate_tipo31_signed_sandbox",
                internal_code=self.invoice.internal_code,
                allow_demo_encf=True,
            )
