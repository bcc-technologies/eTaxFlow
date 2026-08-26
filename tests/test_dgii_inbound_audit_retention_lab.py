import json
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch

from django.core.management import call_command
from django.test import RequestFactory, TestCase, override_settings
from django.test.utils import captured_stdout
from django.utils import timezone

from documents.models import Document
from ecf.dgii.inbound_audit_retention_lab import (
    LAB_MODE,
    LAB_AUDIT_MANUAL_REVIEW_REQUIRED,
    LAB_AUDIT_PURGE_CANDIDATE_IDENTIFIED,
    LAB_AUDIT_RAW_XML_STORED,
    LAB_AUDIT_RETENTION_REVIEWED,
    LAB_RETENTION_KEEP,
    LAB_RETENTION_PURGE_CANDIDATE,
    LAB_RETENTION_RAW_XML_REVIEW,
    LAB_RETENTION_REVIEW,
    audit_lab_record,
    build_export_manifest,
    decide_lab_retention,
    resolve_export_path,
    write_export_manifest,
)
from ecf.dgii.inbound_lab import analyze_inbound_xml, build_lab_report
from ecf.dgii.inbound_persistence_lab import persist_lab_record
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


class InboundXMLLabAuditEventModelTests(TestCase):
    def test_model_defaults(self):
        record = InboundXMLLabRecord.objects.create(
            raw_sha256="a" * 64,
            document_type="ECF",
        )
        event = InboundXMLLabAuditEvent.objects.create(
            lab_record=record,
            event_type=LAB_AUDIT_RETENTION_REVIEWED,
            retention_decision=LAB_RETENTION_KEEP,
            reason="test",
        )
        self.assertEqual(event.compliance_status, "NOT_DGII_COMPLIANT")
        self.assertFalse(event.dgii_submission_allowed)
        self.assertFalse(event.certification_evidence)
        self.assertIn(event.track_id, (None, ""))
        self.assertEqual(event.lab_mode, LAB_MODE)


class RetentionDecisionTests(TestCase):
    def test_safe_recent_keep(self):
        decision = decide_lab_retention(
            {
                "record_id": 1,
                "created_at": timezone.now().isoformat(),
                "persisted_raw_xml": False,
                "certification_evidence": False,
                "dgii_submission_allowed": False,
                "track_id": None,
                "dgii_call_made": False,
            },
            retention_days=30,
        )
        self.assertEqual(decision["retention_decision"], LAB_RETENTION_KEEP)
        self.assertEqual(decision["event_type"], LAB_AUDIT_RETENTION_REVIEWED)

    def test_raw_xml_review(self):
        decision = decide_lab_retention(
            {
                "created_at": timezone.now().isoformat(),
                "persisted_raw_xml": True,
                "certification_evidence": False,
                "dgii_submission_allowed": False,
                "track_id": None,
                "dgii_call_made": False,
            }
        )
        self.assertEqual(decision["retention_decision"], LAB_RETENTION_RAW_XML_REVIEW)
        self.assertEqual(decision["event_type"], LAB_AUDIT_RAW_XML_STORED)

    def test_old_purge_candidate(self):
        old = (timezone.now() - timedelta(days=40)).isoformat()
        decision = decide_lab_retention(
            {
                "created_at": old,
                "persisted_raw_xml": False,
                "certification_evidence": False,
                "dgii_submission_allowed": False,
                "track_id": None,
                "dgii_call_made": False,
            },
            retention_days=30,
        )
        self.assertEqual(decision["retention_decision"], LAB_RETENTION_PURGE_CANDIDATE)
        self.assertEqual(decision["event_type"], LAB_AUDIT_PURGE_CANDIDATE_IDENTIFIED)

    def test_certification_evidence_violation(self):
        decision = decide_lab_retention(
            {
                "created_at": timezone.now().isoformat(),
                "persisted_raw_xml": False,
                "certification_evidence": True,
                "dgii_submission_allowed": False,
                "track_id": None,
                "dgii_call_made": False,
            }
        )
        self.assertEqual(decision["retention_decision"], LAB_RETENTION_REVIEW)
        self.assertEqual(decision["event_type"], LAB_AUDIT_MANUAL_REVIEW_REQUIRED)

    def test_submission_allowed_violation(self):
        decision = decide_lab_retention(
            {
                "created_at": timezone.now().isoformat(),
                "persisted_raw_xml": False,
                "certification_evidence": False,
                "dgii_submission_allowed": True,
                "track_id": None,
                "dgii_call_made": False,
            }
        )
        self.assertEqual(decision["event_type"], LAB_AUDIT_MANUAL_REVIEW_REQUIRED)

    def test_track_id_violation(self):
        decision = decide_lab_retention(
            {
                "created_at": timezone.now().isoformat(),
                "persisted_raw_xml": False,
                "certification_evidence": False,
                "dgii_submission_allowed": False,
                "track_id": "TRACK-1",
                "dgii_call_made": False,
            }
        )
        self.assertEqual(decision["event_type"], LAB_AUDIT_MANUAL_REVIEW_REQUIRED)


class AuditLabRecordTests(TestCase):
    def test_dry_run_creates_no_audit_event(self):
        record = InboundXMLLabRecord.objects.create(
            raw_sha256="b" * 64,
            document_type="ECF",
        )
        result = audit_lab_record(record, apply=False)
        self.assertTrue(result["dry_run"])
        self.assertFalse(result["applied"])
        self.assertEqual(InboundXMLLabAuditEvent.objects.count(), 0)

    def test_apply_creates_audit_event(self):
        record = InboundXMLLabRecord.objects.create(
            raw_sha256="c" * 64,
            document_type="ECF",
        )
        result = audit_lab_record(record, apply=True)
        self.assertTrue(result["applied"])
        self.assertEqual(InboundXMLLabAuditEvent.objects.count(), 1)


class AuditRetentionCommandTests(TestCase):
    def setUp(self):
        persist_lab_record(
            (FIXTURE_DIR / "synthetic_ecf_unsigned.xml").read_bytes(),
            filename="synthetic_ecf_unsigned.xml",
        )

    def test_dry_run_writes_no_audit_events(self):
        before = InboundXMLLabAuditEvent.objects.count()
        with captured_stdout() as out:
            call_command("dgii_inbound_audit_retention_lab", from_lab_records=True)
        text = out.getvalue()
        self.assertIn("NOT_DGII_COMPLIANT", text)
        self.assertIn("NON_PRODUCTION_LAB_ONLY", text)
        self.assertEqual(InboundXMLLabAuditEvent.objects.count(), before)

    def test_apply_writes_audit_events_only(self):
        before_invoice = Invoice.objects.count()
        before_doc = Document.objects.count()
        before_ecf = ECFDocument.objects.count()
        with captured_stdout() as out:
            call_command(
                "dgii_inbound_audit_retention_lab",
                from_lab_records=True,
                apply_lab_audit=True,
                json_flag=True,
            )
        report = json.loads(out.getvalue())
        self.assertFalse(report["dry_run"])
        self.assertTrue(report["apply_lab_audit"])
        self.assertFalse(report["certification_evidence"])
        self.assertFalse(report["destructive_retention_actions_enabled"])
        self.assertGreater(report["applied_count"], 0)
        self.assertGreater(InboundXMLLabAuditEvent.objects.count(), 0)
        self.assertEqual(Invoice.objects.count(), before_invoice)
        self.assertEqual(Document.objects.count(), before_doc)
        self.assertEqual(ECFDocument.objects.count(), before_ecf)
        self.assertFalse(
            InboundXMLLabAuditEvent.objects.exclude(track_id__isnull=True)
            .exclude(track_id="")
            .exists()
        )

    def test_record_id_and_limit(self):
        record = InboundXMLLabRecord.objects.first()
        with captured_stdout() as out:
            call_command(
                "dgii_inbound_audit_retention_lab",
                record_id=record.pk,
                json_flag=True,
            )
        report = json.loads(out.getvalue())
        self.assertEqual(report["result_count"], 1)

        with captured_stdout() as out:
            call_command(
                "dgii_inbound_audit_retention_lab",
                from_lab_records=True,
                limit=1,
                json_flag=True,
            )
        report = json.loads(out.getvalue())
        self.assertEqual(report["result_count"], 1)

    def test_export_manifest_metadata_only(self):
        with captured_stdout() as out:
            call_command(
                "dgii_inbound_audit_retention_lab",
                from_lab_records=True,
                export_manifest=True,
                json_flag=True,
            )
        report = json.loads(out.getvalue())
        self.assertTrue(report["export_path"])
        path = Path(report["export_path"])
        self.assertTrue(path.is_file())
        manifest = json.loads(path.read_text(encoding="utf-8"))
        self.assertFalse(manifest["includes_raw_xml"])
        self.assertEqual(manifest["export_scope"], "METADATA_ONLY")
        blob = path.read_text(encoding="utf-8")
        self.assertNotIn("raw_xml_text", blob)

    def test_export_path_traversal_rejected(self):
        with self.assertRaises(Exception):
            call_command(
                "dgii_inbound_audit_retention_lab",
                from_lab_records=True,
                export_manifest=True,
                export_path="/tmp/evil.json",
            )


class ExportHelperTests(TestCase):
    def test_resolve_and_write_export(self):
        record = InboundXMLLabRecord.objects.create(
            raw_sha256="d" * 64,
            document_type="ECF",
            raw_xml_text="<ECF/>",
            persisted_raw_xml=True,
        )
        manifest = build_export_manifest([record])
        path = write_export_manifest(None, manifest)
        self.assertTrue(str(path).endswith(".json"))
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertNotIn("raw_xml_text", json.dumps(data))
        with self.assertRaises(ValueError):
            resolve_export_path("../outside.json")


class Phase033OtherLabsDoNotAuditTests(TestCase):
    def test_existing_labs_do_not_run_audit_by_default(self):
        before = InboundXMLLabAuditEvent.objects.count()
        xml_bytes = (FIXTURE_DIR / "synthetic_ecf_unsigned.xml").read_bytes()
        self.assertEqual(
            build_lab_report([analyze_inbound_xml(xml_bytes)])["audit_retention_status"],
            "NOT_RUN_BY_DEFAULT",
        )
        call_command("dgii_inbound_xml_lab", json_flag=True)
        call_command("dgii_inbound_schema_lab", json_flag=True)
        call_command("dgii_inbound_signature_lab", json_flag=True)
        call_command("dgii_inbound_persistence_lab", json_flag=True)
        call_command(
            "dgii_inbound_workflow_lab",
            path=str(FIXTURE_DIR),
            json_flag=True,
        )
        self.assertEqual(InboundXMLLabAuditEvent.objects.count(), before)


class Phase033ReceiverContractTests(TestCase):
    def test_receiver_contract_reports_audit_lab(self):
        meta = get_receiver_contract_metadata()
        self.assertTrue(meta["non_production_inbound_audit_retention_lab_available"])
        self.assertFalse(meta["production_audit_ready"])
        self.assertFalse(meta["production_retention_ready"])
        self.assertFalse(meta["public_route_audit_enabled"])
        self.assertFalse(meta["destructive_retention_actions_enabled"])
        self.assertEqual(meta["export_manifest_scope"], "METADATA_ONLY")
        self.assertEqual(meta["audit_retention_scope"], "NON_PRODUCTION_LAB_ONLY")


class Phase033ReadinessBlockerTests(TestCase):
    PHASE_033_BLOCKERS = (
        "inbound_audit_retention_lab_only",
        "production_audit_trail_not_implemented",
        "production_retention_policy_not_approved",
        "public_route_audit_disabled",
        "destructive_retention_actions_disabled",
        "metadata_export_not_certification_evidence",
        "raw_xml_retention_policy_not_approved",
        "audit_retention_policy_not_legal_reviewed",
    )

    def test_readiness_includes_phase_033_blockers(self):
        with captured_stdout() as out:
            call_command("dgii_readiness_report", json_flag=True)
        report = json.loads(out.getvalue())
        self.assertEqual(report["overall_status"], "BLOCKED")
        self.assertEqual(report["compliance_status"], "NOT_DGII_COMPLIANT")
        self.assertFalse(report["dgii_submission_allowed"])
        for blocker in self.PHASE_033_BLOCKERS:
            self.assertIn(blocker, report["blockers"])

    def test_doc_exists(self):
        repo_root = Path(__file__).resolve().parents[1]
        self.assertTrue(
            (
                repo_root
                / "docs/dgii/lab/NON_PRODUCTION_INBOUND_AUDIT_RETENTION_POLICY_LAB.md"
            ).is_file()
        )


class Phase033PublicRouteBoundaryTests(TestCase):
    def test_public_disabled_routes_return_503(self):
        response = dgii_recepcion_ecf(RequestFactory().get("/fe/recepcion/api/ecf"))
        self.assertEqual(response.status_code, 503)

    @patch("ecf.dgii.inbound_audit_retention_lab.audit_lab_record")
    @patch("ecf.dgii.receiver.classify_inbound_xml")
    def test_public_post_does_not_audit_or_parse(self, mock_classify, mock_audit):
        before = InboundXMLLabAuditEvent.objects.count()
        request = RequestFactory().post(
            "/fe/recepcion/api/ecf",
            data=b'<?xml version="1.0"?><ECF/>',
            content_type="application/xml",
        )
        response = dgii_recepcion_ecf(request)
        self.assertEqual(response.status_code, 503)
        mock_classify.assert_not_called()
        mock_audit.assert_not_called()
        self.assertEqual(InboundXMLLabAuditEvent.objects.count(), before)

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
