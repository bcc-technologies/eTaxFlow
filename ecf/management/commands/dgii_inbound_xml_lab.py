import json
import sys
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from ecf.dgii.inbound_lab import (
    DEFAULT_FIXTURE_DIR,
    SYNTHETIC_SAMPLE_MARKER,
    analyze_fixture_directory,
    analyze_fixture_file,
    build_lab_report,
)


class Command(BaseCommand):
    help = (
        "Analyze synthetic inbound XML fixtures in the non-production lab. "
        "No DGII calls, no database mutation, no TrackId."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--path",
            default=str(DEFAULT_FIXTURE_DIR),
            help="Fixture file or directory (default: tests/fixtures/dgii/inbound_lab/)",
        )
        parser.add_argument("--json", action="store_true", dest="json_flag")
        parser.add_argument(
            "--fail-on-errors",
            action="store_true",
            dest="fail_on_errors",
            help="Exit with code 1 if any fixture has classification errors.",
        )

    def handle(self, *args, **options):
        target = Path(options["path"])
        if not target.exists():
            raise CommandError(f"Path not found: {target}")

        if target.is_file():
            results = [analyze_fixture_file(target)]
        elif target.is_dir():
            results = analyze_fixture_directory(target)
        else:
            raise CommandError(f"Path is neither file nor directory: {target}")

        report = build_lab_report(results)

        if options.get("json_flag"):
            self.stdout.write(json.dumps(report, indent=2, sort_keys=True))
        else:
            self.stdout.write("DGII inbound XML lab (NON_PRODUCTION_ONLY — NOT_DGII_COMPLIANT)")
            self.stdout.write("=" * 60)
            self.stdout.write(f"lab_mode: {report['lab_mode']}")
            self.stdout.write(f"synthetic_marker: {SYNTHETIC_SAMPLE_MARKER}")
            self.stdout.write(f"compliance_status: {report['compliance_status']}")
            self.stdout.write(f"dgii_submission_allowed: {report['dgii_submission_allowed']}")
            self.stdout.write(f"not_certification_evidence: {report['not_certification_evidence']}")
            self.stdout.write(f"fixture_count: {report['fixture_count']}")
            self.stdout.write(f"error_count: {report['error_count']}")
            self.stdout.write(
                f"schema_validation_status: {report['schema_validation_status']}"
            )
            self.stdout.write(
                f"schema_validation_command: {report['schema_validation_command']}"
            )
            self.stdout.write(
                f"signature_verification_status: {report['signature_verification_status']}"
            )
            self.stdout.write(
                f"signature_verification_command: {report['signature_verification_command']}"
            )
            self.stdout.write("")
            for item in report["results"]:
                self.stdout.write(
                    f"- {item['filename']}: type={item['document_type']} "
                    f"status={item['status']} sig={item['signature_present']} "
                    f"sha256={item['sha256'][:12]}..."
                )
            self.stdout.write("")
            self.stdout.write("No network call. No DGII submission. NOT certification evidence.")

        if options.get("fail_on_errors") and report["error_count"]:
            sys.exit(1)
