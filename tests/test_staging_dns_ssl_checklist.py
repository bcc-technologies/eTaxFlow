import json
import re
from pathlib import Path

from django.core.management import call_command
from django.test import RequestFactory, TestCase, override_settings
from django.test.utils import captured_stdout

from documents.models import Document
from ecf.dgii.endpoints import get_software_registration_metadata
from ecf.models import ECFDocument
from ecf.views.dgii_public_endpoints import (
    dgii_aprobacion_comercial_ecf,
    dgii_autenticacion_semilla,
    dgii_autenticacion_validacioncertificado,
    dgii_recepcion_ecf,
    disabled_endpoint_payload,
)
from invoicing.models import Invoice


class StagingEnvExampleTests(TestCase):
    def test_env_staging_example_exists(self):
        path = Path(__file__).resolve().parents[1] / ".env.staging.example"
        self.assertTrue(path.is_file())
        text = path.read_text(encoding="utf-8")
        self.assertIn("ETAXFLOW_ENABLE_PUBLIC_DGII_ENDPOINTS=false", text)
        self.assertIn("ETAXFLOW_PUBLIC_BASE_URL=", text)
        self.assertIn("Do NOT commit", text)

    def test_env_staging_example_has_no_obvious_real_secrets(self):
        path = Path(__file__).resolve().parents[1] / ".env.staging.example"
        text = path.read_text(encoding="utf-8")
        self.assertNotIn("BEGIN PRIVATE KEY", text)
        self.assertNotIn("BEGIN CERTIFICATE", text)
        self.assertNotRegex(text, r"SECRET_KEY=.{8,}")
        self.assertIsNone(re.search(r"password=\S+", text, re.I))


class DeploymentMetadataTests(TestCase):
    def test_deployment_fields_default_unverified_and_blocked(self):
        meta = get_software_registration_metadata()
        self.assertEqual(meta["staging_dns_status"], "UNVERIFIED")
        self.assertEqual(meta["staging_ssl_status"], "UNVERIFIED")
        self.assertEqual(meta["staging_external_reachability_status"], "UNVERIFIED")
        self.assertEqual(meta["endpoint_routes_status"], "DISABLED")
        self.assertEqual(meta["deployment_readiness_status"], "BLOCKED")
        self.assertTrue(meta["manual_verification_required"])
        self.assertFalse(meta["public_base_url_configured"])


class DGIIEndpointPlanCommandTests(TestCase):
    def test_json_includes_deployment_readiness_blocked(self):
        with captured_stdout() as out:
            call_command("dgii_endpoint_plan", json_flag=True)
        payload = json.loads(out.getvalue())
        self.assertEqual(payload["deployment_readiness_status"], "BLOCKED")
        self.assertTrue(payload["manual_verification_required"])
        self.assertEqual(payload["staging_dns_status"], "UNVERIFIED")
        self.assertEqual(payload["staging_ssl_status"], "UNVERIFIED")
        self.assertEqual(payload["staging_external_reachability_status"], "UNVERIFIED")


class DGIIPublicEndpointStubHardeningTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.views = (
            dgii_recepcion_ecf,
            dgii_aprobacion_comercial_ecf,
            dgii_autenticacion_semilla,
            dgii_autenticacion_validacioncertificado,
        )
        self.expected = disabled_endpoint_payload()

    def _assert_disabled_response(self, response):
        self.assertEqual(response.status_code, 503)
        payload = json.loads(response.content)
        self.assertEqual(payload["status"], self.expected["status"])
        self.assertEqual(payload["compliance_status"], self.expected["compliance_status"])
        self.assertFalse(payload["dgii_submission_allowed"])
        self.assertIsNone(payload["track_id"])
        self.assertIn("disabled", payload["message"].lower())

    def test_all_disabled_routes_return_503_on_get_and_post(self):
        before_invoice = Invoice.objects.count()
        before_doc = Document.objects.count()
        before_ecf = ECFDocument.objects.count()
        xml_body = b'<?xml version="1.0"?><ECF><eNCF>E319000000001</eNCF></ECF>'

        for view in self.views:
            for method in ("get", "post"):
                if method == "get":
                    request = self.factory.get("/fe/stub/")
                else:
                    request = self.factory.post(
                        "/fe/stub/",
                        data=xml_body,
                        content_type="application/xml",
                    )
                self._assert_disabled_response(view(request))

        self.assertEqual(Invoice.objects.count(), before_invoice)
        self.assertEqual(Document.objects.count(), before_doc)
        self.assertEqual(ECFDocument.objects.count(), before_ecf)

    def test_disabled_payload_helper_shape(self):
        payload = disabled_endpoint_payload()
        self.assertEqual(payload["track_id"], None)
        self.assertFalse(payload["dgii_submission_allowed"])


class Phase026ReadinessBlockerTests(TestCase):
    PHASE_026_BLOCKERS = (
        "staging_dns_not_verified",
        "staging_ssl_not_verified",
        "staging_external_reachability_not_verified",
        "staging_environment_not_deployed",
        "public_endpoint_routes_disabled",
        "disabled_stub_only",
        "production_signing_not_approved",
        "endpoint_security_owner_not_assigned",
    )

    def test_readiness_includes_phase_026_blockers(self):
        with captured_stdout() as out:
            call_command("dgii_readiness_report", json_flag=True)
        report = json.loads(out.getvalue())
        self.assertEqual(report["overall_status"], "BLOCKED")
        self.assertEqual(report["compliance_status"], "NOT_DGII_COMPLIANT")
        self.assertFalse(report["dgii_submission_allowed"])
        self.assertFalse(report["dgii_call_made"])
        self.assertIsNone(report["track_id"])
        for blocker in self.PHASE_026_BLOCKERS:
            self.assertIn(blocker, report["blockers"])

    def test_staging_checklist_doc_exists(self):
        repo_root = Path(__file__).resolve().parents[1]
        self.assertTrue(
            (repo_root / "docs/deployment/DGII_STAGING_DNS_SSL_CHECKLIST.md").is_file()
        )
