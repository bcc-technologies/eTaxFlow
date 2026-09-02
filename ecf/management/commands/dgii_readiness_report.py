import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from ecf.dgii.endpoint_readiness import build_endpoint_readiness_checks
from ecf.dgii.endpoints import get_software_registration_metadata
from ecf.dgii.inventory_status import source_inventory_status
from ecf.dgii.inbound_lab_readiness import build_inbound_lab_readiness_checks
from ecf.dgii.inbound_persistence_lab_readiness import build_inbound_persistence_lab_readiness_checks
from ecf.dgii.inbound_schema_lab_readiness import build_inbound_schema_lab_readiness_checks
from ecf.dgii.inbound_signature_lab_readiness import build_inbound_signature_lab_readiness_checks
from ecf.dgii.inbound_workflow_lab_readiness import build_inbound_workflow_lab_readiness_checks
from ecf.dgii.inbound_audit_retention_lab_readiness import (
    build_inbound_audit_retention_lab_readiness_checks,
)
from ecf.dgii.inbound_security_policy_lab_readiness import (
    build_inbound_security_policy_lab_readiness_checks,
)
from ecf.dgii.inbound_reporting_lab_readiness import (
    build_inbound_reporting_lab_readiness_checks,
)
from ecf.dgii.staging_evidence_lab_readiness import (
    build_staging_evidence_lab_readiness_checks,
)
from ecf.dgii.certification_package_lab_readiness import (
    build_certification_package_lab_readiness_checks,
)
from ecf.dgii.final_go_no_go_lab_readiness import (
    build_final_go_no_go_lab_readiness_checks,
)
from ecf.dgii.final_inbound_audit_lab_readiness import (
    build_final_inbound_audit_lab_readiness_checks,
)
from ecf.dgii.receiver import get_receiver_contract_metadata
from ecf.dgii.receiver_readiness import build_receiver_readiness_checks
from ecf.models import ECFDocument
from organizations.models import Organization


def _check(name: str, status: str, detail: str, *, blocker: bool = False) -> dict:
    return {
        "name": name,
        "status": status,
        "detail": detail,
        "blocker": blocker,
    }


def build_readiness_report() -> dict:
    inventory = source_inventory_status()
    endpoint_meta = get_software_registration_metadata()
    receiver_meta = get_receiver_contract_metadata()
    endpoint_checks, endpoint_blocker_checks = build_endpoint_readiness_checks()
    receiver_blocker_checks = build_receiver_readiness_checks()
    inbound_lab_blocker_checks = build_inbound_lab_readiness_checks()
    inbound_schema_lab_blocker_checks = build_inbound_schema_lab_readiness_checks()
    inbound_signature_lab_blocker_checks = build_inbound_signature_lab_readiness_checks()
    inbound_persistence_lab_blocker_checks = build_inbound_persistence_lab_readiness_checks()
    inbound_workflow_lab_blocker_checks = build_inbound_workflow_lab_readiness_checks()
    inbound_audit_retention_lab_blocker_checks = build_inbound_audit_retention_lab_readiness_checks()
    inbound_security_policy_lab_blocker_checks = build_inbound_security_policy_lab_readiness_checks()
    inbound_reporting_lab_blocker_checks = build_inbound_reporting_lab_readiness_checks()
    staging_evidence_lab_blocker_checks = build_staging_evidence_lab_readiness_checks()
    certification_package_lab_blocker_checks = build_certification_package_lab_readiness_checks()
    final_go_no_go_lab_blocker_checks = build_final_go_no_go_lab_readiness_checks()
    final_inbound_audit_lab_blocker_checks = build_final_inbound_audit_lab_readiness_checks()
    configured_rnc_count = Organization.objects.exclude(rnc="").count()
    default_issuer_count = Organization.objects.filter(is_default_issuer=True).count()
    xsd_present = Path("docs/dgii/sources/e-CF_31_v1.0.xsd").is_file()
    checks = [
        _check(
            "rnc_readiness",
            "PARTIAL" if configured_rnc_count else "BLOCKED",
            (
                f"{configured_rnc_count} organization RNC values are configured; "
                f"{default_issuer_count} default issuer(s). Values are not DGII-verified."
            ),
            blocker=not bool(configured_rnc_count),
        ),
        _check(
            "ofv_readiness_manual_checkpoint",
            "MANUAL_REQUIRED",
            "Confirm OFV enrollment and operator access manually with the responsible human owner.",
            blocker=True,
        ),
        _check(
            "alta_ncf_manual_checkpoint",
            "MANUAL_REQUIRED",
            "Confirm authorized NCF/eNCF ranges and Alta NCF steps manually; local demo ranges are not authorization.",
            blocker=True,
        ),
        _check(
            "certificate_readiness",
            "BLOCKED",
            "No production certificate/key custody is configured; production signing is intentionally unavailable.",
            blocker=True,
        ),
        _check(
            "signing_readiness",
            "BLOCKED",
            "Real signing is disabled. Only a test-only sandbox and non-signing placeholder exist.",
            blocker=True,
        ),
        _check(
            "xml_validation_readiness",
            "PARTIAL" if xsd_present else "BLOCKED",
            "Local XSD validation exists, but the local source requires an experimental stub and is not certification evidence.",
            blocker=not xsd_present,
        ),
        _check(
            "printed_representation_readiness",
            "PARTIAL",
            "A local NON_PRODUCTION_DRAFT PDF generator exists; DGII-approved representation and QR/security source values remain unverified.",
        ),
        _check(
            "contingency_readiness",
            "NOT_IMPLEMENTED",
            "Contingency emission, regularization, and reconciliation workflow are not implemented.",
            blocker=True,
        ),
        _check(
            "logs_audit_retention",
            "PARTIAL",
            "AuditEvent records exist, but operational retention, export, and review policy is not configured.",
        ),
        _check(
            "backups",
            "NOT_IMPLEMENTED",
            "Application backup, restore testing, and key-custody recovery procedures are not implemented here.",
            blocker=True,
        ),
        _check(
            "secrets_handling",
            "PARTIAL",
            "Signing/DGII defaults are disabled and blank; deployment secret-manager integration is still required.",
            blocker=True,
        ),
        _check(
            "security_blockers",
            "BLOCKED",
            "Live DGII transport, production signing, certificate custody, and authorization controls are unavailable.",
            blocker=True,
        ),
        # Phase 024 — source intake and human authorization gate blockers
        _check(
            "official_source_inventory_reviewed",
            "MANUAL_REQUIRED",
            "Phase 024 inventory collected locally; human review of DGII_ECF_DOCUMENT_INVENTORY and authorization gate is not confirmed.",
            blocker=True,
        ),
        _check(
            "usuario_administrador_ecf_not_confirmed",
            "MANUAL_REQUIRED",
            "Usuario Administrador e-CF must be assigned before DGII authorization request; no owner recorded in repo.",
            blocker=True,
        ),
        _check(
            "representative_certificate_owner_not_confirmed",
            "MANUAL_REQUIRED",
            "Representative linked to RNC and certificate owner are not confirmed.",
            blocker=True,
        ),
        _check(
            "production_signing_architecture_not_approved",
            "BLOCKED",
            "Production XMLDSig architecture and key custody are not approved; only test sandbox and placeholder exist.",
            blocker=True,
        ),
        _check(
            "official_encf_authorization_ranges_not_confirmed",
            "MANUAL_REQUIRED",
            "Authorized Alta NCF/eNCF ranges are not confirmed; local demo/XSD-facet sequences are non-authorized.",
            blocker=True,
        ),
        _check(
            "public_urls_not_deployed",
            endpoint_meta["url_status"],
            (
                "URL Recepción, URL Aprobación Comercial, and URL Autenticación are not "
                "deployed or verified for DGII portal submission."
            ),
            blocker=True,
        ),
        _check(
            "acuse_aprobacion_services_not_live",
            "NOT_IMPLEMENTED",
            "Signed Acuse de Recibo (ARECF) and Aprobación Comercial (ACECF) receiver services are not live.",
            blocker=True,
        ),
        _check(
            "contingency_process_not_approved",
            "NOT_IMPLEMENTED",
            "Contingency process is not approved or implemented per Instructivo Contingencia FE.",
            blocker=True,
        ),
        *endpoint_blocker_checks,
        *receiver_blocker_checks,
        *inbound_lab_blocker_checks,
        *inbound_schema_lab_blocker_checks,
        *inbound_signature_lab_blocker_checks,
        *inbound_persistence_lab_blocker_checks,
        *inbound_workflow_lab_blocker_checks,
        *inbound_audit_retention_lab_blocker_checks,
        *inbound_security_policy_lab_blocker_checks,
        *inbound_reporting_lab_blocker_checks,
        *staging_evidence_lab_blocker_checks,
        *certification_package_lab_blocker_checks,
        *final_go_no_go_lab_blocker_checks,
        *final_inbound_audit_lab_blocker_checks,
    ]
    blockers = [item["name"] for item in checks if item["blocker"]]
    blockers.extend(name for name, item in endpoint_checks.items() if item["blocker"])
    missing_docs = [
        {"filename": item["filename"], "label": item["label"]}
        for item in inventory["missing"]
    ]
    return {
        "report_type": "DGII_PRE_CERTIFICATION_READINESS",
        "overall_status": "BLOCKED" if blockers else "PARTIAL",
        "compliance_status": "NOT_DGII_COMPLIANT",
        "dgii_submission_allowed": False,
        "dgii_call_made": False,
        "track_id": None,
        "production_signature_ready": False,
        "production_signature_verification_ready": False,
        "production_security_ready": False,
        "production_staging_ready": False,
        "portal_submission_allowed": False,
        "endpoint_activation_allowed": False,
        "final_decision": "FINAL_DECISION_BLOCKED",
        "software": {
            "name": endpoint_meta["software_name"],
            "version": endpoint_meta["software_version"],
            "type": endpoint_meta["software_type"],
            "environment": settings.DGII_ENVIRONMENT,
            "status": endpoint_meta["readiness_status"],
            "public_base_url": endpoint_meta["public_base_url"],
            "endpoints_enabled": endpoint_meta["endpoints_enabled"],
        },
        "endpoint_plan": endpoint_meta,
        "receiver_contract": receiver_meta,
        "endpoints": endpoint_checks,
        "checks": checks,
        "blockers": blockers,
        "remaining_dgii_documentation_missing": missing_docs,
        "source_inventory": inventory,
        "manual_decisions_required": [
            "Choose internal own software vs certified FE provider route (Phase 024 gate).",
            "Assign Usuario Administrador e-CF before any DGII authorization request.",
            "Confirm OFV enrollment and access owner.",
            "Confirm authorized Alta NCF/eNCF process and ranges.",
            "Confirm representative linked to RNC and certificate owner.",
            "Choose production certificate custody and approved signer backend.",
            "Review Phase 024 official source inventory and authorization gate.",
            "Collect and review missing DGII/legal source documents (Norma/Ley/Decreto).",
            "Approve staging backup, retention, contingency, and incident-response policies.",
            "Approve and deploy public URLs (Recepción, Aprobación Comercial, Autenticación) when ready.",
        ],
        "not_certification_evidence": True,
        "notes": [
            "Read-only local report; no data mutation or network call occurred.",
            "MOCK service contracts and TEST_ONLY signing do not establish DGII readiness.",
            "Phase 024 source intake does not authorize live DGII calls or compliance.",
            "Phase 025 endpoint plan is DESIGN_ONLY; do not submit portal URLs until deployed.",
            "Phase 026 staging DNS/SSL checklist is manual only; no deployment performed.",
            "Phase 027 receiver contract is internal design only; no live receiver processing.",
            "Phase 028 inbound XML lab uses NON_OFFICIAL_SYNTHETIC_SAMPLE fixtures only; not certification evidence.",
            "Phase 029 local inbound XSD validation is LOCAL_OFFLINE_ONLY; a local pass is not DGII acceptance.",
            "Phase 030 inbound signature lab is LOCAL_OFFLINE_TEST_ONLY; presence is not validity.",
            "Phase 031 inbound persistence lab writes InboundXMLLabRecord only; not fiscal documents.",
            "Phase 032 inbound workflow lab routes lab records only; not fiscal acceptance.",
            "Phase 033 inbound audit/retention lab is metadata-only; not legal retention or DGII audit.",
            "Phase 034 inbound security policy lab is LAB_ONLY; SECURITY_POLICY_BLOCKED; not production approval.",
            "Phase 039 final inbound audit report is FINAL_AUDIT_LAB_ONLY; not certification evidence.",
            f"Existing ECFDocument rows: {ECFDocument.objects.count()} (not approval evidence).",
        ],
    }


class Command(BaseCommand):
    help = (
        "Report local DGII pre-certification readiness and blockers. "
        "Read-only; no DGII call or compliance claim."
    )

    def add_arguments(self, parser):
        parser.add_argument("--json", action="store_true", dest="json_flag")

    def handle(self, *args, **options):
        report = build_readiness_report()
        if options.get("json_flag"):
            self.stdout.write(json.dumps(report, indent=2, sort_keys=True, default=str))
            return
        self.stdout.write("DGII pre-certification readiness report")
        self.stdout.write("=" * 60)
        self.stdout.write(f"overall_status: {report['overall_status']}")
        self.stdout.write(f"compliance_status: {report['compliance_status']}")
        self.stdout.write(f"dgii_submission_allowed: {report['dgii_submission_allowed']}")
        self.stdout.write("software:")
        for key, value in report["software"].items():
            self.stdout.write(f"  {key}: {value}")
        self.stdout.write("checks:")
        for item in report["checks"]:
            self.stdout.write(f"  - [{item['status']}] {item['name']}: {item['detail']}")
        self.stdout.write("blockers:")
        for blocker in report["blockers"]:
            self.stdout.write(f"  - {blocker}")
        self.stdout.write("remaining_dgii_documentation_missing:")
        for item in report["remaining_dgii_documentation_missing"]:
            self.stdout.write(f"  - {item['filename']}: {item['label']}")
        self.stdout.write("No DGII call. No submission. NOT_DGII_COMPLIANT.")
