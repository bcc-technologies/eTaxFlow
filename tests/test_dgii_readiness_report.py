import json
from pathlib import Path

from django.core.management import call_command
from django.test import TestCase
from django.test.utils import captured_stdout


class DGIIRreadinessReportTests(TestCase):
    PHASE_024_BLOCKERS = (
        "official_source_inventory_reviewed",
        "usuario_administrador_ecf_not_confirmed",
        "representative_certificate_owner_not_confirmed",
        "production_signing_architecture_not_approved",
        "official_encf_authorization_ranges_not_confirmed",
        "public_urls_not_deployed",
        "acuse_aprobacion_services_not_live",
        "contingency_process_not_approved",
    )

    PHASE_025_BLOCKERS = (
        "public_base_url_not_configured",
        "public_dgii_endpoints_disabled",
        "endpoint_ssl_not_verified",
        "endpoint_internet_access_not_verified",
        "endpoint_routes_not_implemented_or_not_verified",
        "recepcion_url_blocked",
        "aprobacion_comercial_url_blocked",
        "autenticacion_url_blocked",
    )

    PHASE_026_BLOCKERS = (
        "staging_dns_not_verified",
        "staging_ssl_not_verified",
        "staging_external_reachability_not_verified",
        "staging_environment_not_deployed",
        "public_endpoint_routes_disabled",
        "disabled_stub_only",
        "production_signing_not_approved",
        "endpoint_security_owner_not_assigned",
    )

    PHASE_027_BLOCKERS = (
        "receiver_processing_not_implemented",
        "inbound_xml_signature_verification_not_implemented",
        "inbound_persistence_not_implemented",
        "inbound_duplicate_detection_not_implemented",
        "acuse_receiver_workflow_not_implemented",
        "aprobacion_comercial_receiver_workflow_not_implemented",
        "ecf_receiver_workflow_not_implemented",
        "receiver_security_controls_not_approved",
    )

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
        for blocker in self.PHASE_024_BLOCKERS:
            self.assertIn(blocker, report["blockers"])
        for blocker in self.PHASE_025_BLOCKERS:
            self.assertIn(blocker, report["blockers"])
        for blocker in self.PHASE_026_BLOCKERS:
            self.assertIn(blocker, report["blockers"])
        for blocker in self.PHASE_027_BLOCKERS:
            self.assertIn(blocker, report["blockers"])
        self.assertTrue(report["remaining_dgii_documentation_missing"])

    def test_human_report_runs_without_mutation(self):
        with captured_stdout() as out:
            call_command("dgii_readiness_report")
        output = out.getvalue()
        self.assertIn("DGII pre-certification readiness report", output)
        self.assertIn("overall_status: BLOCKED", output)
        self.assertIn("No DGII call", output)

    def test_phase_024_source_artifacts_exist(self):
        repo_root = Path(__file__).resolve().parents[1]
        self.assertTrue((repo_root / "docs/dgii/DGII_ECF_DOCUMENT_INVENTORY.md").is_file())
        self.assertTrue(
            (repo_root / "docs/dgii/source_intake/PHASE_024_SOURCE_REVIEW_SUMMARY.md").is_file()
        )
        self.assertTrue(
            (repo_root / "docs/dgii/governance/PHASE_024_DGII_AUTHORIZATION_GATE.md").is_file()
        )

    def test_no_live_transport_or_compliance_claim_in_report(self):
        with captured_stdout() as out:
            call_command("dgii_readiness_report", json_flag=True)
        report = json.loads(out.getvalue())
        self.assertFalse(report["dgii_submission_allowed"])
        self.assertFalse(report["dgii_call_made"])
        self.assertEqual(report["compliance_status"], "NOT_DGII_COMPLIANT")
        notes = " ".join(report.get("notes", []))
        self.assertIn("Phase 024", notes)
        self.assertIn("endpoint_plan", report)
