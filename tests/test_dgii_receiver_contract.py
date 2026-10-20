import json
from pathlib import Path
from unittest.mock import patch

from django.core.management import call_command
from django.test import RequestFactory, TestCase
from django.test.utils import captured_stdout

from documents.models import Document
from ecf.dgii.receiver import (
    ReceiverDocumentType,
    ReceiverStatus,
    build_disabled_receiver_response,
    classify_inbound_xml,
    detect_signature_presence,
    get_receiver_contract_metadata,
    identify_xml_root,
    signature_verification_implemented,
)
from ecf.models import ECFDocument
from ecf.views.dgii_public_endpoints import (
    dgii_aprobacion_comercial_ecf,
    dgii_autenticacion_semilla,
    dgii_autenticacion_validacioncertificado,
    dgii_recepcion_ecf,
)
from invoicing.models import Invoice

_MINIMAL_ECF = b"""<?xml version="1.0" encoding="UTF-8"?>
<ECF><Encabezado><eNCF>E319000000001</eNCF></Encabezado></ECF>"""

_ECF_WITH_SIG = b"""<?xml version="1.0" encoding="UTF-8"?>
<ECF><Encabezado><eNCF>E319000000001</eNCF></Encabezado>
<Signature xmlns="http://www.w3.org/2000/09/xmldsig#"><SignedInfo/></Signature></ECF>"""

_MINIMAL_ARECF = b"""<?xml version="1.0"?><ARECF><DetalleAcuse/></ARECF>"""
_MINIMAL_ACECF = b"""<?xml version="1.0"?><ACECF><DetalleAprobacion/></ACECF>"""
_UNKNOWN_ROOT = b"""<?xml version="1.0"?><FooBar><x/></FooBar>"""
_INVALID_XML = b"not-xml"


class ReceiverClassificationTests(TestCase):
    def test_classify_ecf_root(self):
        result = classify_inbound_xml(_MINIMAL_ECF)
        self.assertEqual(result.document_type, ReceiverDocumentType.ECF)
        self.assertEqual(result.root_tag, "ECF")
        self.assertEqual(result.status, ReceiverStatus.SIGNATURE_MISSING)

    def test_classify_arecf_root(self):
        result = classify_inbound_xml(_MINIMAL_ARECF)
        self.assertEqual(result.document_type, ReceiverDocumentType.ARECF)
        self.assertEqual(result.root_tag, "ARECF")

    def test_classify_acecf_root(self):
        result = classify_inbound_xml(_MINIMAL_ACECF)
        self.assertEqual(result.document_type, ReceiverDocumentType.ACECF)
        self.assertEqual(result.root_tag, "ACECF")

    def test_classify_unknown_root_as_unsupported(self):
        result = classify_inbound_xml(_UNKNOWN_ROOT)
        self.assertEqual(result.document_type, ReceiverDocumentType.UNKNOWN)
        self.assertEqual(result.status, ReceiverStatus.UNSUPPORTED_ROOT)
        self.assertEqual(result.root_tag, "FooBar")

    def test_invalid_xml_returns_invalid_xml(self):
        self.assertEqual(identify_xml_root(_INVALID_XML), ReceiverStatus.INVALID_XML)
        result = classify_inbound_xml(_INVALID_XML)
        self.assertEqual(result.status, ReceiverStatus.INVALID_XML)

    def test_signature_presence_true_when_signature_element_exists(self):
        self.assertTrue(detect_signature_presence(_ECF_WITH_SIG))

    def test_signature_presence_false_when_signature_missing(self):
        self.assertFalse(detect_signature_presence(_MINIMAL_ECF))

    def test_signature_verification_not_implemented(self):
        self.assertFalse(signature_verification_implemented())
        result = classify_inbound_xml(_ECF_WITH_SIG)
        self.assertEqual(result.status, ReceiverStatus.SIGNATURE_VERIFICATION_NOT_IMPLEMENTED)
        self.assertTrue(result.signature_present)


class DisabledReceiverResponseTests(TestCase):
    def test_disabled_response_boundary_fields(self):
        payload = build_disabled_receiver_response()
        self.assertEqual(payload["status"], ReceiverStatus.DISABLED)
        self.assertEqual(payload["compliance_status"], "NOT_DGII_COMPLIANT")
        self.assertFalse(payload["dgii_submission_allowed"])
        self.assertIsNone(payload["track_id"])


class PublicDisabledRouteTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.views = (
            dgii_recepcion_ecf,
            dgii_aprobacion_comercial_ecf,
            dgii_autenticacion_semilla,
            dgii_autenticacion_validacioncertificado,
        )

    def test_public_disabled_routes_return_503(self):
        for view in self.views:
            response = view(self.factory.get("/fe/stub/"))
            self.assertEqual(response.status_code, 503)
            payload = json.loads(response.content)
            self.assertEqual(payload["status"], ReceiverStatus.DISABLED)

    @patch("ecf.dgii.receiver.classify_inbound_xml")
    @patch("ecf.dgii.receiver.identify_xml_root")
    def test_public_disabled_post_does_not_parse_xml(self, mock_identify, mock_classify):
        before_invoice = Invoice.objects.count()
        before_doc = Document.objects.count()
        before_ecf = ECFDocument.objects.count()
        xml_body = b'<?xml version="1.0"?><ECF><eNCF>E319000000001</eNCF></ECF>'

        for view in self.views:
            request = self.factory.post(
                "/fe/stub/",
                data=xml_body,
                content_type="application/xml",
            )
            response = view(request)
            self.assertEqual(response.status_code, 503)

        mock_identify.assert_not_called()
        mock_classify.assert_not_called()
        self.assertEqual(Invoice.objects.count(), before_invoice)
        self.assertEqual(Document.objects.count(), before_doc)
        self.assertEqual(ECFDocument.objects.count(), before_ecf)


class ReceiverContractCommandTests(TestCase):
    def test_command_runs(self):
        with captured_stdout() as out:
            call_command("dgii_receiver_contract")
        text = out.getvalue()
        self.assertIn("NOT_DGII_COMPLIANT", text)
        self.assertIn("receiver_processing_enabled: False", text)

    def test_json_output_is_parseable(self):
        with captured_stdout() as out:
            call_command("dgii_receiver_contract", json_flag=True)
        payload = json.loads(out.getvalue())
        self.assertFalse(payload["public_endpoints_enabled"])
        self.assertFalse(payload["receiver_processing_enabled"])
        self.assertEqual(payload["signature_verification"], "NOT_IMPLEMENTED")
        self.assertEqual(payload["persistence"], "NOT_IMPLEMENTED")
        self.assertEqual(payload["readiness_status"], "BLOCKED")
        self.assertEqual(payload["compliance_status"], "NOT_DGII_COMPLIANT")
        self.assertFalse(payload["dgii_submission_allowed"])
        self.assertEqual(payload["track_id_creation"], "DISABLED")
        self.assertFalse(payload["dgii_call_made"])
        self.assertIsNone(payload["track_id"])

    def test_metadata_helper_matches_command(self):
        meta = get_receiver_contract_metadata()
        self.assertFalse(meta["public_endpoints_enabled"])
        self.assertFalse(meta["receiver_processing_enabled"])


class Phase027ReadinessBlockerTests(TestCase):
    PHASE_027_BLOCKERS = (
        "receiver_processing_not_implemented",
        "inbound_xml_signature_verification_not_implemented",
        "inbound_persistence_not_implemented",
        "inbound_duplicate_detection_not_implemented",
        "acuse_receiver_workflow_not_implemented",
        "aprobacion_comercial_receiver_workflow_not_implemented",
        "ecf_receiver_workflow_not_implemented",
        "receiver_security_controls_not_approved",
    )

    def test_readiness_includes_phase_027_blockers(self):
        with captured_stdout() as out:
            call_command("dgii_readiness_report", json_flag=True)
        report = json.loads(out.getvalue())
        self.assertEqual(report["overall_status"], "BLOCKED")
        self.assertEqual(report["compliance_status"], "NOT_DGII_COMPLIANT")
        self.assertFalse(report["dgii_submission_allowed"])
        self.assertFalse(report["dgii_call_made"])
        self.assertIsNone(report["track_id"])
        self.assertTrue(report["not_certification_evidence"])
        for blocker in self.PHASE_027_BLOCKERS:
            self.assertIn(blocker, report["blockers"])

    def test_receiver_contract_doc_exists(self):
        repo_root = Path(__file__).resolve().parents[1]
        self.assertTrue(
            (
                repo_root
                / "docs/dgii/endpoints/PRE_CERTIFICATION_RECEIVER_ENDPOINT_CONTRACT.md"
            ).is_file()
        )
