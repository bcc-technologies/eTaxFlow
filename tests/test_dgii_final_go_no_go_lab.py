import json
from pathlib import Path
from unittest.mock import patch

from django.core.management import call_command
from django.test import RequestFactory, TestCase
from django.test.utils import captured_stdout

from documents.models import Document
from ecf.dgii.endpoints import get_software_registration_metadata
from ecf.dgii.final_go_no_go_lab import (
    FINAL_DECISION_BLOCKED,
    FINAL_DECISION_LAB_ONLY_COMPLETE,
    FINAL_DECISION_READY_FOR_HUMAN_REVIEW,
    REVIEW_SCOPE,
    build_final_go_no_go_markdown,
    evaluate_final_go_no_go,
    get_final_decision_vocabulary,
    resolve_output_dir,
    write_final_go_no_go_review,
)
from ecf.dgii.inbound_lab import analyze_inbound_xml, build_lab_report
from ecf.dgii.receiver import get_receiver_contract_metadata
from ecf.models import ECFDocument, InboundXMLLabAuditEvent, InboundXMLLabRecord
from ecf.views.dgii_public_endpoints import dgii_recepcion_ecf
from invoicing.models import Invoice

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures/dgii/inbound_lab"
REPO_ROOT = Path(__file__).resolve().parents[1]


class FinalGoNoGoModuleTests(TestCase):
    def test_module_imports_and_vocabulary(self):
        import ecf.dgii.final_go_no_go_lab as mod

        self.assertTrue(hasattr(mod, "evaluate_final_go_no_go"))
        self.assertTrue(hasattr(mod, "get_final_decision_vocabulary"))
        vocab = get_final_decision_vocabulary()
        self.assertIn(FINAL_DECISION_BLOCKED, vocab["allowed"])
        self.assertIn(FINAL_DECISION_LAB_ONLY_COMPLETE, vocab["allowed"])
        self.assertIn(FINAL_DECISION_READY_FOR_HUMAN_REVIEW, vocab["allowed"])
        self.assertNotIn("READY_FOR_DGII_SUBMISSION", vocab["allowed"])
        self.assertIn("READY_FOR_DGII_SUBMISSION", vocab["forbidden"])

    def test_evaluate_boundaries(self):
        result = evaluate_final_go_no_go()
        self.assertEqual(result["final_decision"], FINAL_DECISION_BLOCKED)
        self.assertEqual(result["review_scope"], REVIEW_SCOPE)
        self.assertEqual(result["compliance_status"], "NOT_DGII_COMPLIANT")
        self.assertFalse(result["dgii_submission_allowed"])
        self.assertFalse(result["portal_submission_allowed"])
        self.assertFalse(result["certification_evidence"])
        self.assertFalse(result["public_endpoints_enabled"])
        self.assertFalse(result["production_staging_ready"])
        self.assertFalse(result["production_security_ready"])
        self.assertFalse(result["production_signature_ready"])
        self.assertFalse(result["production_signature_verification_ready"])
        self.assertIsNone(result["track_id"])
        self.assertFalse(result["dgii_call_made"])
        self.assertTrue(result["blockers"])
        self.assertTrue(result["human_decisions_required"])
        self.assertTrue(result["component_summaries"])
        md = build_final_go_no_go_markdown(result)
        self.assertIn("FINAL_DECISION_BLOCKED", md)
        self.assertIn("NOT_DGII_COMPLIANT", md)

    def test_write_review_and_path_traversal(self):
        report = write_final_go_no_go_review()
        output = Path(report["output_dir"])
        self.assertTrue((output / "final_go_no_go_review.json").is_file())
        self.assertTrue((output / "final_go_no_go_review.md").is_file())
        self.assertTrue((output / "manifest.json").is_file())
        with self.assertRaises(ValueError):
            resolve_output_dir("/tmp/evil_final_review")
        with self.assertRaises(ValueError):
            resolve_output_dir("runtime/dgii_final_reviews/../../etc/passwd")


class FinalGoNoGoCommandTests(TestCase):
    def test_command_runs_json_summary_export(self):
        with captured_stdout() as out:
            call_command("dgii_final_go_no_go_lab")
        text = out.getvalue()
        self.assertIn("NOT_DGII_COMPLIANT", text)
        self.assertIn("FINAL_REVIEW_LAB_ONLY", text)
        self.assertIn("FINAL_DECISION_BLOCKED", text)
        self.assertIn("production_signature_verification_ready=false", text)

        with captured_stdout() as out:
            call_command("dgii_final_go_no_go_lab", json_flag=True)
        report = json.loads(out.getvalue())
        self.assertEqual(report["final_decision"], FINAL_DECISION_BLOCKED)
        self.assertFalse(report["dgii_submission_allowed"])

        with captured_stdout() as out:
            call_command("dgii_final_go_no_go_lab", summary_only=True)
        text = out.getvalue()
        self.assertIn("blocker_count", text)
        self.assertNotIn("Human decisions required:", text)

        with captured_stdout() as out:
            call_command("dgii_final_go_no_go_lab", export_review=True, json_flag=True)
        report = json.loads(out.getvalue())
        self.assertTrue(report.get("files_exported"))
        self.assertTrue(Path(report["output_dir"]).is_dir())

    def test_command_no_db_writes(self):
        before = {
            "records": InboundXMLLabRecord.objects.count(),
            "audit": InboundXMLLabAuditEvent.objects.count(),
            "invoice": Invoice.objects.count(),
            "document": Document.objects.count(),
            "ecf": ECFDocument.objects.count(),
        }
        with captured_stdout() as out:
            call_command("dgii_final_go_no_go_lab", json_flag=True)
        report = json.loads(out.getvalue())
        self.assertIsNone(report["track_id"])
        self.assertFalse(report["dgii_call_made"])
        self.assertFalse(report["public_endpoints_enabled"])
        self.assertEqual(InboundXMLLabRecord.objects.count(), before["records"])
        self.assertEqual(InboundXMLLabAuditEvent.objects.count(), before["audit"])
        self.assertEqual(Invoice.objects.count(), before["invoice"])
        self.assertEqual(Document.objects.count(), before["document"])
        self.assertEqual(ECFDocument.objects.count(), before["ecf"])


class FinalGoNoGoBoundaryTests(TestCase):
    def test_public_disabled_routes_still_503(self):
        response = dgii_recepcion_ecf(RequestFactory().get("/fe/recepcion/api/ecf"))
        self.assertEqual(response.status_code, 503)

    @patch("ecf.dgii.receiver.classify_inbound_xml")
    def test_public_disabled_post_does_not_parse_or_write(self, mock_classify):
        before = InboundXMLLabRecord.objects.count()
        request = RequestFactory().post(
            "/fe/recepcion/api/ecf",
            data=b'<?xml version="1.0"?><ECF/>',
            content_type="application/xml",
        )
        response = dgii_recepcion_ecf(request)
        self.assertEqual(response.status_code, 503)
        mock_classify.assert_not_called()
        self.assertEqual(InboundXMLLabRecord.objects.count(), before)


class FinalGoNoGoContractTests(TestCase):
    def test_endpoint_and_receiver_contract(self):
        meta = get_software_registration_metadata()
        self.assertTrue(meta["final_go_no_go_lab_available"])
        self.assertEqual(meta["final_go_no_go_command"], "dgii_final_go_no_go_lab")
        self.assertEqual(meta["final_decision"], FINAL_DECISION_BLOCKED)
        self.assertFalse(meta["endpoint_activation_allowed"])
        self.assertFalse(meta["portal_submission_allowed"])
        self.assertFalse(meta["dgii_submission_allowed"])

        receiver = get_receiver_contract_metadata()
        self.assertTrue(receiver["final_go_no_go_lab_available"])
        self.assertEqual(receiver["final_decision"], FINAL_DECISION_BLOCKED)
        self.assertFalse(receiver["endpoint_activation_allowed"])
        self.assertFalse(receiver["portal_submission_allowed"])
        self.assertFalse(receiver["certification_evidence"])


class FinalGoNoGoCrossLabTests(TestCase):
    def test_existing_labs_do_not_run_final_by_default(self):
        xml_bytes = (FIXTURE_DIR / "synthetic_ecf_unsigned.xml").read_bytes()
        self.assertEqual(
            build_lab_report([analyze_inbound_xml(xml_bytes)])["final_go_no_go_status"],
            "NOT_RUN_BY_DEFAULT",
        )
        with captured_stdout() as out:
            call_command("dgii_inbound_xml_lab", json_flag=True)
            call_command("dgii_certification_package_lab", json_flag=True)
            call_command("dgii_staging_evidence_lab", json_flag=True)
        self.assertNotIn("final_go_no_go_review.json", out.getvalue())


class FinalGoNoGoReadinessTests(TestCase):
    PHASE_038_BLOCKERS = (
        "final_go_no_go_lab_only",
        "final_decision_blocked",
        "final_human_review_not_completed",
        "final_security_owner_approval_missing",
        "final_tax_compliance_approval_missing",
        "final_dgii_authorization_missing",
        "final_public_endpoint_activation_forbidden",
        "final_portal_submission_forbidden",
        "final_dgii_submission_forbidden",
        "final_production_signing_not_approved",
        "final_production_signature_verification_not_ready",
        "final_staging_evidence_not_approved",
        "final_certification_package_blocked",
    )

    def test_readiness_includes_phase_038_blockers(self):
        with captured_stdout() as out:
            call_command("dgii_readiness_report", json_flag=True)
        report = json.loads(out.getvalue())
        self.assertEqual(report["overall_status"], "BLOCKED")
        self.assertEqual(report["compliance_status"], "NOT_DGII_COMPLIANT")
        self.assertFalse(report["dgii_submission_allowed"])
        self.assertFalse(report["portal_submission_allowed"])
        self.assertEqual(report["final_decision"], FINAL_DECISION_BLOCKED)
        self.assertFalse(report["production_signature_verification_ready"])
        for blocker in self.PHASE_038_BLOCKERS:
            self.assertIn(blocker, report["blockers"])

    def test_doc_exists(self):
        self.assertTrue(
            (
                REPO_ROOT
                / "docs/dgii/certification/FINAL_NON_PRODUCTION_PRE_CERT_GO_NO_GO_REVIEW.md"
            ).is_file()
        )


class FinalGoNoGoPrivateKeySafetyTests(TestCase):
    def test_no_private_key_files_added_by_phase(self):
        forbidden = (".p12", ".pfx", ".key", "privkey", "private.pem", "key.pem")
        for path in (
            REPO_ROOT / "ecf/dgii/final_go_no_go_lab.py",
            REPO_ROOT / "ecf/management/commands/dgii_final_go_no_go_lab.py",
            REPO_ROOT
            / "docs/dgii/certification/FINAL_NON_PRODUCTION_PRE_CERT_GO_NO_GO_REVIEW.md",
        ):
            self.assertTrue(path.is_file())
            lower = path.name.lower()
            self.assertFalse(any(token in lower for token in forbidden))
