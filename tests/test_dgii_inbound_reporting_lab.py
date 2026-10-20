import json
from pathlib import Path
from unittest.mock import patch

from django.core.management import call_command
from django.test import RequestFactory, TestCase
from django.test.utils import captured_stdout

from documents.models import Document
from ecf.dgii.inbound_lab import analyze_inbound_xml, build_lab_report
from ecf.dgii.inbound_reporting_lab import (
    LAB_MODE,
    REPORT_SCOPE,
    build_csv_summary,
    build_inbound_lab_summary,
    build_json_report,
    build_markdown_summary,
    collect_lab_report_data,
    resolve_output_dir,
    write_report_bundle,
)
from ecf.dgii.receiver import get_receiver_contract_metadata
from ecf.models import (
    ECFDocument,
    InboundXMLLabAuditEvent,
    InboundXMLLabRecord,
    InboundXMLLabWorkflowEvent,
)
from ecf.views.dgii_public_endpoints import dgii_recepcion_ecf
from invoicing.models import Invoice

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures/dgii/inbound_lab"
REPO_ROOT = Path(__file__).resolve().parents[1]


class ReportingModuleImportTests(TestCase):
    def test_inbound_reporting_lab_module_imports(self):
        import ecf.dgii.inbound_reporting_lab as mod

        self.assertTrue(hasattr(mod, "collect_lab_report_data"))
        self.assertTrue(hasattr(mod, "build_inbound_lab_summary"))
        self.assertTrue(hasattr(mod, "build_json_report"))
        self.assertTrue(hasattr(mod, "build_csv_summary"))
        self.assertTrue(hasattr(mod, "build_markdown_summary"))
        self.assertTrue(hasattr(mod, "write_report_bundle"))
        self.assertEqual(mod.LAB_MODE, "NON_PRODUCTION_LAB_ONLY")
        self.assertEqual(mod.REPORT_SCOPE, "NON_PRODUCTION_LAB_ONLY")


class ReportingDataTests(TestCase):
    def test_collect_lab_report_data_json_serializable(self):
        data = collect_lab_report_data()
        json.dumps(data, default=str)
        self.assertIn("records", data)
        self.assertIn("workflow_events", data)
        self.assertIn("audit_events", data)
        self.assertIn("security_policy", data)
        self.assertIn("readiness", data)

    def test_summary_boundaries(self):
        summary = build_inbound_lab_summary()
        self.assertEqual(summary["compliance_status"], "NOT_DGII_COMPLIANT")
        self.assertFalse(summary["dgii_submission_allowed"])
        self.assertFalse(summary["certification_evidence"])
        self.assertFalse(summary["public_endpoints_enabled"])
        self.assertIsNone(summary["track_id"])
        self.assertFalse(summary["dgii_call_made"])
        self.assertEqual(summary["report_scope"], REPORT_SCOPE)
        self.assertEqual(summary["lab_mode"], LAB_MODE)
        self.assertFalse(summary["includes_raw_xml"])

    def test_json_report_required_sections(self):
        report = build_json_report()
        self.assertIn("record_count", report)
        self.assertIn("workflow_event_count", report)
        self.assertIn("audit_event_count", report)
        self.assertIn("security_control_summary", report)
        self.assertIn("readiness_summary", report)
        blob = json.dumps(report, default=str)
        self.assertNotIn("raw_xml_text", blob)

    def test_csv_summary_no_raw_xml(self):
        csv_text = build_csv_summary()
        self.assertIn("compliance_status", csv_text)
        self.assertNotIn("raw_xml_text", csv_text)

    def test_markdown_summary_not_compliant(self):
        md = build_markdown_summary()
        self.assertIn("NOT_DGII_COMPLIANT", md)
        self.assertNotIn("raw_xml_text", md)

    def test_write_report_bundle_and_no_raw_xml(self):
        report = write_report_bundle()
        output = Path(report["output_dir"])
        self.assertTrue((output / "inbound_lab_report.json").is_file())
        self.assertTrue((output / "inbound_lab_summary.csv").is_file())
        self.assertTrue((output / "inbound_lab_summary.md").is_file())
        self.assertTrue((output / "manifest.json").is_file())
        for name in (
            "inbound_lab_report.json",
            "inbound_lab_summary.csv",
            "inbound_lab_summary.md",
            "manifest.json",
        ):
            self.assertNotIn("raw_xml_text", (output / name).read_text(encoding="utf-8"))

    def test_output_path_traversal_rejected(self):
        with self.assertRaises(ValueError):
            resolve_output_dir("/tmp/evil_report_dir")
        with self.assertRaises(ValueError):
            resolve_output_dir("runtime/dgii_lab_reports/../../etc/passwd")


class ReportingCommandTests(TestCase):
    def test_command_runs_and_json_parseable(self):
        with captured_stdout() as out:
            call_command("dgii_inbound_reporting_lab")
        text = out.getvalue()
        self.assertIn("NOT_DGII_COMPLIANT", text)
        self.assertIn("NON_PRODUCTION_LAB_ONLY", text)
        self.assertIn("certification_evidence=false", text)
        self.assertIn("dgii_submission_allowed=false", text)
        self.assertIn("track_id=null", text)
        self.assertIn("dgii_call_made=false", text)

        with captured_stdout() as out:
            call_command("dgii_inbound_reporting_lab", json_flag=True)
        report = json.loads(out.getvalue())
        self.assertEqual(report["compliance_status"], "NOT_DGII_COMPLIANT")
        self.assertFalse(report["dgii_submission_allowed"])
        self.assertFalse(report["certification_evidence"])

    def test_summary_only_and_export_bundle(self):
        with captured_stdout() as out:
            call_command("dgii_inbound_reporting_lab", summary_only=True)
        text = out.getvalue()
        self.assertIn("record_count", text)
        self.assertNotIn("document_type_breakdown:", text)

        with captured_stdout() as out:
            call_command("dgii_inbound_reporting_lab", export_bundle=True, json_flag=True)
        report = json.loads(out.getvalue())
        self.assertTrue(report.get("files_exported"))
        self.assertTrue(Path(report["output_dir"]).is_dir())

    def test_command_writes_no_db_rows_or_fiscal_models(self):
        before = {
            "records": InboundXMLLabRecord.objects.count(),
            "workflow": InboundXMLLabWorkflowEvent.objects.count(),
            "audit": InboundXMLLabAuditEvent.objects.count(),
            "invoice": Invoice.objects.count(),
            "document": Document.objects.count(),
            "ecf": ECFDocument.objects.count(),
        }
        with captured_stdout():
            call_command("dgii_inbound_reporting_lab", json_flag=True)
            call_command("dgii_inbound_reporting_lab", export_bundle=True, json_flag=True)
        self.assertEqual(InboundXMLLabRecord.objects.count(), before["records"])
        self.assertEqual(InboundXMLLabWorkflowEvent.objects.count(), before["workflow"])
        self.assertEqual(InboundXMLLabAuditEvent.objects.count(), before["audit"])
        self.assertEqual(Invoice.objects.count(), before["invoice"])
        self.assertEqual(Document.objects.count(), before["document"])
        self.assertEqual(ECFDocument.objects.count(), before["ecf"])


class ReportingBoundaryTests(TestCase):
    @patch("ecf.dgii.inbound_reporting_lab.collect_lab_report_data")
    def test_command_does_not_create_track_id_or_call_dgii(self, mock_collect):
        mock_collect.return_value = {
            "records": [],
            "workflow_events": [],
            "audit_events": [],
            "security_policy": {},
            "endpoint_plan": {},
            "receiver_contract": {},
            "readiness": {"blockers": [], "overall_status": "BLOCKED"},
            "public_endpoints_enabled": False,
        }
        with captured_stdout() as out:
            call_command("dgii_inbound_reporting_lab", json_flag=True)
        report = json.loads(out.getvalue())
        self.assertIsNone(report["track_id"])
        self.assertFalse(report["dgii_call_made"])

    def test_public_disabled_routes_still_503(self):
        response = dgii_recepcion_ecf(RequestFactory().get("/fe/recepcion/api/ecf"))
        self.assertEqual(response.status_code, 503)

    @patch("ecf.dgii.receiver.classify_inbound_xml")
    def test_public_disabled_post_does_not_parse_or_write(self, mock_classify):
        before_records = InboundXMLLabRecord.objects.count()
        before_audit = InboundXMLLabAuditEvent.objects.count()
        request = RequestFactory().post(
            "/fe/recepcion/api/ecf",
            data=b'<?xml version="1.0"?><ECF/>',
            content_type="application/xml",
        )
        response = dgii_recepcion_ecf(request)
        self.assertEqual(response.status_code, 503)
        mock_classify.assert_not_called()
        self.assertEqual(InboundXMLLabRecord.objects.count(), before_records)
        self.assertEqual(InboundXMLLabAuditEvent.objects.count(), before_audit)


class ReportingReceiverContractTests(TestCase):
    def test_receiver_contract_reporting_fields(self):
        meta = get_receiver_contract_metadata()
        self.assertTrue(meta["inbound_reporting_lab_available"])
        self.assertFalse(meta["production_dashboard_ready"])
        self.assertFalse(meta["raw_xml_export_enabled"])
        self.assertTrue(meta["report_exports_metadata_only"])
        self.assertFalse(meta["public_endpoint_reporting_enabled"])
        self.assertFalse(meta["certification_evidence"])
        self.assertEqual(meta["reporting_command"], "dgii_inbound_reporting_lab")
        self.assertEqual(meta["reporting_scope"], "NON_PRODUCTION_LAB_ONLY")


class ReportingCrossLabDefaultTests(TestCase):
    def test_existing_labs_do_not_run_reporting_by_default(self):
        xml_bytes = (FIXTURE_DIR / "synthetic_ecf_unsigned.xml").read_bytes()
        self.assertEqual(
            build_lab_report([analyze_inbound_xml(xml_bytes)])["reporting_status"],
            "NOT_RUN_BY_DEFAULT",
        )
        with captured_stdout() as out:
            call_command("dgii_inbound_xml_lab", json_flag=True)
            call_command("dgii_inbound_schema_lab", json_flag=True)
            call_command("dgii_inbound_signature_lab", json_flag=True)
            call_command("dgii_inbound_persistence_lab", json_flag=True)
            call_command("dgii_inbound_workflow_lab", path=str(FIXTURE_DIR), json_flag=True)
            call_command(
                "dgii_inbound_audit_retention_lab", from_lab_records=True, json_flag=True
            )
            call_command("dgii_inbound_security_policy_lab", json_flag=True)
        # Ensure reporting command itself was not invoked by those labs
        self.assertNotIn("inbound_lab_report.json", out.getvalue())


class ReportingReadinessTests(TestCase):
    PHASE_035_BLOCKERS = (
        "inbound_reporting_lab_only",
        "reports_not_certification_evidence",
        "reports_metadata_only",
        "production_dashboard_not_implemented",
        "public_endpoint_reporting_disabled",
        "report_review_not_human_approved",
        "raw_xml_reporting_policy_not_approved",
    )

    def test_readiness_includes_phase_035_blockers(self):
        with captured_stdout() as out:
            call_command("dgii_readiness_report", json_flag=True)
        report = json.loads(out.getvalue())
        self.assertEqual(report["overall_status"], "BLOCKED")
        self.assertEqual(report["compliance_status"], "NOT_DGII_COMPLIANT")
        self.assertFalse(report["dgii_submission_allowed"])
        for blocker in self.PHASE_035_BLOCKERS:
            self.assertIn(blocker, report["blockers"])

    def test_doc_exists(self):
        self.assertTrue(
            (
                REPO_ROOT / "docs/dgii/lab/NON_PRODUCTION_INBOUND_REPORTING_EXPORT_LAB.md"
            ).is_file()
        )


class ReportingPrivateKeySafetyTests(TestCase):
    def test_no_private_key_files_added_by_phase(self):
        # Phase artifacts must not introduce private key material.
        forbidden = (".p12", ".pfx", ".key", "privkey", "private.pem", "key.pem")
        for path in (
            REPO_ROOT / "ecf/dgii/inbound_reporting_lab.py",
            REPO_ROOT / "ecf/management/commands/dgii_inbound_reporting_lab.py",
            REPO_ROOT / "docs/dgii/lab/NON_PRODUCTION_INBOUND_REPORTING_EXPORT_LAB.md",
        ):
            self.assertTrue(path.is_file())
            lower = path.name.lower()
            self.assertFalse(any(token in lower for token in forbidden))
