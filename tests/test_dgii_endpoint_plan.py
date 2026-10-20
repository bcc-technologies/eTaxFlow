import json
from pathlib import Path

from django.core.management import call_command
from django.test import RequestFactory, TestCase, override_settings
from django.test.utils import captured_stdout

from ecf.dgii.endpoints import get_software_registration_metadata
from ecf.models import ECFDocument
from ecf.views.dgii_public_endpoints import (
    dgii_aprobacion_comercial_ecf,
    dgii_autenticacion_semilla,
    dgii_autenticacion_validacioncertificado,
    dgii_recepcion_ecf,
)


class DGIISoftwareRegistrationMetadataTests(TestCase):
    def test_defaults_are_blocked_and_not_compliant(self):
        meta = get_software_registration_metadata()
        self.assertEqual(meta["software_type"], "PROPIO")
        self.assertEqual(meta["software_name"], "eTaxFlow")
        self.assertEqual(meta["software_version"], "0.1.0")
        self.assertFalse(meta["endpoints_enabled"])
        self.assertEqual(meta["public_base_url"], "")
        self.assertEqual(meta["recepcion_url"], "")
        self.assertEqual(meta["readiness_status"], "BLOCKED")
        self.assertEqual(meta["compliance_status"], "NOT_DGII_COMPLIANT")
        self.assertFalse(meta["dgii_submission_allowed"])

    @override_settings(
        ETAXFLOW_PUBLIC_BASE_URL="https://etaxflow.bcctechnologies.com.do",
        ETAXFLOW_ENABLE_PUBLIC_DGII_ENDPOINTS=False,
    )
    def test_configured_base_url_composes_exact_portal_urls(self):
        meta = get_software_registration_metadata()
        self.assertEqual(
            meta["recepcion_url"],
            "https://etaxflow.bcctechnologies.com.do/fe/recepcion/api/ecf",
        )
        self.assertEqual(
            meta["aprobacion_comercial_url"],
            "https://etaxflow.bcctechnologies.com.do/fe/aprobacioncomercial/api/ecf",
        )
        self.assertEqual(
            meta["autenticacion_url_template"],
            "https://etaxflow.bcctechnologies.com.do/fe/autenticacion/api/[semilla]validacioncertificado",
        )
        self.assertEqual(meta["readiness_status"], "DESIGN_ONLY")
        self.assertFalse(meta["endpoints_enabled"])


class DGIIEndpointPlanCommandTests(TestCase):
    def test_human_output_runs(self):
        with captured_stdout() as out:
            call_command("dgii_endpoint_plan")
        text = out.getvalue()
        self.assertIn("DESIGN_ONLY", text)
        self.assertIn("NOT_DGII_COMPLIANT", text)
        self.assertIn("BLOCKED", text)

    def test_json_output_is_parseable(self):
        with captured_stdout() as out:
            call_command("dgii_endpoint_plan", json_flag=True)
        payload = json.loads(out.getvalue())
        self.assertEqual(payload["software_type"], "PROPIO")
        self.assertEqual(payload["software_name"], "eTaxFlow")
        self.assertTrue(payload["software_version"])
        self.assertFalse(payload["endpoints_enabled"])
        self.assertEqual(payload["compliance_status"], "NOT_DGII_COMPLIANT")
        self.assertFalse(payload["dgii_submission_allowed"])
        self.assertEqual(payload["deployment_readiness_status"], "BLOCKED")
        self.assertTrue(payload["manual_verification_required"])


class DGIIPublicEndpointStubTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.views = (
            ("/fe/recepcion/api/ecf", dgii_recepcion_ecf),
            ("/fe/aprobacioncomercial/api/ecf", dgii_aprobacion_comercial_ecf),
            ("/fe/autenticacion/api/semilla", dgii_autenticacion_semilla),
            (
                "/fe/autenticacion/api/validacioncertificado",
                dgii_autenticacion_validacioncertificado,
            ),
        )

    def test_disabled_stubs_return_503_not_compliant(self):
        before_ecf = ECFDocument.objects.count()
        for _route, view in self.views:
            request = self.factory.post(
                _route,
                data=b"<ECF/>",
                content_type="application/xml",
            )
            response = view(request)
            self.assertEqual(response.status_code, 503)
            payload = json.loads(response.content)
            self.assertEqual(payload["status"], "DISABLED")
            self.assertEqual(payload["compliance_status"], "NOT_DGII_COMPLIANT")
            self.assertFalse(payload["dgii_submission_allowed"])
            self.assertIsNone(payload["track_id"])
            self.assertIn("message", payload)
        self.assertEqual(ECFDocument.objects.count(), before_ecf)

    @override_settings(ETAXFLOW_ENABLE_PUBLIC_DGII_ENDPOINTS=True)
    def test_enabled_flag_still_not_implemented(self):
        request = self.factory.get("/fe/recepcion/api/ecf")
        response = dgii_recepcion_ecf(request)
        self.assertEqual(response.status_code, 503)
        payload = json.loads(response.content)
        self.assertEqual(payload["status"], "NOT_IMPLEMENTED")
        self.assertEqual(payload["compliance_status"], "NOT_DGII_COMPLIANT")


class DGIIRreadinessEndpointBlockerTests(TestCase):
    PHASE_025_BLOCKERS = (
        "public_base_url_not_configured",
        "public_dgii_endpoints_disabled",
        "endpoint_ssl_not_verified",
        "endpoint_internet_access_not_verified",
        "endpoint_routes_not_implemented_or_not_verified",
        "recepcion_url_blocked",
        "aprobacion_comercial_url_blocked",
        "autenticacion_url_blocked",
    )

    def test_readiness_includes_phase_025_endpoint_blockers(self):
        with captured_stdout() as out:
            call_command("dgii_readiness_report", json_flag=True)
        report = json.loads(out.getvalue())
        self.assertEqual(report["overall_status"], "BLOCKED")
        self.assertEqual(report["compliance_status"], "NOT_DGII_COMPLIANT")
        self.assertFalse(report["dgii_submission_allowed"])
        self.assertFalse(report["dgii_call_made"])
        self.assertIsNone(report["track_id"])
        for blocker in self.PHASE_025_BLOCKERS:
            self.assertIn(blocker, report["blockers"])
        self.assertIn("endpoint_plan", report)
        self.assertEqual(report["endpoint_plan"]["software_type"], "PROPIO")

    def test_endpoint_design_doc_exists(self):
        repo_root = Path(__file__).resolve().parents[1]
        self.assertTrue(
            (repo_root / "docs/dgii/endpoints/PRE_CERTIFICATION_ENDPOINT_DESIGN.md").is_file()
        )
