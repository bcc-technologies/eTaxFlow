import json
from pathlib import Path
from unittest.mock import patch

from django.core.management import call_command
from django.test import RequestFactory, TestCase
from django.test.utils import captured_stdout

from documents.models import Document
from ecf.dgii.endpoints import get_software_registration_metadata
from ecf.dgii.inbound_lab import analyze_inbound_xml, build_lab_report
from ecf.dgii.receiver import get_receiver_contract_metadata
from ecf.dgii.staging_evidence_lab import (
    EVIDENCE_MISSING,
    LAB_MODE,
    STAGING_EVIDENCE_BLOCKED,
    build_evidence_template,
    get_required_evidence_catalog,
    resolve_evidence_path,
    summarize_evidence,
    validate_evidence_payload,
    write_evidence_report,
    write_evidence_template,
)
from ecf.models import (
    ECFDocument,
    InboundXMLLabAuditEvent,
    InboundXMLLabRecord,
)
from ecf.views.dgii_public_endpoints import dgii_recepcion_ecf
from invoicing.models import Invoice

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures/dgii/inbound_lab"
REPO_ROOT = Path(__file__).resolve().parents[1]


class StagingEvidenceModuleTests(TestCase):
    def test_module_imports_and_catalog(self):
        import ecf.dgii.staging_evidence_lab as mod

        self.assertTrue(hasattr(mod, "get_required_evidence_catalog"))
        self.assertTrue(hasattr(mod, "build_evidence_template"))
        self.assertTrue(hasattr(mod, "validate_evidence_payload"))
        catalog = get_required_evidence_catalog()
        self.assertGreater(len(catalog), 10)
        self.assertEqual(
            [c["evidence_id"] for c in catalog],
            [c["evidence_id"] for c in get_required_evidence_catalog()],
        )
        for item in catalog:
            self.assertIn("evidence_id", item)
            self.assertIn("category", item)
            self.assertIn("title", item)
            self.assertTrue(item["blocker"])
            self.assertEqual(item["current_status"], EVIDENCE_MISSING)

    def test_template_and_validate_boundaries(self):
        template = build_evidence_template()
        self.assertEqual(len(template["evidence_items"]), len(get_required_evidence_catalog()))
        result = validate_evidence_payload(template)
        self.assertEqual(result["staging_evidence_decision"], STAGING_EVIDENCE_BLOCKED)
        self.assertEqual(result["compliance_status"], "NOT_DGII_COMPLIANT")
        self.assertFalse(result["dgii_submission_allowed"])
        self.assertFalse(result["certification_evidence"])
        self.assertFalse(result["public_endpoints_enabled"])
        self.assertFalse(result["production_staging_ready"])
        self.assertIsNone(result["track_id"])
        self.assertFalse(result["dgii_call_made"])
        self.assertFalse(result["network_checks_performed"])
        self.assertGreater(result["missing_count"], 0)
        self.assertGreater(result["manual_review_count"], 0)
        self.assertEqual(result["evidence_scope"], "NON_PRODUCTION_LAB_ONLY")
        self.assertEqual(result["lab_mode"], LAB_MODE)
        summary = summarize_evidence(result)
        self.assertEqual(summary["staging_evidence_decision"], STAGING_EVIDENCE_BLOCKED)
        self.assertFalse(summary["production_staging_ready"])

    def test_write_template_and_report_paths(self):
        template_path = write_evidence_template()
        self.assertTrue(template_path.is_file())
        self.assertIn("dgii_staging_evidence", str(template_path))
        result = validate_evidence_payload(
            json.loads(template_path.read_text(encoding="utf-8"))
        )
        report_path = write_evidence_report(None, result)
        self.assertTrue(report_path.is_file())
        self.assertIn("dgii_staging_evidence", str(report_path))

    def test_path_traversal_rejected(self):
        with self.assertRaises(ValueError):
            resolve_evidence_path("/tmp/evil.json", default_name="x.json")
        with self.assertRaises(ValueError):
            resolve_evidence_path(
                "runtime/dgii_staging_evidence/../../etc/passwd",
                default_name="x.json",
            )
        with self.assertRaises(ValueError):
            write_evidence_template("/tmp/evil_template.json")
        with self.assertRaises(ValueError):
            write_evidence_report(
                "/tmp/evil_report.json",
                validate_evidence_payload(build_evidence_template()),
            )


class StagingEvidenceCommandTests(TestCase):
    def test_command_runs_json_summary_template_export(self):
        with captured_stdout() as out:
            call_command("dgii_staging_evidence_lab")
        text = out.getvalue()
        self.assertIn("NOT_DGII_COMPLIANT", text)
        self.assertIn("NON_PRODUCTION_LAB_ONLY", text)
        self.assertIn("STAGING_EVIDENCE_BLOCKED", text)
        self.assertIn("certification_evidence=false", text)
        self.assertIn("production_staging_ready=false", text)
        self.assertIn("network_checks_performed=false", text)

        with captured_stdout() as out:
            call_command("dgii_staging_evidence_lab", json_flag=True)
        report = json.loads(out.getvalue())
        self.assertEqual(report["staging_evidence_decision"], STAGING_EVIDENCE_BLOCKED)
        self.assertFalse(report["dgii_submission_allowed"])

        with captured_stdout() as out:
            call_command("dgii_staging_evidence_lab", summary_only=True)
        text = out.getvalue()
        self.assertIn("missing_count", text)
        self.assertNotIn("Evidence items:", text)

        with captured_stdout() as out:
            call_command("dgii_staging_evidence_lab", write_template=True, json_flag=True)
        report = json.loads(out.getvalue())
        self.assertTrue(report.get("template_path"))
        self.assertTrue(Path(report["template_path"]).is_file())

        with captured_stdout() as out:
            call_command("dgii_staging_evidence_lab", export_report=True, json_flag=True)
        report = json.loads(out.getvalue())
        self.assertTrue(report.get("report_path"))
        self.assertTrue(Path(report["report_path"]).is_file())

    def test_command_evidence_file_and_no_db_writes(self):
        template_path = write_evidence_template()
        before = {
            "records": InboundXMLLabRecord.objects.count(),
            "audit": InboundXMLLabAuditEvent.objects.count(),
            "invoice": Invoice.objects.count(),
            "document": Document.objects.count(),
            "ecf": ECFDocument.objects.count(),
        }
        with captured_stdout() as out:
            call_command(
                "dgii_staging_evidence_lab",
                evidence_file=str(template_path),
                json_flag=True,
            )
        report = json.loads(out.getvalue())
        self.assertEqual(report["staging_evidence_decision"], STAGING_EVIDENCE_BLOCKED)
        self.assertIsNone(report["track_id"])
        self.assertFalse(report["dgii_call_made"])
        self.assertFalse(report["network_checks_performed"])
        self.assertEqual(InboundXMLLabRecord.objects.count(), before["records"])
        self.assertEqual(InboundXMLLabAuditEvent.objects.count(), before["audit"])
        self.assertEqual(Invoice.objects.count(), before["invoice"])
        self.assertEqual(Document.objects.count(), before["document"])
        self.assertEqual(ECFDocument.objects.count(), before["ecf"])


class StagingEvidenceBoundaryTests(TestCase):
    def test_public_disabled_routes_still_503(self):
        response = dgii_recepcion_ecf(RequestFactory().get("/fe/recepcion/api/ecf"))
        self.assertEqual(response.status_code, 503)

    @patch("ecf.dgii.receiver.classify_inbound_xml")
    def test_public_disabled_post_does_not_parse_or_write(self, mock_classify):
        before_records = InboundXMLLabRecord.objects.count()
        request = RequestFactory().post(
            "/fe/recepcion/api/ecf",
            data=b'<?xml version="1.0"?><ECF/>',
            content_type="application/xml",
        )
        response = dgii_recepcion_ecf(request)
        self.assertEqual(response.status_code, 503)
        mock_classify.assert_not_called()
        self.assertEqual(InboundXMLLabRecord.objects.count(), before_records)


class StagingEvidenceContractTests(TestCase):
    def test_endpoint_plan_and_receiver_contract(self):
        meta = get_software_registration_metadata()
        self.assertTrue(meta["staging_evidence_lab_available"])
        self.assertEqual(meta["staging_evidence_command"], "dgii_staging_evidence_lab")
        self.assertEqual(meta["staging_evidence_decision"], STAGING_EVIDENCE_BLOCKED)
        self.assertFalse(meta["production_staging_ready"])
        self.assertFalse(meta["external_dns_verified"])
        self.assertFalse(meta["external_tls_verified"])
        self.assertTrue(meta["staging_manual_evidence_required"])

        receiver = get_receiver_contract_metadata()
        self.assertTrue(receiver["staging_evidence_lab_available"])
        self.assertFalse(receiver["production_staging_ready"])
        self.assertFalse(receiver["public_endpoint_external_verification_ready"])
        self.assertFalse(receiver["dns_tls_evidence_ready"])
        self.assertTrue(receiver["manual_staging_review_required"])
        self.assertFalse(receiver["certification_evidence"])


class StagingEvidenceCrossLabTests(TestCase):
    def test_existing_labs_do_not_run_staging_evidence_by_default(self):
        xml_bytes = (FIXTURE_DIR / "synthetic_ecf_unsigned.xml").read_bytes()
        self.assertEqual(
            build_lab_report([analyze_inbound_xml(xml_bytes)])["staging_evidence_status"],
            "NOT_RUN_BY_DEFAULT",
        )
        with captured_stdout() as out:
            call_command("dgii_inbound_xml_lab", json_flag=True)
            call_command("dgii_inbound_reporting_lab", json_flag=True)
            call_command("dgii_inbound_security_policy_lab", json_flag=True)
        self.assertNotIn("staging_evidence_template.json", out.getvalue())


class StagingEvidenceReadinessTests(TestCase):
    PHASE_036_BLOCKERS = (
        "staging_evidence_lab_only",
        "dns_tls_evidence_not_uploaded",
        "external_disabled_endpoint_evidence_not_uploaded",
        "external_post_disabled_evidence_not_uploaded",
        "staging_environment_evidence_not_reviewed",
        "staging_db_separation_not_verified",
        "secrets_policy_not_reviewed",
        "public_base_url_not_verified",
        "logging_redaction_evidence_not_reviewed",
        "security_owner_staging_review_not_completed",
        "tax_compliance_staging_review_not_completed",
        "phase_024_authorization_gate_not_signed_off_for_staging",
    )

    def test_readiness_includes_phase_036_blockers(self):
        with captured_stdout() as out:
            call_command("dgii_readiness_report", json_flag=True)
        report = json.loads(out.getvalue())
        self.assertEqual(report["overall_status"], "BLOCKED")
        self.assertEqual(report["compliance_status"], "NOT_DGII_COMPLIANT")
        self.assertFalse(report["dgii_submission_allowed"])
        self.assertFalse(report["production_staging_ready"])
        for blocker in self.PHASE_036_BLOCKERS:
            self.assertIn(blocker, report["blockers"])

    def test_doc_exists(self):
        self.assertTrue(
            (
                REPO_ROOT
                / "docs/deployment/DGII_STAGING_DEPLOYMENT_EVIDENCE_COLLECTOR_LAB.md"
            ).is_file()
        )


class StagingEvidencePrivateKeySafetyTests(TestCase):
    def test_no_private_key_files_added_by_phase(self):
        forbidden = (".p12", ".pfx", ".key", "privkey", "private.pem", "key.pem")
        for path in (
            REPO_ROOT / "ecf/dgii/staging_evidence_lab.py",
            REPO_ROOT / "ecf/management/commands/dgii_staging_evidence_lab.py",
            REPO_ROOT
            / "docs/deployment/DGII_STAGING_DEPLOYMENT_EVIDENCE_COLLECTOR_LAB.md",
        ):
            self.assertTrue(path.is_file())
            lower = path.name.lower()
            self.assertFalse(any(token in lower for token in forbidden))
