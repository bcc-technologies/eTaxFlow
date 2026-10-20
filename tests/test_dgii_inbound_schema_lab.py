import json
from pathlib import Path
from unittest.mock import patch

from django.core.management import call_command
from django.test import RequestFactory, TestCase
from django.test.utils import captured_stdout

from documents.models import Document
from ecf.dgii import inbound_schema_lab as schema_lab_module
from ecf.dgii.inbound_lab import analyze_inbound_xml, build_lab_report
from ecf.dgii.inbound_schema_lab import (
    DEFAULT_XSD_BY_DOCUMENT_TYPE,
    SCHEMA_VALIDATION_SCOPE,
    analyze_inbound_xml_with_local_xsd,
    analyze_path_with_local_xsd,
    find_local_xsd_for_document_type,
    validate_xml_against_local_xsd,
)
from ecf.dgii.receiver import ReceiverDocumentType, get_receiver_contract_metadata
from ecf.models import ECFDocument
from ecf.views.dgii_public_endpoints import dgii_recepcion_ecf
from invoicing.models import Invoice

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures/dgii/inbound_lab"
SOURCES_DIR = Path(__file__).resolve().parents[1] / "docs/dgii/sources"


class InboundSchemaLabImportTests(TestCase):
    def test_module_imports(self):
        self.assertTrue(hasattr(schema_lab_module, "analyze_inbound_xml_with_local_xsd"))
        self.assertTrue(hasattr(schema_lab_module, "find_local_xsd_for_document_type"))


class LocalXsdMappingTests(TestCase):
    def test_ecf_maps_to_tipo31_xsd_if_present(self):
        mapping = find_local_xsd_for_document_type("ECF")
        self.assertEqual(mapping.xsd_filename, "e-CF_31_v1.0.xsd")
        if (SOURCES_DIR / "e-CF_31_v1.0.xsd").is_file():
            self.assertTrue(mapping.xsd_available)
            self.assertTrue(mapping.xsd_path.endswith("e-CF_31_v1.0.xsd"))

    def test_arecf_maps_to_arecf_xsd_if_present(self):
        mapping = find_local_xsd_for_document_type("ARECF")
        self.assertEqual(mapping.xsd_filename, "ARECF_v1.0.xsd")
        if (SOURCES_DIR / "ARECF_v1.0.xsd").is_file():
            self.assertTrue(mapping.xsd_available)

    def test_acecf_maps_to_acecf_xsd_if_present(self):
        mapping = find_local_xsd_for_document_type("ACECF")
        self.assertEqual(mapping.xsd_filename, "ACECF_v1.0.xsd")
        if (SOURCES_DIR / "ACECF_v1.0.xsd").is_file():
            self.assertTrue(mapping.xsd_available)

    def test_unknown_root_has_no_xsd_mapping(self):
        mapping = find_local_xsd_for_document_type("UNKNOWN")
        self.assertFalse(mapping.xsd_available)
        self.assertEqual(mapping.status, "UNSUPPORTED")

    def test_missing_xsd_is_reported_without_crash(self):
        result = validate_xml_against_local_xsd(b"<ECF/>", "docs/dgii/sources/does-not-exist.xsd")
        self.assertFalse(result.xsd_available)
        self.assertFalse(result.local_xsd_valid)
        self.assertGreater(result.xsd_error_count, 0)

    def test_invalid_xml_is_reported_without_crash(self):
        mapping = find_local_xsd_for_document_type("ECF")
        result = validate_xml_against_local_xsd(b"<ECF><Unclosed>", mapping.xsd_path)
        self.assertFalse(result.local_xsd_valid)
        self.assertIn("invalid_xml", result.xsd_errors)


class SyntheticFixtureSchemaLabTests(TestCase):
    def _assert_boundary(self, result):
        payload = result.to_dict()
        self.assertEqual(payload["schema_validation_scope"], SCHEMA_VALIDATION_SCOPE)
        self.assertEqual(payload["compliance_status"], "NOT_DGII_COMPLIANT")
        self.assertFalse(payload["dgii_submission_allowed"])
        self.assertFalse(payload["certification_evidence"])
        self.assertFalse(payload["persisted"])
        self.assertFalse(payload["dgii_call_made"])
        self.assertIsNone(payload["track_id"])
        self.assertFalse(payload["signature_verified"])
        self.assertIn("xsd_path", payload)
        self.assertIn("xsd_available", payload)
        self.assertIn("xsd_compiled", payload)
        self.assertIn("local_xsd_valid", payload)
        self.assertIn("xsd_error_count", payload)
        self.assertIn("xsd_errors", payload)

    def test_synthetic_ecf_unsigned_has_xsd_result_fields(self):
        path = FIXTURE_DIR / "synthetic_ecf_unsigned.xml"
        result = analyze_inbound_xml_with_local_xsd(path.read_bytes(), filename=path.name)
        self.assertEqual(result.document_type, ReceiverDocumentType.ECF)
        self._assert_boundary(result)

    def test_synthetic_arecf_unsigned_has_xsd_result_fields(self):
        path = FIXTURE_DIR / "synthetic_arecf_unsigned.xml"
        result = analyze_inbound_xml_with_local_xsd(path.read_bytes(), filename=path.name)
        self.assertEqual(result.document_type, ReceiverDocumentType.ARECF)
        self._assert_boundary(result)

    def test_synthetic_acecf_unsigned_has_xsd_result_fields(self):
        path = FIXTURE_DIR / "synthetic_acecf_unsigned.xml"
        result = analyze_inbound_xml_with_local_xsd(path.read_bytes(), filename=path.name)
        self.assertEqual(result.document_type, ReceiverDocumentType.ACECF)
        self._assert_boundary(result)

    def test_placeholder_signature_is_not_verified(self):
        path = FIXTURE_DIR / "synthetic_ecf_signed_placeholder.xml"
        result = analyze_inbound_xml_with_local_xsd(path.read_bytes(), filename=path.name)
        self.assertTrue(result.signature_present)
        self.assertFalse(result.signature_verified)


class InboundSchemaLabCommandTests(TestCase):
    def test_command_runs(self):
        with captured_stdout() as out:
            call_command("dgii_inbound_schema_lab")
        text = out.getvalue()
        self.assertIn("NOT_DGII_COMPLIANT", text)
        self.assertIn("LOCAL_OFFLINE_ONLY", text)
        self.assertIn("NON_OFFICIAL_SYNTHETIC_SAMPLE", text)
        self.assertIn("not_certification_evidence=true", text)

    def test_command_json_is_parseable(self):
        with captured_stdout() as out:
            call_command("dgii_inbound_schema_lab", json_flag=True)
        report = json.loads(out.getvalue())
        self.assertEqual(report["schema_validation_scope"], "LOCAL_OFFLINE_ONLY")
        self.assertFalse(report["certification_evidence"])
        self.assertGreaterEqual(report["fixture_count"], 1)
        self.assertIn("e-CF_31_v1.0.xsd", report["xsd_mapping"]["ECF"])

    def test_command_path_file(self):
        fixture = FIXTURE_DIR / "synthetic_ecf_unsigned.xml"
        with captured_stdout() as out:
            call_command("dgii_inbound_schema_lab", path=str(fixture), json_flag=True)
        report = json.loads(out.getvalue())
        self.assertEqual(report["fixture_count"], 1)
        self.assertEqual(report["results"][0]["document_type"], "ECF")

    def test_command_summary_only(self):
        with captured_stdout() as out:
            call_command("dgii_inbound_schema_lab", summary_only=True)
        text = out.getvalue()
        self.assertIn("fixture_count:", text)
        self.assertNotIn("sig_present=", text)

    def test_command_does_not_mutate_database(self):
        before_invoice = Invoice.objects.count()
        before_doc = Document.objects.count()
        before_ecf = ECFDocument.objects.count()
        call_command("dgii_inbound_schema_lab", json_flag=True)
        self.assertEqual(Invoice.objects.count(), before_invoice)
        self.assertEqual(Document.objects.count(), before_doc)
        self.assertEqual(ECFDocument.objects.count(), before_ecf)

    def test_original_inbound_xml_lab_does_not_run_xsd_by_default(self):
        xml_bytes = (FIXTURE_DIR / "synthetic_ecf_unsigned.xml").read_bytes()
        lab = analyze_inbound_xml(xml_bytes, filename="synthetic_ecf_unsigned.xml")
        payload = lab.to_dict()
        self.assertNotIn("local_xsd_valid", payload)
        report = build_lab_report([lab])
        self.assertEqual(report["schema_validation_status"], "NOT_RUN_BY_DEFAULT")
        self.assertEqual(report["schema_validation_command"], "dgii_inbound_schema_lab")
        self.assertTrue(report["schema_validation_available"])


class Phase029ReceiverContractTests(TestCase):
    def test_receiver_contract_reports_schema_lab(self):
        meta = get_receiver_contract_metadata()
        self.assertTrue(meta["local_inbound_schema_lab_available"])
        self.assertEqual(meta["schema_validation_scope"], "LOCAL_OFFLINE_ONLY")
        self.assertEqual(meta["schema_validation_command"], "dgii_inbound_schema_lab")
        self.assertFalse(meta["schema_validation_certification_evidence"])
        self.assertEqual(meta["supported_schema_roots"], ["ECF", "ARECF", "ACECF"])
        self.assertFalse(meta["public_endpoints_enabled"])
        self.assertEqual(meta["persistence"], "NOT_IMPLEMENTED")
        self.assertEqual(meta["signature_verification"], "NOT_IMPLEMENTED")


class Phase029ReadinessBlockerTests(TestCase):
    PHASE_029_BLOCKERS = (
        "local_inbound_schema_validation_lab_only",
        "local_xsd_validation_not_dgii_acceptance",
        "official_certification_fixtures_not_loaded",
        "inbound_xsd_errors_not_resolved",
        "inbound_schema_mapping_not_human_reviewed",
        "inbound_signature_validation_still_not_implemented",
        "inbound_public_processing_still_disabled",
        "inbound_persistence_still_not_implemented",
    )

    def test_readiness_includes_phase_029_blockers(self):
        with captured_stdout() as out:
            call_command("dgii_readiness_report", json_flag=True)
        report = json.loads(out.getvalue())
        self.assertEqual(report["overall_status"], "BLOCKED")
        self.assertEqual(report["compliance_status"], "NOT_DGII_COMPLIANT")
        self.assertFalse(report["dgii_submission_allowed"])
        self.assertFalse(report["dgii_call_made"])
        self.assertIsNone(report["track_id"])
        for blocker in self.PHASE_029_BLOCKERS:
            self.assertIn(blocker, report["blockers"])

    def test_schema_lab_doc_exists(self):
        repo_root = Path(__file__).resolve().parents[1]
        self.assertTrue(
            (repo_root / "docs/dgii/lab/LOCAL_INBOUND_SCHEMA_VALIDATION_LAB.md").is_file()
        )


class Phase029PublicRouteBoundaryTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_public_disabled_routes_return_503(self):
        response = dgii_recepcion_ecf(self.factory.get("/fe/recepcion/api/ecf"))
        self.assertEqual(response.status_code, 503)

    @patch("ecf.dgii.inbound_schema_lab.analyze_inbound_xml_with_local_xsd")
    @patch("ecf.dgii.receiver.classify_inbound_xml")
    def test_public_disabled_post_does_not_parse_or_validate(self, mock_classify, mock_schema):
        before_ecf = ECFDocument.objects.count()
        request = self.factory.post(
            "/fe/recepcion/api/ecf",
            data=b'<?xml version="1.0"?><ECF/>',
            content_type="application/xml",
        )
        response = dgii_recepcion_ecf(request)
        self.assertEqual(response.status_code, 503)
        mock_classify.assert_not_called()
        mock_schema.assert_not_called()
        self.assertEqual(ECFDocument.objects.count(), before_ecf)

    def test_analyze_path_directory_is_deterministic(self):
        results = analyze_path_with_local_xsd(FIXTURE_DIR)
        names = [item.filename for item in results]
        self.assertEqual(names, sorted(names))
        self.assertEqual(DEFAULT_XSD_BY_DOCUMENT_TYPE["ECF"], "e-CF_31_v1.0.xsd")
