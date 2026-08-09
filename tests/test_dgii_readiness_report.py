import json

from django.core.management import call_command
from django.test import TestCase
from django.test.utils import captured_stdout


class DGIIRreadinessReportTests(TestCase):
    def test_json_report_is_parseable_and_reports_blockers(self):
        with captured_stdout() as out:
            call_command("dgii_readiness_report", json_flag=True)
        report = json.loads(out.getvalue())
        self.assertEqual(report["overall_status"], "BLOCKED")
        self.assertEqual(report["compliance_status"], "NOT_DGII_COMPLIANT")
        self.assertFalse(report["dgii_submission_allowed"])
        self.assertFalse(report["dgii_call_made"])
        self.assertIsNone(report["track_id"])
        self.assertTrue(report["not_certification_evidence"])
        self.assertIn("signing_readiness", report["blockers"])
        self.assertIn("url_recepcion", report["blockers"])
        self.assertTrue(report["remaining_dgii_documentation_missing"])

    def test_human_report_runs_without_mutation(self):
        with captured_stdout() as out:
            call_command("dgii_readiness_report")
        output = out.getvalue()
        self.assertIn("DGII pre-certification readiness report", output)
        self.assertIn("overall_status: BLOCKED", output)
        self.assertIn("No DGII call", output)
