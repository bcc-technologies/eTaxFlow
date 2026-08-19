import json
from pathlib import Path
from unittest.mock import patch

from django.core.management import call_command
from django.test import RequestFactory, TestCase
from django.test.utils import captured_stdout

from documents.models import Document
from ecf.dgii.inbound_lab import analyze_inbound_xml, build_lab_report
from ecf.dgii.inbound_persistence_lab import (
    LAB_MODE,
    build_lab_record_payload,
    persist_lab_record,
    persist_path,
)
from ecf.dgii.inbound_schema_lab import analyze_inbound_xml_with_local_xsd, build_schema_lab_report
from ecf.dgii.inbound_signature_lab import (
    analyze_inbound_xml_with_signature_lab,
    build_signature_lab_report,
)
from ecf.dgii.receiver import get_receiver_contract_metadata
from ecf.models import ECFDocument, InboundXMLLabRecord
from ecf.views.dgii_public_endpoints import dgii_recepcion_ecf
from invoicing.models import Invoice

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures/dgii/inbound_lab"


class InboundXMLLabRecordModelTests(TestCase):
    def test_model_defaults(self):
        row = InboundXMLLabRecord.objects.create(
            raw_sha256="a" * 64,
            document_type="ECF",
        )
        self.assertEqual(row.compliance_status, "NOT_DGII_COMPLIANT")
        self.assertFalse(row.dgii_submission_allowed)
        self.assertFalse(row.certification_evidence)
        self.assertIn(row.track_id, (None, ""))
        self.assertEqual(row.lab_mode, LAB_MODE)
        self.assertFalse(row.persisted_raw_xml)
        self.assertEqual(row.raw_xml_text, "")


class PersistencePayloadTests(TestCase):
    def test_payload_includes_hash_schema_signature_and_boundaries(self):
        xml_bytes = (FIXTURE_DIR / "synthetic_ecf_unsigned.xml").read_bytes()
        payload = build_lab_record_payload(xml_bytes, filename="synthetic_ecf_unsigned.xml")
        self.assertEqual(len(payload["raw_sha256"]), 64)
        self.assertIn("xsd_available", payload)
        self.assertIn("local_xsd_valid", payload)
        self.assertIn("signature_verification_status", payload)
        self.assertFalse(payload["certification_evidence"])
        self.assertFalse(payload["dgii_submission_allowed"])
        self.assertIsNone(payload["track_id"])
        self.assertEqual(payload["lab_mode"], LAB_MODE)

    def test_payload_keeps_xsd_unmapped_as_whole_token(self):
        xml_bytes = (FIXTURE_DIR / "synthetic_unknown_root.xml").read_bytes()
        payload = build_lab_record_payload(xml_bytes, filename="synthetic_unknown_root.xml")
        self.assertIn("xsd_unmapped", payload["errors_json"])
        self.assertNotIn("x", payload["errors_json"])


class PersistLabRecordTests(TestCase):
    def test_persist_creates_without_raw_xml_by_default(self):
        xml_bytes = (FIXTURE_DIR / "synthetic_ecf_unsigned.xml").read_bytes()
        result = persist_lab_record(xml_bytes, filename="synthetic_ecf_unsigned.xml")
        self.assertTrue(result["created"])
        row = InboundXMLLabRecord.objects.get(pk=result["record_id"])
        self.assertFalse(row.persisted_raw_xml)
        self.assertEqual(row.raw_xml_text, "")
        self.assertFalse(result["certification_evidence"])
        self.assertIsNone(result["track_id"])

    def test_store_raw_xml_flag(self):
        xml_bytes = (FIXTURE_DIR / "synthetic_arecf_unsigned.xml").read_bytes()
        result = persist_lab_record(
            xml_bytes,
            filename="synthetic_arecf_unsigned.xml",
            store_raw_xml=True,
        )
        row = InboundXMLLabRecord.objects.get(pk=result["record_id"])
        self.assertTrue(row.persisted_raw_xml)
        self.assertTrue(row.raw_xml_text)
        self.assertIn("ARECF", row.raw_xml_text)

    def test_idempotent_by_sha256(self):
        xml_bytes = (FIXTURE_DIR / "synthetic_acecf_unsigned.xml").read_bytes()
        first = persist_lab_record(xml_bytes, filename="synthetic_acecf_unsigned.xml")
        second = persist_lab_record(xml_bytes, filename="synthetic_acecf_unsigned.xml")
        self.assertTrue(first["created"])
        self.assertTrue(second["updated"])
        self.assertEqual(first["record_id"], second["record_id"])
        self.assertEqual(InboundXMLLabRecord.objects.count(), 1)

    def test_persist_path_directory_deterministic(self):
        results = persist_path(FIXTURE_DIR)
        names = [item["filename"] for item in results]
        self.assertEqual(names, sorted(names))
        self.assertEqual(InboundXMLLabRecord.objects.count(), len(results))


class PersistenceLabCommandTests(TestCase):
    def test_dry_run_writes_no_db_rows(self):
        before = InboundXMLLabRecord.objects.count()
        with captured_stdout() as out:
            call_command("dgii_inbound_persistence_lab")
        text = out.getvalue()
        self.assertIn("NOT_DGII_COMPLIANT", text)
        self.assertIn("NON_PRODUCTION_LAB_ONLY", text)
        self.assertIn("certification_evidence=false", text)
        self.assertIn("track_id=null", text)
        self.assertEqual(InboundXMLLabRecord.objects.count(), before)

    def test_persist_command_writes_lab_rows_and_json_is_parseable(self):
        with captured_stdout() as out:
            call_command("dgii_inbound_persistence_lab", persist_lab_records=True, json_flag=True)
        report = json.loads(out.getvalue())
        self.assertFalse(report["dry_run"])
        self.assertTrue(report["persist_lab_records"])
        self.assertFalse(report["certification_evidence"])
        self.assertGreater(report["created_count"], 0)
        self.assertGreater(InboundXMLLabRecord.objects.count(), 0)

    def test_command_path_file(self):
        fixture = FIXTURE_DIR / "synthetic_ecf_unsigned.xml"
        with captured_stdout() as out:
            call_command(
                "dgii_inbound_persistence_lab",
                path=str(fixture),
                persist_lab_records=True,
                json_flag=True,
            )
        report = json.loads(out.getvalue())
        self.assertEqual(report["result_count"], 1)

    def test_summary_only(self):
        with captured_stdout() as out:
            call_command("dgii_inbound_persistence_lab", summary_only=True)
        text = out.getvalue()
        self.assertIn("result_count:", text)
        self.assertNotIn("sha256=", text)

    def test_command_does_not_create_production_models_or_track_id(self):
        before_invoice = Invoice.objects.count()
        before_doc = Document.objects.count()
        before_ecf = ECFDocument.objects.count()
        call_command("dgii_inbound_persistence_lab", persist_lab_records=True, json_flag=True)
        self.assertEqual(Invoice.objects.count(), before_invoice)
        self.assertEqual(Document.objects.count(), before_doc)
        self.assertEqual(ECFDocument.objects.count(), before_ecf)
        self.assertFalse(InboundXMLLabRecord.objects.exclude(track_id__isnull=True).exclude(track_id="").exists())


class Phase031OtherLabsDoNotPersistTests(TestCase):
    def test_xml_schema_signature_labs_do_not_persist(self):
        xml_bytes = (FIXTURE_DIR / "synthetic_ecf_unsigned.xml").read_bytes()
        before = InboundXMLLabRecord.objects.count()
        lab = analyze_inbound_xml(xml_bytes, filename="synthetic_ecf_unsigned.xml")
        schema = analyze_inbound_xml_with_local_xsd(xml_bytes, filename="synthetic_ecf_unsigned.xml")
        signature = analyze_inbound_xml_with_signature_lab(xml_bytes, filename="synthetic_ecf_unsigned.xml")
        self.assertEqual(build_lab_report([lab])["persistence_status"], "NOT_RUN_BY_DEFAULT")
        self.assertEqual(build_schema_lab_report([schema])["persistence_status"], "NOT_RUN_BY_DEFAULT")
        self.assertEqual(build_signature_lab_report([signature])["persistence_status"], "NOT_RUN_BY_DEFAULT")
        call_command("dgii_inbound_xml_lab", json_flag=True)
        call_command("dgii_inbound_schema_lab", json_flag=True)
        call_command("dgii_inbound_signature_lab", json_flag=True)
        self.assertEqual(InboundXMLLabRecord.objects.count(), before)


class Phase031ReceiverContractTests(TestCase):
    def test_receiver_contract_reports_persistence_lab(self):
        meta = get_receiver_contract_metadata()
        self.assertTrue(meta["non_production_inbound_persistence_lab_available"])
        self.assertFalse(meta["production_persistence_ready"])
        self.assertFalse(meta["public_route_persistence_enabled"])
        self.assertEqual(meta["persistence_scope"], "NON_PRODUCTION_LAB_ONLY")
        self.assertEqual(meta["raw_xml_storage_default"], "DISABLED")
        self.assertEqual(meta["track_id_creation"], "DISABLED")


class Phase031ReadinessBlockerTests(TestCase):
    PHASE_031_BLOCKERS = (
        "inbound_persistence_lab_only",
        "production_inbound_persistence_not_implemented",
        "public_route_persistence_disabled",
        "raw_xml_storage_policy_not_approved",
        "inbound_lab_records_not_fiscal_documents",
        "inbound_persistence_not_certification_evidence",
        "inbound_business_workflow_not_implemented",
        "inbound_audit_policy_not_approved",
    )

    def test_readiness_includes_phase_031_blockers(self):
        with captured_stdout() as out:
            call_command("dgii_readiness_report", json_flag=True)
        report = json.loads(out.getvalue())
        self.assertEqual(report["overall_status"], "BLOCKED")
        self.assertEqual(report["compliance_status"], "NOT_DGII_COMPLIANT")
        self.assertFalse(report["dgii_submission_allowed"])
        self.assertFalse(report["production_signature_ready"])
        for blocker in self.PHASE_031_BLOCKERS:
            self.assertIn(blocker, report["blockers"])

    def test_doc_exists(self):
        repo_root = Path(__file__).resolve().parents[1]
        self.assertTrue(
            (repo_root / "docs/dgii/lab/NON_PRODUCTION_INBOUND_PERSISTENCE_LAB.md").is_file()
        )


class Phase031PublicRouteBoundaryTests(TestCase):
    def test_public_disabled_routes_return_503(self):
        response = dgii_recepcion_ecf(RequestFactory().get("/fe/recepcion/api/ecf"))
        self.assertEqual(response.status_code, 503)

    @patch("ecf.dgii.inbound_persistence_lab.persist_lab_record")
    @patch("ecf.dgii.receiver.classify_inbound_xml")
    def test_public_post_does_not_persist_or_parse(self, mock_classify, mock_persist):
        before = InboundXMLLabRecord.objects.count()
        request = RequestFactory().post(
            "/fe/recepcion/api/ecf",
            data=b'<?xml version="1.0"?><ECF/>',
            content_type="application/xml",
        )
        response = dgii_recepcion_ecf(request)
        self.assertEqual(response.status_code, 503)
        mock_classify.assert_not_called()
        mock_persist.assert_not_called()
        self.assertEqual(InboundXMLLabRecord.objects.count(), before)

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
            if name.endswith((".p12", ".pfx", ".key")) or name in {"key.pem", "privkey.pem", "private.pem"}:
                offenders.append(str(path.relative_to(repo_root)))
        self.assertEqual(offenders, [])
