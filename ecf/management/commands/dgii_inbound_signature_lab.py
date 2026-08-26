import json
import sys
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from ecf.dgii.inbound_lab import DEFAULT_FIXTURE_DIR, SYNTHETIC_SAMPLE_MARKER
from ecf.dgii.inbound_signature_lab import (
    VERIFICATION_SCOPE,
    analyze_path_with_signature_lab,
    build_signature_lab_report,
)


class Command(BaseCommand):
    help = (
        "Inspect synthetic inbound XMLDSig Signature nodes (offline, test-only). "
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
            "--fail-on-invalid-signature",
            action="store_true",
            dest="fail_on_invalid_signature",
            help="Exit with code 1 if any fixture is TEST_ONLY_INVALID or PARSE_ERROR.",
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
            results = analyze_path_with_signature_lab(target)
        except FileNotFoundError as exc:
            raise CommandError(str(exc)) from exc

        report = build_signature_lab_report(results)

        if options.get("json_flag"):
            self.stdout.write(json.dumps(report, indent=2, sort_keys=True))
        else:
            self.stdout.write(
                "DGII inbound signature lab (LOCAL_OFFLINE_TEST_ONLY — NOT_DGII_COMPLIANT)"
            )
            self.stdout.write("=" * 60)
            self.stdout.write("NOT_DGII_COMPLIANT")
            self.stdout.write(VERIFICATION_SCOPE)
            self.stdout.write(SYNTHETIC_SAMPLE_MARKER)
            self.stdout.write("not_certification_evidence=true")
            self.stdout.write("production_signature_ready=false")
            self.stdout.write(f"lab_mode: {report['lab_mode']}")
            self.stdout.write(f"verification_scope: {report['verification_scope']}")
            self.stdout.write(
                f"cryptographic_xmldsig_verification: {report['cryptographic_xmldsig_verification']}"
            )
            self.stdout.write(f"compliance_status: {report['compliance_status']}")
            self.stdout.write(f"dgii_submission_allowed: {report['dgii_submission_allowed']}")
            self.stdout.write(f"fixture_count: {report['fixture_count']}")
            self.stdout.write(f"invalid_signature_count: {report['invalid_signature_count']}")
            self.stdout.write(f"persistence_lab_available: {report['persistence_lab_available']}")
            self.stdout.write(f"persistence_command: {report['persistence_command']}")
            self.stdout.write(f"persistence_status: {report['persistence_status']}")
            self.stdout.write(f"workflow_lab_available: {report['workflow_lab_available']}")
            self.stdout.write(f"workflow_command: {report['workflow_command']}")
            self.stdout.write(f"workflow_status: {report['workflow_status']}")
            if not options.get("summary_only"):
                self.stdout.write("")
                for item in report["results"]:
                    self.stdout.write(
                        f"- {item['filename']}: type={item['document_type']} "
                        f"present={item['signature_present']} "
                        f"status={item['signature_verification_status']} "
                        f"verified={item['signature_verified']} "
                        f"prod_ready={item['production_signature_ready']}"
                    )
            self.stdout.write("")
            self.stdout.write(
                "Signature present does not equal valid. "
                "No network call. No DGII submission. NOT certification evidence."
            )

        if options.get("fail_on_invalid_signature") and report["invalid_signature_count"]:
            sys.exit(1)
