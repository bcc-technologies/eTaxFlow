import json
import sys
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from ecf.dgii.inbound_lab import DEFAULT_FIXTURE_DIR, SYNTHETIC_SAMPLE_MARKER
from ecf.dgii.inbound_schema_lab import (
    SCHEMA_VALIDATION_SCOPE,
    analyze_path_with_local_xsd,
    build_schema_lab_report,
)


class Command(BaseCommand):
    help = (
        "Validate synthetic inbound XML fixtures against local XSDs (offline). "
        "No DGII calls, no database mutation, no TrackId, not certification evidence."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--path",
            default=str(DEFAULT_FIXTURE_DIR),
            help="Fixture file or directory (default: tests/fixtures/dgii/inbound_lab/)",
        )
        parser.add_argument("--json", action="store_true", dest="json_flag")
        parser.add_argument(
            "--fail-on-invalid",
            action="store_true",
            dest="fail_on_invalid",
            help="Exit with code 1 if any fixture is not locally XSD-valid.",
        )
        parser.add_argument(
            "--summary-only",
            action="store_true",
            dest="summary_only",
            help="Print summary counts without per-file details (ignored with --json).",
        )

    def handle(self, *args, **options):
        target = Path(options["path"])
        if not target.exists():
            raise CommandError(f"Path not found: {target}")

        try:
            results = analyze_path_with_local_xsd(target)
        except FileNotFoundError as exc:
            raise CommandError(str(exc)) from exc

        report = build_schema_lab_report(results)

        if options.get("json_flag"):
            self.stdout.write(json.dumps(report, indent=2, sort_keys=True))
        else:
            self.stdout.write(
                "DGII inbound schema lab (LOCAL_OFFLINE_ONLY — NOT_DGII_COMPLIANT)"
            )
            self.stdout.write("=" * 60)
            self.stdout.write("NOT_DGII_COMPLIANT")
            self.stdout.write(SCHEMA_VALIDATION_SCOPE)
            self.stdout.write(SYNTHETIC_SAMPLE_MARKER)
            self.stdout.write("not_certification_evidence=true")
            self.stdout.write(f"lab_mode: {report['lab_mode']}")
            self.stdout.write(f"schema_validation_scope: {report['schema_validation_scope']}")
            self.stdout.write(f"compliance_status: {report['compliance_status']}")
            self.stdout.write(f"dgii_submission_allowed: {report['dgii_submission_allowed']}")
            self.stdout.write(f"not_certification_evidence: {report['not_certification_evidence']}")
            self.stdout.write(f"fixture_count: {report['fixture_count']}")
            self.stdout.write(f"local_xsd_invalid_count: {report['local_xsd_invalid_count']}")
            self.stdout.write(f"xsd_mapping: {report['xsd_mapping']}")
            self.stdout.write(
                f"signature_verification_status: {report['signature_verification_status']}"
            )
            self.stdout.write(f"persistence_lab_available: {report['persistence_lab_available']}")
            self.stdout.write(f"persistence_command: {report['persistence_command']}")
            self.stdout.write(f"persistence_status: {report['persistence_status']}")
            self.stdout.write(f"workflow_lab_available: {report['workflow_lab_available']}")
            self.stdout.write(f"workflow_command: {report['workflow_command']}")
            self.stdout.write(f"workflow_status: {report['workflow_status']}")
            self.stdout.write(f"audit_retention_lab_available: {report['audit_retention_lab_available']}")
            self.stdout.write(f"audit_retention_command: {report['audit_retention_command']}")
            self.stdout.write(f"audit_retention_status: {report['audit_retention_status']}")
            self.stdout.write(f"security_policy_lab_available: {report['security_policy_lab_available']}")
            self.stdout.write(f"security_policy_command: {report['security_policy_command']}")
            self.stdout.write(f"security_policy_status: {report['security_policy_status']}")
            self.stdout.write(f"reporting_lab_available: {report['reporting_lab_available']}")
            self.stdout.write(f"reporting_command: {report['reporting_command']}")
            self.stdout.write(f"reporting_status: {report['reporting_status']}")
            self.stdout.write(f"staging_evidence_lab_available: {report['staging_evidence_lab_available']}")
            self.stdout.write(f"staging_evidence_command: {report['staging_evidence_command']}")
            self.stdout.write(f"staging_evidence_status: {report['staging_evidence_status']}")
            self.stdout.write(f"certification_package_lab_available: {report['certification_package_lab_available']}")
            self.stdout.write(f"certification_package_command: {report['certification_package_command']}")
            self.stdout.write(f"certification_package_status: {report['certification_package_status']}")
            self.stdout.write(f"final_go_no_go_lab_available: {report['final_go_no_go_lab_available']}")
            self.stdout.write(f"final_go_no_go_command: {report['final_go_no_go_command']}")
            self.stdout.write(f"final_go_no_go_status: {report['final_go_no_go_status']}")
            self.stdout.write(
                f"final_inbound_audit_lab_available: {report.get('final_inbound_audit_lab_available', True)}"
            )
            self.stdout.write("final_inbound_audit_command: dgii_final_inbound_audit_lab")
            self.stdout.write(
                f"final_inbound_audit_status: {report.get('final_inbound_audit_status', 'NOT_RUN_BY_DEFAULT')}"
            )
            if not options.get("summary_only"):
                self.stdout.write("")
                for item in report["results"]:
                    self.stdout.write(
                        f"- {item['filename']}: type={item['document_type']} "
                        f"local_xsd_valid={item['local_xsd_valid']} "
                        f"xsd_errors={item['xsd_error_count']} "
                        f"sig_present={item['signature_present']} "
                        f"sig_verified={item['signature_verified']}"
                    )
            self.stdout.write("")
            self.stdout.write(
                "Local XSD valid does not equal DGII acceptance. "
                "No network call. No DGII submission. NOT certification evidence."
            )

        if options.get("fail_on_invalid") and report["local_xsd_invalid_count"]:
            sys.exit(1)
