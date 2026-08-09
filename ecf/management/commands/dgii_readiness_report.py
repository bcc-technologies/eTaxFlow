import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from ecf.dgii.inventory_status import source_inventory_status
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
    ]
    endpoint_checks = {
        "url_recepcion": _check(
            "url_recepcion",
            "BLOCKED",
            "Blank by default; no live reception endpoint is configured.",
            blocker=True,
        ),
        "url_aprobacion_comercial": _check(
            "url_aprobacion_comercial",
            "BLOCKED",
            "Blank by default; no live commercial approval endpoint is configured.",
            blocker=True,
        ),
        "url_autenticacion": _check(
            "url_autenticacion",
            "BLOCKED",
            "Blank by default; no live authentication endpoint is configured.",
            blocker=True,
        ),
    }
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
        "software": {
            "name": settings.DGII_SOFTWARE_NAME,
            "version": settings.DGII_SOFTWARE_VERSION,
            "type": settings.DGII_SOFTWARE_TYPE,
            "environment": settings.DGII_ENVIRONMENT,
            "status": "READY",
        },
        "endpoints": endpoint_checks,
        "checks": checks,
        "blockers": blockers,
        "remaining_dgii_documentation_missing": missing_docs,
        "source_inventory": inventory,
        "manual_decisions_required": [
            "Confirm OFV enrollment and access owner.",
            "Confirm authorized Alta NCF/eNCF process and ranges.",
            "Choose production certificate custody and approved signer backend.",
            "Collect and review missing DGII/legal/certification source documents.",
            "Approve staging backup, retention, contingency, and incident-response policies.",
        ],
        "not_certification_evidence": True,
        "notes": [
            "Read-only local report; no data mutation or network call occurred.",
            "MOCK service contracts and TEST_ONLY signing do not establish DGII readiness.",
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
