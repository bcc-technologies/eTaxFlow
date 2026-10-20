import json
from pathlib import Path
from unittest.mock import patch

from django.core.management import call_command
from django.test import RequestFactory, TestCase
from django.test.utils import captured_stdout

from documents.models import Document
from ecf.dgii.endpoints import get_software_registration_metadata
from ecf.dgii.final_inbound_audit_lab import (
    FINAL_DECISION_BLOCKED,
    PHASE_039_BLOCKERS,
    REPORT_SCOPE,
    build_final_inbound_audit_markdown,
    build_final_inbound_audit_report,
    get_command_inventory,
    get_model_inventory,
    get_phase_inventory,
    resolve_output_dir,
    write_final_inbound_audit_report,
)
from ecf.dgii.inbound_lab import analyze_inbound_xml, build_lab_report
from ecf.dgii.receiver import get_receiver_contract_metadata
from ecf.models import ECFDocument, InboundXMLLabAuditEvent, InboundXMLLabRecord
from ecf.views.dgii_public_endpoints import dgii_recepcion_ecf
from invoicing.models import Invoice

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures/dgii/inbound_lab"
REPO_ROOT = Path(__file__).resolve().parents[1]


class FinalInboundAuditModuleTests(TestCase):
    def test_module_imports(self):
        import ecf.dgii.final_inbound_audit_lab as mod

        self.assertTrue(hasattr(mod, "build_final_inbound_audit_report"))
        self.assertTrue(hasattr(mod, "get_phase_inventory"))

    def test_phase_inventory(self):
        inventory = get_phase_inventory()
        phases = [item["phase"] for item in inventory]
        self.assertIn("024", phases)
        self.assertIn("039", phases)
        self.assertEqual(get_phase_inventory(), inventory)

    def test_command_inventory(self):
        commands = [item["command"] for item in get_command_inventory()]
        self.assertIn("dgii_final_inbound_audit_lab", commands)
        self.assertIn("dgii_final_go_no_go_lab", commands)

    def test_model_inventory(self):
        models = [item["model"] for item in get_model_inventory()]
        self.assertIn("InboundXMLLabRecord", models)
        self.assertIn("InboundXMLLabWorkflowEvent", models)
        self.assertIn("InboundXMLLabAuditEvent", models)

    def test_report_boundaries(self):
        report = build_final_inbound_audit_report()
        self.assertEqual(report["report_scope"], REPORT_SCOPE)
        self.assertEqual(report["compliance_status"], "NOT_DGII_COMPLIANT")
        self.assertFalse(report["dgii_submission_allowed"])
        self.assertFalse(report["portal_submission_allowed"])
        self.assertFalse(report["certification_evidence"])
        self.assertFalse(report["public_endpoints_enabled"])
        self.assertFalse(report["endpoint_activation_allowed"])
        self.assertFalse(report["production_staging_ready"])
        self.assertFalse(report["production_security_ready"])
        self.assertFalse(report["production_signature_ready"])
        self.assertFalse(report["production_signature_verification_ready"])
        self.assertEqual(report["final_decision"], FINAL_DECISION_BLOCKED)
        self.assertIsNone(report["track_id"])
        self.assertFalse(report["dgii_call_made"])
        self.assertTrue(report["blockers"])
        self.assertTrue(report["human_decisions_required"])
        self.assertTrue(report["next_operational_steps"])
        self.assertTrue(report["component_summaries"])

    def test_markdown_boundaries(self):
        md = build_final_inbound_audit_markdown()
        self.assertIn("NOT_DGII_COMPLIANT", md)
        self.assertIn("FINAL_DECISION_BLOCKED", md)
        self.assertIn("dgii_submission_allowed=false", md)

    def test_write_report_and_path_traversal(self):
        report = write_final_inbound_audit_report()
        output = Path(report["output_dir"])
        self.assertTrue((output / "final_inbound_lab_audit_report.json").is_file())
        self.assertTrue((output / "final_inbound_lab_audit_report.md").is_file())
        self.assertTrue((output / "manifest.json").is_file())
        blob = (output / "final_inbound_lab_audit_report.json").read_text()
        self.assertNotIn("raw_xml_text", blob)
        with self.assertRaises(ValueError):
            resolve_output_dir("/tmp/evil_final_audit")
        with self.assertRaises(ValueError):
            resolve_output_dir("runtime/dgii_final_audit_reports/../../etc/passwd")


class FinalInboundAuditCommandTests(TestCase):
    def test_command_runs_json_summary_export(self):
        with captured_stdout() as out:
            call_command("dgii_final_inbound_audit_lab")
        text = out.getvalue()
        self.assertIn("NOT_DGII_COMPLIANT", text)
        self.assertIn("FINAL_AUDIT_LAB_ONLY", text)
        self.assertIn("FINAL_DECISION_BLOCKED", text)
        self.assertIn("production_signature_verification_ready=false", text)

        with captured_stdout() as out:
            call_command("dgii_final_inbound_audit_lab", json_flag=True)
        report = json.loads(out.getvalue())
        self.assertEqual(report["final_decision"], FINAL_DECISION_BLOCKED)
        self.assertFalse(report["dgii_submission_allowed"])

        with captured_stdout() as out:
            call_command("dgii_final_inbound_audit_lab", summary_only=True)
        text = out.getvalue()
        self.assertIn("blocker_count", text)

        with captured_stdout() as out:
            call_command(
                "dgii_final_inbound_audit_lab",
                export_markdown=True,
                export_json=True,
                json_flag=True,
            )
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
            call_command("dgii_final_inbound_audit_lab", json_flag=True)
        report = json.loads(out.getvalue())
        self.assertIsNone(report["track_id"])
        self.assertFalse(report["dgii_call_made"])
        self.assertFalse(report["public_endpoints_enabled"])
        self.assertEqual(InboundXMLLabRecord.objects.count(), before["records"])
        self.assertEqual(InboundXMLLabAuditEvent.objects.count(), before["audit"])
        self.assertEqual(Invoice.objects.count(), before["invoice"])
        self.assertEqual(Document.objects.count(), before["document"])
        self.assertEqual(ECFDocument.objects.count(), before["ecf"])


class FinalInboundAuditBoundaryTests(TestCase):
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


class FinalInboundAuditContractTests(TestCase):
    def test_endpoint_and_receiver_contract(self):
        meta = get_software_registration_metadata()
        self.assertTrue(meta["final_inbound_audit_lab_available"])
        self.assertEqual(meta["final_inbound_audit_command"], "dgii_final_inbound_audit_lab")
        self.assertEqual(meta["final_audit_scope"], REPORT_SCOPE)
        self.assertEqual(meta["final_decision"], FINAL_DECISION_BLOCKED)
        self.assertFalse(meta["endpoint_activation_allowed"])
        self.assertFalse(meta["portal_submission_allowed"])
        self.assertFalse(meta["dgii_submission_allowed"])
        self.assertFalse(meta["certification_evidence"])

        receiver = get_receiver_contract_metadata()
        self.assertTrue(receiver["final_inbound_audit_lab_available"])
        self.assertEqual(receiver["final_decision"], FINAL_DECISION_BLOCKED)
        self.assertFalse(receiver["endpoint_activation_allowed"])
        self.assertFalse(receiver["portal_submission_allowed"])
        self.assertFalse(receiver["certification_evidence"])


class FinalInboundAuditCrossLabTests(TestCase):
    def test_existing_labs_do_not_run_final_audit_by_default(self):
        xml_bytes = (FIXTURE_DIR / "synthetic_ecf_unsigned.xml").read_bytes()
        self.assertEqual(
            build_lab_report([analyze_inbound_xml(xml_bytes)])["final_inbound_audit_status"],
            "NOT_RUN_BY_DEFAULT",
        )
        with captured_stdout() as out:
            call_command("dgii_inbound_xml_lab", json_flag=True)
            call_command("dgii_final_go_no_go_lab", json_flag=True)
            call_command("dgii_certification_package_lab", json_flag=True)
        self.assertNotIn("final_inbound_lab_audit_report.json", out.getvalue())


class FinalInboundAuditReadinessTests(TestCase):
    def test_readiness_includes_phase_039_blockers(self):
        with captured_stdout() as out:
            call_command("dgii_readiness_report", json_flag=True)
        report = json.loads(out.getvalue())
        self.assertEqual(report["overall_status"], "BLOCKED")
        self.assertEqual(report["compliance_status"], "NOT_DGII_COMPLIANT")
        self.assertFalse(report["dgii_submission_allowed"])
        self.assertFalse(report["portal_submission_allowed"])
        self.assertFalse(report["endpoint_activation_allowed"])
        self.assertEqual(report["final_decision"], FINAL_DECISION_BLOCKED)
        for blocker in PHASE_039_BLOCKERS:
            self.assertIn(blocker, report["blockers"])

    def test_doc_exists(self):
        self.assertTrue(
            (REPO_ROOT / "docs/dgii/audit/FINAL_INBOUND_LAB_AUDIT_REPORT.md").is_file()
        )


class FinalInboundAuditPrivateKeySafetyTests(TestCase):
    def test_no_private_key_files_added_by_phase(self):
        forbidden = (".p12", ".pfx", ".key", "privkey", "private.pem", "key.pem")
        for path in (
            REPO_ROOT / "ecf/dgii/final_inbound_audit_lab.py",
            REPO_ROOT / "ecf/management/commands/dgii_final_inbound_audit_lab.py",
            REPO_ROOT / "docs/dgii/audit/FINAL_INBOUND_LAB_AUDIT_REPORT.md",
        ):
            self.assertTrue(path.is_file())
            lower = path.name.lower()
            self.assertFalse(any(token in lower for token in forbidden))
