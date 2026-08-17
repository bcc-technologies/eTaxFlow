import json
from pathlib import Path
from unittest.mock import patch

from django.core.management import call_command
from django.test import RequestFactory, TestCase
from django.test.utils import captured_stdout

from documents.models import Document
from ecf.dgii.inbound_lab import (
    DEFAULT_FIXTURE_DIR,
    analyze_fixture_directory,
    analyze_fixture_file,
    analyze_inbound_xml,
    compute_sha256,
)
from ecf.dgii.receiver import ReceiverDocumentType, ReceiverStatus, get_receiver_contract_metadata
from ecf.models import ECFDocument
from ecf.views.dgii_public_endpoints import (
    dgii_aprobacion_comercial_ecf,
    dgii_autenticacion_semilla,
    dgii_recepcion_ecf,
)
from invoicing.models import Invoice

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures/dgii/inbound_lab"
EXPECTED_FIXTURES = (
    "synthetic_ecf_unsigned.xml",
    "synthetic_ecf_signed_placeholder.xml",
    "synthetic_arecf_unsigned.xml",
    "synthetic_arecf_signed_placeholder.xml",
    "synthetic_acecf_unsigned.xml",
    "synthetic_acecf_signed_placeholder.xml",
    "synthetic_unknown_root.xml",
    "synthetic_invalid.xml",
)


class InboundLabFixtureTests(TestCase):
    def test_fixture_directory_exists(self):
        self.assertTrue(FIXTURE_DIR.is_dir())

    def test_all_synthetic_fixture_files_exist(self):
        for name in EXPECTED_FIXTURES:
            self.assertTrue((FIXTURE_DIR / name).is_file(), name)

    def test_ecf_unsigned_fixture(self):
        result = analyze_fixture_file(FIXTURE_DIR / "synthetic_ecf_unsigned.xml")
        self.assertEqual(result.document_type, ReceiverDocumentType.ECF)
        self.assertEqual(result.root_tag, "ECF")
        self.assertFalse(result.signature_present)
        self.assertEqual(result.status, ReceiverStatus.SIGNATURE_MISSING)

    def test_ecf_signed_placeholder_fixture(self):
        result = analyze_fixture_file(FIXTURE_DIR / "synthetic_ecf_signed_placeholder.xml")
        self.assertEqual(result.document_type, ReceiverDocumentType.ECF)
        self.assertTrue(result.signature_present)
        self.assertEqual(result.status, ReceiverStatus.SIGNATURE_VERIFICATION_NOT_IMPLEMENTED)

    def test_arecf_unsigned_fixture(self):
        result = analyze_fixture_file(FIXTURE_DIR / "synthetic_arecf_unsigned.xml")
        self.assertEqual(result.document_type, ReceiverDocumentType.ARECF)
        self.assertEqual(result.root_tag, "ARECF")
        self.assertFalse(result.signature_present)

    def test_arecf_signed_placeholder_fixture(self):
        result = analyze_fixture_file(FIXTURE_DIR / "synthetic_arecf_signed_placeholder.xml")
        self.assertEqual(result.document_type, ReceiverDocumentType.ARECF)
        self.assertTrue(result.signature_present)

    def test_acecf_unsigned_fixture(self):
        result = analyze_fixture_file(FIXTURE_DIR / "synthetic_acecf_unsigned.xml")
        self.assertEqual(result.document_type, ReceiverDocumentType.ACECF)
        self.assertEqual(result.root_tag, "ACECF")

    def test_acecf_signed_placeholder_fixture(self):
        result = analyze_fixture_file(FIXTURE_DIR / "synthetic_acecf_signed_placeholder.xml")
        self.assertEqual(result.document_type, ReceiverDocumentType.ACECF)
        self.assertTrue(result.signature_present)

    def test_unknown_root_fixture(self):
        result = analyze_fixture_file(FIXTURE_DIR / "synthetic_unknown_root.xml")
        self.assertEqual(result.document_type, ReceiverDocumentType.UNKNOWN)
        self.assertEqual(result.status, ReceiverStatus.UNSUPPORTED_ROOT)
        self.assertEqual(result.root_tag, "UNKNOWNLABROOT")

    def test_invalid_fixture(self):
        result = analyze_fixture_file(FIXTURE_DIR / "synthetic_invalid.xml")
        self.assertEqual(result.status, ReceiverStatus.INVALID_XML)
        self.assertIn("invalid_xml", result.errors)

    def test_hash_is_deterministic(self):
        data = (FIXTURE_DIR / "synthetic_ecf_unsigned.xml").read_bytes()
        self.assertEqual(compute_sha256(data), compute_sha256(data))

    def test_lab_result_boundary_fields(self):
        result = analyze_inbound_xml(b"<ECF/>", filename="inline.xml")
        payload = result.to_dict()
        self.assertFalse(payload["persisted"])
        self.assertFalse(payload["dgii_call_made"])
        self.assertIsNone(payload["track_id"])
        self.assertFalse(payload["certification_evidence"])
        self.assertEqual(payload["compliance_status"], "NOT_DGII_COMPLIANT")
        self.assertFalse(payload["dgii_submission_allowed"])

    def test_analyze_fixture_directory(self):
        results = analyze_fixture_directory(FIXTURE_DIR)
        self.assertEqual(len(results), len(EXPECTED_FIXTURES))


class InboundXmlLabCommandTests(TestCase):
    def test_lab_command_runs(self):
        with captured_stdout() as out:
            call_command("dgii_inbound_xml_lab")
        text = out.getvalue()
        self.assertIn("NOT_DGII_COMPLIANT", text)
        self.assertIn("NON_OFFICIAL_SYNTHETIC_SAMPLE", text)
        self.assertIn("not_certification_evidence: True", text)

    def test_lab_command_json_is_parseable(self):
        with captured_stdout() as out:
            call_command("dgii_inbound_xml_lab", json_flag=True)
        report = json.loads(out.getvalue())
        self.assertEqual(report["lab_mode"], "NON_PRODUCTION_ONLY")
        self.assertFalse(report["certification_evidence"])
        self.assertTrue(report["not_certification_evidence"])
        self.assertEqual(report["fixture_count"], len(EXPECTED_FIXTURES))

    def test_lab_command_path_file(self):
        fixture = FIXTURE_DIR / "synthetic_ecf_unsigned.xml"
        with captured_stdout() as out:
            call_command("dgii_inbound_xml_lab", path=str(fixture), json_flag=True)
        report = json.loads(out.getvalue())
        self.assertEqual(report["fixture_count"], 1)
        self.assertEqual(report["results"][0]["document_type"], "ECF")

    def test_lab_command_does_not_mutate_database(self):
        before_invoice = Invoice.objects.count()
        before_doc = Document.objects.count()
        before_ecf = ECFDocument.objects.count()
        call_command("dgii_inbound_xml_lab", json_flag=True)
        self.assertEqual(Invoice.objects.count(), before_invoice)
        self.assertEqual(Document.objects.count(), before_doc)
        self.assertEqual(ECFDocument.objects.count(), before_ecf)


class Phase028ReceiverContractTests(TestCase):
    def test_receiver_contract_reports_lab_available(self):
        meta = get_receiver_contract_metadata()
        self.assertTrue(meta["inbound_xml_lab_available"])
        self.assertEqual(meta["lab_mode"], "NON_PRODUCTION_ONLY")
        self.assertTrue(meta["synthetic_fixtures_available"])
        self.assertEqual(meta["persistence"], "NOT_IMPLEMENTED")
        self.assertEqual(meta["signature_verification"], "NOT_IMPLEMENTED")
        self.assertEqual(meta["schema_validation"], "NOT_CLAIMED")
        self.assertFalse(meta["certification_evidence"])

    def test_receiver_contract_command_json(self):
        with captured_stdout() as out:
            call_command("dgii_receiver_contract", json_flag=True)
        payload = json.loads(out.getvalue())
        self.assertTrue(payload["inbound_xml_lab_available"])


class Phase028ReadinessBlockerTests(TestCase):
    PHASE_028_BLOCKERS = (
        "inbound_lab_synthetic_only",
        "inbound_schema_validation_not_claimed",
        "inbound_signature_verification_not_implemented",
        "inbound_persistence_not_implemented",
        "inbound_public_processing_disabled",
        "inbound_official_test_set_not_loaded",
        "inbound_lab_not_certification_evidence",
    )

    def test_readiness_includes_phase_028_blockers(self):
        with captured_stdout() as out:
            call_command("dgii_readiness_report", json_flag=True)
        report = json.loads(out.getvalue())
        self.assertEqual(report["overall_status"], "BLOCKED")
        self.assertEqual(report["compliance_status"], "NOT_DGII_COMPLIANT")
        self.assertFalse(report["dgii_submission_allowed"])
        self.assertFalse(report["dgii_call_made"])
        self.assertIsNone(report["track_id"])
        for blocker in self.PHASE_028_BLOCKERS:
            self.assertIn(blocker, report["blockers"])

    def test_lab_doc_exists(self):
        repo_root = Path(__file__).resolve().parents[1]
        self.assertTrue(
            (repo_root / "docs/dgii/lab/NON_PRODUCTION_INBOUND_XML_LAB.md").is_file()
        )


class Phase028PublicRouteBoundaryTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_public_disabled_routes_return_503(self):
        for view in (dgii_recepcion_ecf, dgii_aprobacion_comercial_ecf, dgii_autenticacion_semilla):
            response = view(self.factory.get("/fe/stub/"))
            self.assertEqual(response.status_code, 503)

    @patch("ecf.dgii.receiver.classify_inbound_xml")
    @patch("ecf.dgii.inbound_lab.analyze_inbound_xml")
    def test_public_disabled_post_does_not_parse_or_lab(self, mock_lab, mock_classify):
        before_ecf = ECFDocument.objects.count()
        xml_body = b'<?xml version="1.0"?><ECF/>'
        request = self.factory.post("/fe/recepcion/api/ecf", data=xml_body, content_type="application/xml")
        response = dgii_recepcion_ecf(request)
        self.assertEqual(response.status_code, 503)
        mock_lab.assert_not_called()
        mock_classify.assert_not_called()
        self.assertEqual(ECFDocument.objects.count(), before_ecf)

    def test_default_fixture_dir_matches_repo(self):
        self.assertEqual(DEFAULT_FIXTURE_DIR, Path("tests/fixtures/dgii/inbound_lab"))
