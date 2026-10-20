import json
from pathlib import Path
from unittest.mock import patch

from django.core.management import call_command
from django.test import RequestFactory, TestCase, override_settings
from django.test.utils import captured_stdout

from documents.models import Document
from ecf.dgii.inbound_lab import analyze_inbound_xml, build_lab_report
from ecf.dgii.inbound_persistence_lab import persist_lab_record
from ecf.dgii.inbound_security_policy_lab import (
    CONTROL_NOT_IMPLEMENTED,
    CONTROL_PASS,
    LAB_MODE,
    SECURITY_POLICY_BLOCKED,
    build_security_policy_report,
    evaluate_security_policy,
    get_security_control_catalog,
    resolve_export_path,
    write_security_policy_report,
)
from ecf.dgii.receiver import get_receiver_contract_metadata
from ecf.models import ECFDocument, InboundXMLLabAuditEvent, InboundXMLLabRecord
from ecf.views.dgii_public_endpoints import dgii_recepcion_ecf
from invoicing.models import Invoice

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures/dgii/inbound_lab"


class SecurityPolicyModuleTests(TestCase):
    def test_module_catalog_deterministic_and_complete(self):
        catalog = get_security_control_catalog()
        self.assertGreater(len(catalog), 10)
        ids = [c["control_id"] for c in catalog]
        self.assertEqual(ids, [c["control_id"] for c in get_security_control_catalog()])
        self.assertEqual(len(ids), len(set(ids)))
        for item in catalog:
            self.assertIn("control_id", item)
            self.assertIn("family", item)
            self.assertIn("current_status", item)
            self.assertIn("blocker", item)
            self.assertIn("required_before_public_processing", item)

    def test_evaluate_security_policy_boundaries(self):
        result = evaluate_security_policy()
        self.assertEqual(result["policy_decision"], SECURITY_POLICY_BLOCKED)
        self.assertEqual(result["compliance_status"], "NOT_DGII_COMPLIANT")
        self.assertFalse(result["dgii_submission_allowed"])
        self.assertFalse(result["certification_evidence"])
        self.assertFalse(result["public_endpoints_enabled"])
        self.assertFalse(result["production_security_ready"])
        self.assertIsNone(result["track_id"])
        self.assertFalse(result["dgii_call_made"])
        self.assertEqual(result["lab_mode"], LAB_MODE)


class SecurityPolicyControlHonestyTests(TestCase):
    def _by_id(self, control_id):
        return next(c for c in get_security_control_catalog() if c["control_id"] == control_id)

    def test_body_size_not_reported_as_enforced(self):
        item = self._by_id("body_size_limit_not_implemented")
        self.assertEqual(item["current_status"], CONTROL_NOT_IMPLEMENTED)
        self.assertIn("not ENFORCED", item["evidence"])
        self.assertTrue(item["blocker"])

    def test_content_type_not_reported_as_enforced(self):
        item = self._by_id("content_type_allowlist_not_enforced")
        self.assertEqual(item["current_status"], CONTROL_NOT_IMPLEMENTED)
        self.assertIn("not ENFORCED", item["evidence"])

    def test_rate_limiting_not_enforced(self):
        item = self._by_id("rate_limiting_not_implemented")
        self.assertEqual(item["current_status"], CONTROL_NOT_IMPLEMENTED)

    def test_trust_chain_and_revocation_not_ready(self):
        self.assertEqual(
            self._by_id("certificate_trust_chain_not_implemented")["current_status"],
            CONTROL_NOT_IMPLEMENTED,
        )
        self.assertEqual(
            self._by_id("revocation_check_not_implemented")["current_status"],
            CONTROL_NOT_IMPLEMENTED,
        )

    def test_disabled_route_controls_pass(self):
        for control_id in (
            "disabled_routes_return_503",
            "disabled_routes_do_not_parse_xml",
            "disabled_routes_do_not_persist",
            "disabled_routes_do_not_create_trackid",
        ):
            self.assertEqual(self._by_id(control_id)["current_status"], CONTROL_PASS)


class SecurityPolicyCommandTests(TestCase):
    def test_command_runs_and_json_parseable(self):
        with captured_stdout() as out:
            call_command("dgii_inbound_security_policy_lab", json_flag=True)
        report = json.loads(out.getvalue())
        self.assertEqual(report["policy_decision"], SECURITY_POLICY_BLOCKED)
        self.assertEqual(report["compliance_status"], "NOT_DGII_COMPLIANT")
        self.assertFalse(report["production_security_ready"])

    def test_summary_only(self):
        with captured_stdout() as out:
            call_command("dgii_inbound_security_policy_lab", summary_only=True)
        text = out.getvalue()
        self.assertIn("SECURITY_POLICY_BLOCKED", text)
        self.assertIn("NOT_DGII_COMPLIANT", text)
        self.assertIn("control_count:", text)
        self.assertNotIn("family=endpoint_gate", text)

    def test_export_report_metadata_only(self):
        with captured_stdout() as out:
            call_command("dgii_inbound_security_policy_lab", export_report=True, json_flag=True)
        report = json.loads(out.getvalue())
        path = Path(report["export_path"])
        self.assertTrue(path.is_file())
        payload = json.loads(path.read_text(encoding="utf-8"))
        self.assertNotIn("raw_xml_text", json.dumps(payload))
        self.assertEqual(payload["policy_decision"], SECURITY_POLICY_BLOCKED)

    def test_export_path_traversal_rejected(self):
        with self.assertRaises(Exception):
            call_command(
                "dgii_inbound_security_policy_lab",
                export_path="/tmp/evil_security.json",
                export_report=True,
            )

    def test_command_writes_no_db_and_no_production_models(self):
        before_audit = InboundXMLLabAuditEvent.objects.count()
        before_invoice = Invoice.objects.count()
        before_doc = Document.objects.count()
        before_ecf = ECFDocument.objects.count()
        call_command("dgii_inbound_security_policy_lab", json_flag=True)
        self.assertEqual(InboundXMLLabAuditEvent.objects.count(), before_audit)
        self.assertEqual(Invoice.objects.count(), before_invoice)
        self.assertEqual(Document.objects.count(), before_doc)
        self.assertEqual(ECFDocument.objects.count(), before_ecf)


class ExportHelperTests(TestCase):
    def test_resolve_rejects_outside_root(self):
        with self.assertRaises(ValueError):
            resolve_export_path("../outside.json")

    def test_write_report(self):
        report = build_security_policy_report()
        path = write_security_policy_report(None, report)
        self.assertTrue(path.is_file())
        self.assertTrue(str(path).startswith("runtime/dgii_security_reports/") or "dgii_security_reports" in str(path))


class Phase034OtherLabsDoNotRunSecurityPolicyTests(TestCase):
    def test_existing_labs_do_not_run_security_policy_by_default(self):
        xml_bytes = (FIXTURE_DIR / "synthetic_ecf_unsigned.xml").read_bytes()
        self.assertEqual(
            build_lab_report([analyze_inbound_xml(xml_bytes)])["security_policy_status"],
            "NOT_RUN_BY_DEFAULT",
        )
        with captured_stdout():
            call_command("dgii_inbound_xml_lab", json_flag=True)
            call_command("dgii_inbound_schema_lab", json_flag=True)
            call_command("dgii_inbound_signature_lab", json_flag=True)
            call_command("dgii_inbound_persistence_lab", json_flag=True)
            call_command("dgii_inbound_workflow_lab", path=str(FIXTURE_DIR), json_flag=True)
            call_command("dgii_inbound_audit_retention_lab", from_lab_records=True, json_flag=True)


class Phase034ReceiverContractTests(TestCase):
    def test_receiver_contract_reports_security_policy_lab(self):
        meta = get_receiver_contract_metadata()
        self.assertTrue(meta["inbound_security_policy_lab_available"])
        self.assertFalse(meta["production_security_ready"])
        self.assertFalse(meta["public_endpoint_security_controls_enforced"])
        self.assertFalse(meta["body_size_limit_enforced"])
        self.assertFalse(meta["content_type_allowlist_enforced"])
        self.assertFalse(meta["rate_limiting_enforced"])
        self.assertEqual(meta["security_policy_decision"], SECURITY_POLICY_BLOCKED)
        self.assertEqual(meta["security_policy_scope"], "NON_PRODUCTION_LAB_ONLY")


class Phase034ReadinessBlockerTests(TestCase):
    PHASE_034_BLOCKERS = (
        "inbound_security_policy_lab_only",
        "public_endpoint_security_controls_not_enforced",
        "body_size_limit_not_enforced",
        "content_type_allowlist_not_enforced",
        "rate_limiting_not_implemented",
        "logging_redaction_policy_not_approved",
        "certificate_trust_chain_not_implemented",
        "revocation_check_not_implemented",
        "security_owner_review_not_completed",
        "incident_response_policy_not_approved",
        "environment_separation_not_verified",
        "dns_tls_not_verified_for_public_receiver",
        "phase_024_human_gate_not_signed_off",
    )

    def test_readiness_includes_phase_034_blockers(self):
        with captured_stdout() as out:
            call_command("dgii_readiness_report", json_flag=True)
        report = json.loads(out.getvalue())
        self.assertEqual(report["overall_status"], "BLOCKED")
        self.assertEqual(report["compliance_status"], "NOT_DGII_COMPLIANT")
        self.assertFalse(report["dgii_submission_allowed"])
        self.assertFalse(report["production_security_ready"])
        for blocker in self.PHASE_034_BLOCKERS:
            self.assertIn(blocker, report["blockers"])

    def test_doc_exists(self):
        repo_root = Path(__file__).resolve().parents[1]
        self.assertTrue(
            (
                repo_root
                / "docs/dgii/security/INBOUND_SECURITY_CONTROLS_POLICY_REVIEW_LAB.md"
            ).is_file()
        )


class Phase034PublicRouteBoundaryTests(TestCase):
    def test_public_disabled_routes_return_503(self):
        response = dgii_recepcion_ecf(RequestFactory().get("/fe/recepcion/api/ecf"))
        self.assertEqual(response.status_code, 503)

    @patch("ecf.dgii.inbound_security_policy_lab.evaluate_security_policy")
    @patch("ecf.dgii.receiver.classify_inbound_xml")
    def test_public_post_does_not_parse_or_write(self, mock_classify, mock_eval):
        before_audit = InboundXMLLabAuditEvent.objects.count()
        before_records = InboundXMLLabRecord.objects.count()
        request = RequestFactory().post(
            "/fe/recepcion/api/ecf",
            data=b'<?xml version="1.0"?><ECF/>',
            content_type="application/xml",
        )
        response = dgii_recepcion_ecf(request)
        self.assertEqual(response.status_code, 503)
        mock_classify.assert_not_called()
        mock_eval.assert_not_called()
        self.assertEqual(InboundXMLLabAuditEvent.objects.count(), before_audit)
        self.assertEqual(InboundXMLLabRecord.objects.count(), before_records)

    def test_no_private_key_files_added(self):
        repo_root = Path(__file__).resolve().parents[1]
        skip_parts = {".venv", ".git", ".conda", "node_modules", "__pycache__"}
        offenders = []
        for path in repo_root.rglob("*"):
            if any(part in skip_parts for part in path.parts):
                continue
            if not path.is_file():
                continue
            name = path.name.lower()
            if name.endswith((".p12", ".pfx", ".key")) or name in {
                "key.pem",
                "privkey.pem",
                "private.pem",
            }:
                offenders.append(str(path.relative_to(repo_root)))
        self.assertEqual(offenders, [])


@override_settings(ETAXFLOW_ENABLE_PUBLIC_DGII_ENDPOINTS=False)
class SecurityPolicyDisabledDefaultTests(TestCase):
    def test_endpoints_remain_disabled_in_policy(self):
        result = evaluate_security_policy()
        self.assertFalse(result["public_endpoints_enabled"])
