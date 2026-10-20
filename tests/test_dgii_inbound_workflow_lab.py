import json
from pathlib import Path
from unittest.mock import patch

from django.core.management import call_command
from django.test import RequestFactory, TestCase
from django.test.utils import captured_stdout

from documents.models import Document
from ecf.dgii.inbound_lab import analyze_inbound_xml, build_lab_report
from ecf.dgii.inbound_persistence_lab import persist_lab_record
from ecf.dgii.inbound_workflow_lab import (
    LAB_MODE,
    LAB_ROUTE_ACECF_REVIEW,
    LAB_ROUTE_ARECF_REVIEW,
    LAB_ROUTE_DUPLICATE_REVIEW,
    LAB_ROUTE_ECF_REVIEW,
    LAB_ROUTE_INVALID_XML_REVIEW,
    LAB_ROUTE_SCHEMA_ISSUE_REVIEW,
    LAB_ROUTE_SIGNATURE_ISSUE_REVIEW,
    LAB_ROUTE_UNSUPPORTED_ROOT_REVIEW,
    LAB_ROUTING_DRY_RUN,
    LAB_ROUTED,
    decide_lab_workflow_route,
    route_lab_record,
    route_lab_records,
)
from ecf.dgii.receiver import get_receiver_contract_metadata
from ecf.models import ECFDocument, InboundXMLLabRecord, InboundXMLLabWorkflowEvent
from ecf.views.dgii_public_endpoints import dgii_recepcion_ecf
from invoicing.models import Invoice

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures/dgii/inbound_lab"


def _clean_payload(**overrides):
    payload = {
        "record_id": None,
        "filename": "clean.xml",
        "raw_sha256": "b" * 64,
        "document_type": "ECF",
        "classification_status": "SIGNATURE_VERIFICATION_NOT_IMPLEMENTED",
        "root_tag": "ECF",
        "signature_present": True,
        "signature_verification_status": "TEST_ONLY_VALID",
        "local_xsd_valid": True,
        "xsd_compiled": True,
        "is_duplicate": False,
    }
    payload.update(overrides)
    return payload


class InboundXMLLabWorkflowEventModelTests(TestCase):
    def test_model_defaults(self):
        record = InboundXMLLabRecord.objects.create(
            raw_sha256="c" * 64,
            document_type="ECF",
        )
        event = InboundXMLLabWorkflowEvent.objects.create(
            lab_record=record,
            route=LAB_ROUTE_ECF_REVIEW,
            status=LAB_ROUTED,
            reason="test",
        )
        self.assertEqual(event.compliance_status, "NOT_DGII_COMPLIANT")
        self.assertFalse(event.dgii_submission_allowed)
        self.assertFalse(event.certification_evidence)
        self.assertIn(event.track_id, (None, ""))
        self.assertEqual(event.lab_mode, LAB_MODE)


class WorkflowRoutingDecisionTests(TestCase):
    def test_route_invalid_xml(self):
        decision = decide_lab_workflow_route(
            {"classification_status": "INVALID_XML", "signature_verification_status": "PARSE_ERROR"}
        )
        self.assertEqual(decision["route"], LAB_ROUTE_INVALID_XML_REVIEW)

    def test_route_unsupported_root(self):
        decision = decide_lab_workflow_route(
            {
                "classification_status": "UNSUPPORTED_ROOT",
                "document_type": "UNKNOWN",
                "root_tag": "UNKNOWNLABROOT",
            }
        )
        self.assertEqual(decision["route"], LAB_ROUTE_UNSUPPORTED_ROOT_REVIEW)

    def test_route_duplicate(self):
        decision = decide_lab_workflow_route(_clean_payload(is_duplicate=True))
        self.assertEqual(decision["route"], LAB_ROUTE_DUPLICATE_REVIEW)

    def test_route_schema_issue(self):
        decision = decide_lab_workflow_route(_clean_payload(local_xsd_valid=False, xsd_compiled=True))
        self.assertEqual(decision["route"], LAB_ROUTE_SCHEMA_ISSUE_REVIEW)

    def test_route_signature_issue(self):
        decision = decide_lab_workflow_route(
            _clean_payload(signature_present=False, signature_verification_status="MISSING")
        )
        self.assertEqual(decision["route"], LAB_ROUTE_SIGNATURE_ISSUE_REVIEW)

    def test_route_ecf_clean(self):
        decision = decide_lab_workflow_route(_clean_payload(document_type="ECF", root_tag="ECF"))
        self.assertEqual(decision["route"], LAB_ROUTE_ECF_REVIEW)

    def test_route_arecf_clean(self):
        decision = decide_lab_workflow_route(_clean_payload(document_type="ARECF", root_tag="ARECF"))
        self.assertEqual(decision["route"], LAB_ROUTE_ARECF_REVIEW)

    def test_route_acecf_clean(self):
        decision = decide_lab_workflow_route(_clean_payload(document_type="ACECF", root_tag="ACECF"))
        self.assertEqual(decision["route"], LAB_ROUTE_ACECF_REVIEW)


class RouteLabRecordTests(TestCase):
    def test_dry_run_creates_no_workflow_event(self):
        record = InboundXMLLabRecord.objects.create(
            raw_sha256="d" * 64,
            document_type="ECF",
            classification_status="INVALID_XML",
        )
        result = route_lab_record(record, apply=False)
        self.assertEqual(result["status"], LAB_ROUTING_DRY_RUN)
        self.assertFalse(result["applied"])
        self.assertEqual(InboundXMLLabWorkflowEvent.objects.count(), 0)

    def test_apply_creates_workflow_event(self):
        record = InboundXMLLabRecord.objects.create(
            raw_sha256="e" * 64,
            document_type="ECF",
            classification_status="INVALID_XML",
        )
        result = route_lab_record(record, apply=True)
        self.assertEqual(result["status"], LAB_ROUTED)
        self.assertTrue(result["applied"])
        self.assertEqual(InboundXMLLabWorkflowEvent.objects.count(), 1)


class WorkflowLabCommandTests(TestCase):
    def test_dry_run_writes_no_workflow_events(self):
        before = InboundXMLLabWorkflowEvent.objects.count()
        with captured_stdout() as out:
            call_command("dgii_inbound_workflow_lab", path=str(FIXTURE_DIR))
        text = out.getvalue()
        self.assertIn("NOT_DGII_COMPLIANT", text)
        self.assertIn("NON_PRODUCTION_LAB_ONLY", text)
        self.assertEqual(InboundXMLLabWorkflowEvent.objects.count(), before)

    def test_apply_writes_workflow_events_only(self):
        before_invoice = Invoice.objects.count()
        before_doc = Document.objects.count()
        before_ecf = ECFDocument.objects.count()
        with captured_stdout() as out:
            call_command(
                "dgii_inbound_workflow_lab",
                path=str(FIXTURE_DIR),
                apply_lab_workflow=True,
                json_flag=True,
            )
        report = json.loads(out.getvalue())
        self.assertFalse(report["dry_run"])
        self.assertTrue(report["apply_lab_workflow"])
        self.assertFalse(report["certification_evidence"])
        self.assertGreater(report["applied_count"], 0)
        self.assertGreater(InboundXMLLabWorkflowEvent.objects.count(), 0)
        self.assertEqual(Invoice.objects.count(), before_invoice)
        self.assertEqual(Document.objects.count(), before_doc)
        self.assertEqual(ECFDocument.objects.count(), before_ecf)
        self.assertFalse(
            InboundXMLLabWorkflowEvent.objects.exclude(track_id__isnull=True)
            .exclude(track_id="")
            .exists()
        )

    def test_command_from_lab_records(self):
        persist_lab_record(
            (FIXTURE_DIR / "synthetic_ecf_unsigned.xml").read_bytes(),
            filename="synthetic_ecf_unsigned.xml",
        )
        with captured_stdout() as out:
            call_command("dgii_inbound_workflow_lab", from_lab_records=True, json_flag=True)
        report = json.loads(out.getvalue())
        self.assertGreater(report["result_count"], 0)

    def test_command_record_id(self):
        result = persist_lab_record(
            (FIXTURE_DIR / "synthetic_arecf_unsigned.xml").read_bytes(),
            filename="synthetic_arecf_unsigned.xml",
        )
        with captured_stdout() as out:
            call_command(
                "dgii_inbound_workflow_lab",
                record_id=result["record_id"],
                json_flag=True,
            )
        report = json.loads(out.getvalue())
        self.assertEqual(report["result_count"], 1)

    def test_summary_only(self):
        with captured_stdout() as out:
            call_command("dgii_inbound_workflow_lab", path=str(FIXTURE_DIR), summary_only=True)
        text = out.getvalue()
        self.assertIn("result_count:", text)
        self.assertNotIn("route=LAB_ROUTE", text)


class Phase032OtherLabsDoNotRunWorkflowTests(TestCase):
    def test_existing_labs_do_not_run_workflow_by_default(self):
        xml_bytes = (FIXTURE_DIR / "synthetic_ecf_unsigned.xml").read_bytes()
        before = InboundXMLLabWorkflowEvent.objects.count()
        self.assertEqual(build_lab_report([analyze_inbound_xml(xml_bytes)])["workflow_status"], "NOT_RUN_BY_DEFAULT")
        call_command("dgii_inbound_xml_lab", json_flag=True)
        call_command("dgii_inbound_schema_lab", json_flag=True)
        call_command("dgii_inbound_signature_lab", json_flag=True)
        call_command("dgii_inbound_persistence_lab", json_flag=True)
        self.assertEqual(InboundXMLLabWorkflowEvent.objects.count(), before)


class Phase032ReceiverContractTests(TestCase):
    def test_receiver_contract_reports_workflow_lab(self):
        meta = get_receiver_contract_metadata()
        self.assertTrue(meta["non_production_inbound_workflow_lab_available"])
        self.assertFalse(meta["production_workflow_ready"])
        self.assertFalse(meta["public_route_workflow_enabled"])
        self.assertFalse(meta["fiscal_acceptance_workflow_enabled"])
        self.assertEqual(meta["workflow_scope"], "NON_PRODUCTION_LAB_ONLY")
        self.assertEqual(meta["track_id_creation"], "DISABLED")


class Phase032ReadinessBlockerTests(TestCase):
    PHASE_032_BLOCKERS = (
        "inbound_workflow_lab_only",
        "production_inbound_workflow_not_implemented",
        "public_route_workflow_disabled",
        "fiscal_acceptance_workflow_not_implemented",
        "acuse_generation_not_implemented",
        "aprobacion_comercial_generation_not_implemented",
        "workflow_policy_not_approved",
        "inbound_workflow_not_certification_evidence",
    )

    def test_readiness_includes_phase_032_blockers(self):
        with captured_stdout() as out:
            call_command("dgii_readiness_report", json_flag=True)
        report = json.loads(out.getvalue())
        self.assertEqual(report["overall_status"], "BLOCKED")
        self.assertEqual(report["compliance_status"], "NOT_DGII_COMPLIANT")
        self.assertFalse(report["dgii_submission_allowed"])
        for blocker in self.PHASE_032_BLOCKERS:
            self.assertIn(blocker, report["blockers"])

    def test_doc_exists(self):
        repo_root = Path(__file__).resolve().parents[1]
        self.assertTrue(
            (repo_root / "docs/dgii/lab/NON_PRODUCTION_INBOUND_WORKFLOW_ROUTING_LAB.md").is_file()
        )


class Phase032PublicRouteBoundaryTests(TestCase):
    def test_public_disabled_routes_return_503(self):
        response = dgii_recepcion_ecf(RequestFactory().get("/fe/recepcion/api/ecf"))
        self.assertEqual(response.status_code, 503)

    @patch("ecf.dgii.inbound_workflow_lab.route_lab_record")
    @patch("ecf.dgii.receiver.classify_inbound_xml")
    def test_public_post_does_not_route_or_parse(self, mock_classify, mock_route):
        before = InboundXMLLabWorkflowEvent.objects.count()
        request = RequestFactory().post(
            "/fe/recepcion/api/ecf",
            data=b'<?xml version="1.0"?><ECF/>',
            content_type="application/xml",
        )
        response = dgii_recepcion_ecf(request)
        self.assertEqual(response.status_code, 503)
        mock_classify.assert_not_called()
        mock_route.assert_not_called()
        self.assertEqual(InboundXMLLabWorkflowEvent.objects.count(), before)

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


class RouteLabRecordsOrderingTests(TestCase):
    def test_route_lab_records_deterministic(self):
        first = InboundXMLLabRecord.objects.create(raw_sha256="1" * 64, document_type="ECF")
        second = InboundXMLLabRecord.objects.create(raw_sha256="2" * 64, document_type="ARECF")
        results = route_lab_records([second, first], apply=False)
        self.assertEqual([item["record_id"] for item in results], [first.pk, second.pk])
