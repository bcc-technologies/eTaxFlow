import json
from pathlib import Path
from unittest.mock import patch

from django.core.management import call_command
from django.test import RequestFactory, TestCase
from django.test.utils import captured_stdout

from documents.models import Document
from ecf.dgii import inbound_signature_lab as signature_lab_module
from ecf.dgii.inbound_lab import analyze_inbound_xml, build_lab_report
from ecf.dgii.inbound_schema_lab import analyze_inbound_xml_with_local_xsd, build_schema_lab_report
from ecf.dgii.inbound_signature_lab import (
    VERIFICATION_SCOPE,
    SignatureLabStatus,
    analyze_inbound_xml_with_signature_lab,
    analyze_path_with_signature_lab,
    classify_signature_status,
)
from ecf.dgii.receiver import get_receiver_contract_metadata
from ecf.models import ECFDocument
from ecf.views.dgii_public_endpoints import dgii_recepcion_ecf
from invoicing.models import Invoice
from tests.helpers import test_only_xmldsig

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures/dgii/inbound_lab"


class InboundSignatureLabImportTests(TestCase):
    def test_module_imports(self):
        self.assertTrue(hasattr(signature_lab_module, "analyze_inbound_xml_with_signature_lab"))
        self.assertTrue(hasattr(signature_lab_module, "inspect_signature_metadata"))
        self.assertFalse(test_only_xmldsig.XMLDSIG_VERIFICATION_IMPLEMENTED)


class SyntheticSignatureFixtureTests(TestCase):
    def _result(self, name: str):
        path = FIXTURE_DIR / name
        return analyze_inbound_xml_with_signature_lab(path.read_bytes(), filename=name)

    def _assert_boundary(self, result):
        payload = result.to_dict()
        self.assertEqual(payload["verification_scope"], VERIFICATION_SCOPE)
        self.assertFalse(payload["production_signature_ready"])
        self.assertEqual(payload["compliance_status"], "NOT_DGII_COMPLIANT")
        self.assertFalse(payload["dgii_submission_allowed"])
        self.assertFalse(payload["certification_evidence"])
        self.assertFalse(payload["persisted"])
        self.assertFalse(payload["dgii_call_made"])
        self.assertIsNone(payload["track_id"])
        self.assertFalse(payload["signature_verified"])

    def test_unsigned_ecf_missing(self):
        result = self._result("synthetic_ecf_unsigned.xml")
        self.assertFalse(result.signature_present)
        self.assertEqual(result.signature_verification_status, SignatureLabStatus.MISSING)
        self._assert_boundary(result)

    def test_placeholder_ecf_not_valid(self):
        result = self._result("synthetic_ecf_signed_placeholder.xml")
        self.assertTrue(result.signature_present)
        self.assertEqual(result.signature_verification_status, SignatureLabStatus.PLACEHOLDER_ONLY)
        self.assertNotEqual(result.signature_verification_status, SignatureLabStatus.TEST_ONLY_VALID)
        self._assert_boundary(result)

    def test_unsigned_arecf_missing(self):
        result = self._result("synthetic_arecf_unsigned.xml")
        self.assertFalse(result.signature_present)

    def test_placeholder_arecf_not_production_valid(self):
        result = self._result("synthetic_arecf_signed_placeholder.xml")
        self.assertTrue(result.signature_present)
        self.assertFalse(result.signature_verified)
        self.assertFalse(result.production_signature_ready)
        self.assertEqual(result.signature_verification_status, SignatureLabStatus.PLACEHOLDER_ONLY)

    def test_unsigned_acecf_missing(self):
        result = self._result("synthetic_acecf_unsigned.xml")
        self.assertFalse(result.signature_present)

    def test_placeholder_acecf_not_production_valid(self):
        result = self._result("synthetic_acecf_signed_placeholder.xml")
        self.assertTrue(result.signature_present)
        self.assertFalse(result.signature_verified)
        self.assertFalse(result.production_signature_ready)

    def test_invalid_xml_parse_error(self):
        result = self._result("synthetic_invalid.xml")
        self.assertEqual(result.signature_verification_status, SignatureLabStatus.PARSE_ERROR)
        self.assertEqual(classify_signature_status(b"<ECF><Unclosed>"), SignatureLabStatus.PARSE_ERROR)

    def test_unknown_root_does_not_crash(self):
        result = self._result("synthetic_unknown_root.xml")
        self.assertEqual(result.document_type, "UNKNOWN")
        self.assertFalse(result.signature_present)


class InboundSignatureLabCommandTests(TestCase):
    def test_command_runs(self):
        with captured_stdout() as out:
            call_command("dgii_inbound_signature_lab")
        text = out.getvalue()
        self.assertIn("NOT_DGII_COMPLIANT", text)
        self.assertIn("LOCAL_OFFLINE_TEST_ONLY", text)
        self.assertIn("NON_OFFICIAL_SYNTHETIC_SAMPLE", text)
        self.assertIn("not_certification_evidence=true", text)
        self.assertIn("production_signature_ready=false", text)

    def test_command_json_is_parseable(self):
        with captured_stdout() as out:
            call_command("dgii_inbound_signature_lab", json_flag=True)
        report = json.loads(out.getvalue())
        self.assertEqual(report["verification_scope"], VERIFICATION_SCOPE)
        self.assertFalse(report["production_signature_ready"])
        self.assertEqual(report["cryptographic_xmldsig_verification"], "NOT_IMPLEMENTED")
        self.assertGreaterEqual(report["fixture_count"], 1)

    def test_command_path_file(self):
        fixture = FIXTURE_DIR / "synthetic_ecf_signed_placeholder.xml"
        with captured_stdout() as out:
            call_command("dgii_inbound_signature_lab", path=str(fixture), json_flag=True)
        report = json.loads(out.getvalue())
        self.assertEqual(report["fixture_count"], 1)
        self.assertEqual(report["results"][0]["signature_verification_status"], "PLACEHOLDER_ONLY")

    def test_command_summary_only(self):
        with captured_stdout() as out:
            call_command("dgii_inbound_signature_lab", summary_only=True)
        text = out.getvalue()
        self.assertIn("fixture_count:", text)
        self.assertNotIn("present=", text)

    def test_command_does_not_mutate_database(self):
        before_invoice = Invoice.objects.count()
        before_doc = Document.objects.count()
        before_ecf = ECFDocument.objects.count()
        call_command("dgii_inbound_signature_lab", json_flag=True)
        self.assertEqual(Invoice.objects.count(), before_invoice)
        self.assertEqual(Document.objects.count(), before_doc)
        self.assertEqual(ECFDocument.objects.count(), before_ecf)


class Phase030OtherLabsRemainClassificationOnlyTests(TestCase):
    def test_inbound_xml_lab_does_not_run_signature_verification(self):
        xml_bytes = (FIXTURE_DIR / "synthetic_ecf_signed_placeholder.xml").read_bytes()
        lab = analyze_inbound_xml(xml_bytes, filename="synthetic_ecf_signed_placeholder.xml")
        self.assertNotIn("signature_verification_status", lab.to_dict())
        report = build_lab_report([lab])
        self.assertEqual(report["signature_verification_status"], "NOT_RUN_BY_DEFAULT")
        self.assertEqual(report["signature_verification_command"], "dgii_inbound_signature_lab")

    def test_schema_lab_does_not_run_signature_verification(self):
        xml_bytes = (FIXTURE_DIR / "synthetic_ecf_unsigned.xml").read_bytes()
        result = analyze_inbound_xml_with_local_xsd(xml_bytes, filename="synthetic_ecf_unsigned.xml")
        payload = result.to_dict()
        self.assertNotIn("signature_verification_status", payload)
        self.assertFalse(payload["signature_verified"])
        report = build_schema_lab_report([result])
        self.assertEqual(report["signature_verification_status"], "NOT_RUN_BY_DEFAULT")


class Phase030ReceiverContractTests(TestCase):
    def test_receiver_contract_reports_signature_lab(self):
        meta = get_receiver_contract_metadata()
        self.assertTrue(meta["local_inbound_signature_lab_available"])
        self.assertEqual(meta["signature_verification_scope"], "LOCAL_OFFLINE_TEST_ONLY")
        self.assertEqual(meta["signature_verification_command"], "dgii_inbound_signature_lab")
        self.assertFalse(meta["production_signature_ready"])
        self.assertFalse(meta["certification_evidence"])
        self.assertEqual(meta["persistence"], "NOT_IMPLEMENTED")
        self.assertFalse(meta["public_endpoints_enabled"])


class Phase030ReadinessBlockerTests(TestCase):
    PHASE_030_BLOCKERS = (
        "local_inbound_signature_lab_only",
        "signature_presence_not_signature_validity",
        "production_signature_verification_not_implemented",
        "certificate_trust_chain_validation_not_implemented",
        "revocation_check_not_implemented",
        "official_certificate_policy_not_approved",
        "inbound_signature_results_not_certification_evidence",
        "inbound_public_processing_still_disabled",
        "inbound_persistence_still_not_implemented",
    )

    def test_readiness_includes_phase_030_blockers(self):
        with captured_stdout() as out:
            call_command("dgii_readiness_report", json_flag=True)
        report = json.loads(out.getvalue())
        self.assertEqual(report["overall_status"], "BLOCKED")
        self.assertEqual(report["compliance_status"], "NOT_DGII_COMPLIANT")
        self.assertFalse(report["dgii_submission_allowed"])
        self.assertFalse(report["production_signature_ready"])
        self.assertFalse(report["dgii_call_made"])
        self.assertIsNone(report["track_id"])
        for blocker in self.PHASE_030_BLOCKERS:
            self.assertIn(blocker, report["blockers"])

    def test_signature_lab_doc_exists(self):
        repo_root = Path(__file__).resolve().parents[1]
        self.assertTrue(
            (repo_root / "docs/dgii/lab/LOCAL_INBOUND_SIGNATURE_VERIFICATION_LAB.md").is_file()
        )


class Phase030PublicRouteAndKeySafetyTests(TestCase):
    def test_public_disabled_routes_return_503(self):
        response = dgii_recepcion_ecf(RequestFactory().get("/fe/recepcion/api/ecf"))
        self.assertEqual(response.status_code, 503)

    @patch("ecf.dgii.inbound_signature_lab.analyze_inbound_xml_with_signature_lab")
    @patch("ecf.dgii.receiver.classify_inbound_xml")
    def test_public_disabled_post_does_not_parse_or_verify(self, mock_classify, mock_sig):
        before_ecf = ECFDocument.objects.count()
        request = RequestFactory().post(
            "/fe/recepcion/api/ecf",
            data=b'<?xml version="1.0"?><ECF/>',
            content_type="application/xml",
        )
        response = dgii_recepcion_ecf(request)
        self.assertEqual(response.status_code, 503)
        mock_classify.assert_not_called()
        mock_sig.assert_not_called()
        self.assertEqual(ECFDocument.objects.count(), before_ecf)

    def test_no_private_key_files_added(self):
        repo_root = Path(__file__).resolve().parents[1]
        offenders = []
        skip_parts = {".venv", ".git", ".conda", "node_modules", "__pycache__"}
        for path in repo_root.rglob("*"):
            if any(part in skip_parts for part in path.parts):
                continue
            if not path.is_file():
                continue
            name = path.name.lower()
            if name.endswith((".p12", ".pfx", ".key")) or name in {"key.pem", "privkey.pem", "private.pem"}:
                offenders.append(str(path.relative_to(repo_root)))
            if "private" in name and name.endswith((".pem", ".key")):
                offenders.append(str(path.relative_to(repo_root)))
        self.assertEqual(offenders, [])

    def test_directory_analysis_is_deterministic(self):
        results = analyze_path_with_signature_lab(FIXTURE_DIR)
        names = [item.filename for item in results]
        self.assertEqual(names, sorted(names))
