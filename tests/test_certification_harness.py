import json
from pathlib import Path

from django.core.management import call_command
from django.test import TestCase
from django.test.utils import captured_stdout

from ecf.dgii.certification.case_runner import run_certification_harness
from ecf.dgii.certification.test_set_importer import import_case_rows, load_test_set
from ecf.models import ECFDocument


FIXTURE = Path("tests/fixtures/dgii/synthetic_certification_case.json")


class CertificationHarnessTests(TestCase):
    def test_synthetic_fixture_imports_and_maps_to_invoice(self):
        payload = load_test_set(FIXTURE)
        imported = import_case_rows(payload)
        self.assertEqual(len(imported), 1)
        invoice = imported[0].invoice
        self.assertEqual(invoice.internal_code, "BCC-HARNESS-SYN-000001")
        self.assertEqual(invoice.fiscal_document_type_ref.code, "31")
        self.assertEqual(invoice.official_encf, "E319000000101")
        self.assertEqual(invoice.lines.count(), 1)
        self.assertEqual(
            invoice.lines.first().description,
            "Synthetic certification harness service",
        )

    def test_unsigned_harness_reports_expected_limitation_without_submission(self):
        report = run_certification_harness(
            load_test_set(FIXTURE),
            mode="unsigned",
            no_submit=True,
        )
        self.assertEqual(report["harness_status"], "EXPECTED_UNSIGNED_LIMITATION")
        self.assertFalse(report["submitted"])
        self.assertFalse(report["dgii_call_made"])
        self.assertEqual(report["track_ids"], [])
        self.assertTrue(report["not_certification_evidence"])
        self.assertFalse(report["cases"][0]["local_validation_passed"])
        self.assertTrue(report["cases"][0]["expected_unsigned_limitation"])
        self.assertIsNone(ECFDocument.objects.get(invoice_id=report["cases"][0]["invoice_id"]).dgii_track_id)

    def test_sandbox_signed_harness_passes_local_validation_only(self):
        report = run_certification_harness(
            load_test_set(FIXTURE),
            mode="sandbox-signed",
            no_submit=True,
        )
        self.assertEqual(report["harness_status"], "PASS")
        self.assertTrue(report["cases"][0]["local_validation_passed"])
        self.assertTrue(report["cases"][0]["validation"]["signature_verified"])
        self.assertEqual(report["compliance_status"], "NOT_DGII_COMPLIANT")

    def test_management_command_json_report_has_no_submission(self):
        with captured_stdout() as out:
            call_command(
                "run_dgii_certification_harness",
                synthetic=True,
                no_submit=True,
                json_flag=True,
            )
        report = json.loads(out.getvalue())
        self.assertEqual(report["fixture_kind"], "synthetic")
        self.assertFalse(report["submitted"])
        self.assertFalse(report["dgii_call_made"])
        self.assertEqual(report["track_ids"], [])
        self.assertEqual(len(report["cases"]), 1)
