import json
from pathlib import Path
from unittest.mock import patch

from django.core.management import call_command
from django.test import RequestFactory, TestCase
from django.test.utils import captured_stdout

from documents.models import Document
from ecf.dgii.certification_package_lab import (
    PACKAGE_BLOCKED,
    PACKAGE_SCOPE,
    build_certification_package_draft,
    build_certification_package_markdown,
    build_endpoint_url_draft,
    get_software_package_defaults,
    resolve_output_dir,
    write_certification_package,
)
from ecf.dgii.endpoints import get_software_registration_metadata
from ecf.dgii.inbound_lab import analyze_inbound_xml, build_lab_report
from ecf.dgii.receiver import get_receiver_contract_metadata
from ecf.models import ECFDocument, InboundXMLLabAuditEvent, InboundXMLLabRecord
from ecf.views.dgii_public_endpoints import dgii_recepcion_ecf
from invoicing.models import Invoice

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures/dgii/inbound_lab"
REPO_ROOT = Path(__file__).resolve().parents[1]


class CertificationPackageModuleTests(TestCase):
    def test_module_imports_and_defaults(self):
        import ecf.dgii.certification_package_lab as mod

        self.assertTrue(hasattr(mod, "get_software_package_defaults"))
        self.assertTrue(hasattr(mod, "build_endpoint_url_draft"))
        self.assertTrue(hasattr(mod, "build_certification_package_draft"))
        defaults = get_software_package_defaults()
        self.assertEqual(defaults["software_type"], "PROPIO")
        self.assertEqual(defaults["software_name"], "eTaxFlow")
        self.assertFalse(defaults["submission_allowed"])
        self.assertFalse(defaults["dgii_submission_allowed"])
        self.assertFalse(defaults["certification_evidence"])
        self.assertFalse(defaults["public_endpoints_enabled"])
        self.assertFalse(defaults["production_staging_ready"])
        self.assertFalse(defaults["production_security_ready"])
        self.assertFalse(defaults["production_signature_ready"])
        self.assertIsNone(defaults["track_id"])
        self.assertFalse(defaults["dgii_call_made"])
        self.assertEqual(defaults["package_scope"], PACKAGE_SCOPE)

    def test_endpoint_url_draft_blank_and_paths(self):
        draft = build_endpoint_url_draft("")
        self.assertFalse(draft["public_base_url_configured"])
        self.assertEqual(draft["recepcion_url"], "")
        self.assertEqual(draft["recepcion_path"], "/fe/recepcion/api/ecf")
        self.assertEqual(
            draft["aprobacion_comercial_path"], "/fe/aprobacioncomercial/api/ecf"
        )
        self.assertEqual(
            draft["autenticacion_semilla_path"], "/fe/autenticacion/api/semilla"
        )
        self.assertEqual(
            draft["autenticacion_validacion_path"],
            "/fe/autenticacion/api/validacioncertificado",
        )
        with_base = build_endpoint_url_draft("https://example.test")
        self.assertTrue(with_base["recepcion_url"].endswith("/fe/recepcion/api/ecf"))
        self.assertTrue(
            with_base["aprobacion_comercial_url"].endswith(
                "/fe/aprobacioncomercial/api/ecf"
            )
        )
        self.assertTrue(
            with_base["autenticacion_semilla_url"].endswith(
                "/fe/autenticacion/api/semilla"
            )
        )
        self.assertTrue(
            with_base["autenticacion_validacion_url"].endswith(
                "/fe/autenticacion/api/validacioncertificado"
            )
        )

    def test_package_draft_boundaries_and_markdown(self):
        package = build_certification_package_draft()
        self.assertEqual(package["package_status"], PACKAGE_BLOCKED)
        self.assertTrue(package["requires_human_review"])
        self.assertTrue(package["blockers"])
        self.assertTrue(package["human_decisions_required"])
        self.assertEqual(package["compliance_status"], "NOT_DGII_COMPLIANT")
        self.assertFalse(package["submission_allowed"])
        self.assertFalse(package["portal_submission_allowed"])
        md = build_certification_package_markdown(package)
        self.assertIn("DRAFT_ONLY", md)
        self.assertIn("NOT_DGII_COMPLIANT", md)

    def test_write_package_and_path_traversal(self):
        report = write_certification_package()
        output = Path(report["output_dir"])
        self.assertTrue((output / "certification_package_draft.json").is_file())
        self.assertTrue((output / "certification_package_draft.md").is_file())
        self.assertTrue((output / "manifest.json").is_file())
        with self.assertRaises(ValueError):
            resolve_output_dir("/tmp/evil_package")
        with self.assertRaises(ValueError):
            resolve_output_dir(
                "runtime/dgii_certification_package_drafts/../../etc/passwd"
            )


class CertificationPackageCommandTests(TestCase):
    def test_command_runs_json_summary_export(self):
        with captured_stdout() as out:
            call_command("dgii_certification_package_lab")
        text = out.getvalue()
        self.assertIn("NOT_DGII_COMPLIANT", text)
        self.assertIn("DRAFT_ONLY", text)
        self.assertIn("PACKAGE_BLOCKED", text)
        self.assertIn("submission_allowed=false", text)
        self.assertIn("production_signature_ready=false", text)

        with captured_stdout() as out:
            call_command("dgii_certification_package_lab", json_flag=True)
        report = json.loads(out.getvalue())
        self.assertEqual(report["package_status"], PACKAGE_BLOCKED)
        self.assertFalse(report["dgii_submission_allowed"])

        with captured_stdout() as out:
            call_command("dgii_certification_package_lab", summary_only=True)
        text = out.getvalue()
        self.assertIn("blocker_count", text)
        self.assertNotIn("Human decisions required:", text)

        with captured_stdout() as out:
            call_command(
                "dgii_certification_package_lab", export_package=True, json_flag=True
            )
        report = json.loads(out.getvalue())
        self.assertTrue(report.get("files_exported"))
        self.assertTrue(Path(report["output_dir"]).is_dir())

    def test_command_no_db_writes_or_track_id(self):
        before = {
            "records": InboundXMLLabRecord.objects.count(),
            "audit": InboundXMLLabAuditEvent.objects.count(),
            "invoice": Invoice.objects.count(),
            "document": Document.objects.count(),
            "ecf": ECFDocument.objects.count(),
        }
        with captured_stdout() as out:
            call_command("dgii_certification_package_lab", json_flag=True)
        report = json.loads(out.getvalue())
        self.assertIsNone(report["track_id"])
        self.assertFalse(report["dgii_call_made"])
        self.assertFalse(report["public_endpoints_enabled"])
        self.assertEqual(InboundXMLLabRecord.objects.count(), before["records"])
        self.assertEqual(InboundXMLLabAuditEvent.objects.count(), before["audit"])
        self.assertEqual(Invoice.objects.count(), before["invoice"])
        self.assertEqual(Document.objects.count(), before["document"])
        self.assertEqual(ECFDocument.objects.count(), before["ecf"])


class CertificationPackageBoundaryTests(TestCase):
    def test_public_disabled_routes_still_503(self):
        response = dgii_recepcion_ecf(RequestFactory().get("/fe/recepcion/api/ecf"))
        self.assertEqual(response.status_code, 503)

    @patch("ecf.dgii.receiver.classify_inbound_xml")
    def test_public_disabled_post_does_not_parse_or_write(self, mock_classify):
        before = InboundXMLLabRecord.objects.count()
        request = RequestFactory().post(
            "/fe/recepcion/api/ecf",
            data=b'<?xml version="1.0"?><ECF/>',
            content_type="application/xml",
        )
        response = dgii_recepcion_ecf(request)
        self.assertEqual(response.status_code, 503)
        mock_classify.assert_not_called()
        self.assertEqual(InboundXMLLabRecord.objects.count(), before)


class CertificationPackageContractTests(TestCase):
    def test_endpoint_and_receiver_contract(self):
        meta = get_software_registration_metadata()
        self.assertTrue(meta["certification_package_lab_available"])
        self.assertEqual(
            meta["certification_package_command"], "dgii_certification_package_lab"
        )
        self.assertEqual(meta["certification_package_status"], PACKAGE_BLOCKED)
        self.assertFalse(meta["portal_submission_allowed"])
        self.assertFalse(meta["public_base_url_externally_verified"])

        receiver = get_receiver_contract_metadata()
        self.assertTrue(receiver["certification_package_lab_available"])
        self.assertFalse(receiver["portal_submission_allowed"])
        self.assertFalse(receiver["portal_submission_ready"])
        self.assertTrue(receiver["package_requires_human_review"])
        self.assertFalse(receiver["certification_evidence"])


class CertificationPackageCrossLabTests(TestCase):
    def test_existing_labs_do_not_run_package_by_default(self):
        xml_bytes = (FIXTURE_DIR / "synthetic_ecf_unsigned.xml").read_bytes()
        self.assertEqual(
            build_lab_report([analyze_inbound_xml(xml_bytes)])[
                "certification_package_status"
            ],
            "NOT_RUN_BY_DEFAULT",
        )
        with captured_stdout() as out:
            call_command("dgii_inbound_xml_lab", json_flag=True)
            call_command("dgii_staging_evidence_lab", json_flag=True)
            call_command("dgii_inbound_reporting_lab", json_flag=True)
        self.assertNotIn("certification_package_draft.json", out.getvalue())


class CertificationPackageReadinessTests(TestCase):
    PHASE_037_BLOCKERS = (
        "certification_package_draft_only",
        "portal_submission_not_allowed",
        "portal_submission_ready_false",
        "public_base_url_not_verified",
        "endpoint_external_evidence_missing",
        "security_owner_review_missing",
        "tax_compliance_owner_review_missing",
        "phase_024_gate_not_signed_off",
        "production_signing_architecture_not_approved",
        "production_signature_verification_not_implemented",
        "certification_portal_credentials_not_confirmed",
        "certification_package_not_human_approved",
    )

    def test_readiness_includes_phase_037_blockers(self):
        with captured_stdout() as out:
            call_command("dgii_readiness_report", json_flag=True)
        report = json.loads(out.getvalue())
        self.assertEqual(report["overall_status"], "BLOCKED")
        self.assertEqual(report["compliance_status"], "NOT_DGII_COMPLIANT")
        self.assertFalse(report["dgii_submission_allowed"])
        self.assertFalse(report["portal_submission_allowed"])
        for blocker in self.PHASE_037_BLOCKERS:
            self.assertIn(blocker, report["blockers"])

    def test_doc_exists(self):
        self.assertTrue(
            (
                REPO_ROOT
                / "docs/dgii/certification/CERTIFICATION_PORTAL_SUBMISSION_PACKAGE_DRAFT.md"
            ).is_file()
        )


class CertificationPackagePrivateKeySafetyTests(TestCase):
    def test_no_private_key_files_added_by_phase(self):
        forbidden = (".p12", ".pfx", ".key", "privkey", "private.pem", "key.pem")
        for path in (
            REPO_ROOT / "ecf/dgii/certification_package_lab.py",
            REPO_ROOT / "ecf/management/commands/dgii_certification_package_lab.py",
            REPO_ROOT
            / "docs/dgii/certification/CERTIFICATION_PORTAL_SUBMISSION_PACKAGE_DRAFT.md",
        ):
            self.assertTrue(path.is_file())
            lower = path.name.lower()
            self.assertFalse(any(token in lower for token in forbidden))
