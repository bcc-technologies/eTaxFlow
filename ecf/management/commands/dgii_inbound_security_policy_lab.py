import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from ecf.dgii.inbound_security_policy_lab import (
    LAB_MODE,
    SECURITY_POLICY_BLOCKED,
    build_security_policy_report,
    write_security_policy_report,
)


class Command(BaseCommand):
    help = (
        "Inbound security controls policy review lab. Report-only; no DB writes. "
        "No DGII calls, no TrackId, not certification evidence, does not enable endpoints."
    )

    def add_arguments(self, parser):
        parser.add_argument("--json", action="store_true", dest="json_flag")
        parser.add_argument(
            "--summary-only",
            action="store_true",
            dest="summary_only",
            help="Print summary without per-control details (ignored with --json).",
        )
        parser.add_argument(
            "--export-report",
            action="store_true",
            dest="export_report",
            help="Write metadata-only JSON under runtime/dgii_security_reports/.",
        )
        parser.add_argument(
            "--export-path",
            default=None,
            help="Optional path under runtime/dgii_security_reports/ (traversal rejected).",
        )

    def handle(self, *args, **options):
        report = build_security_policy_report()
        export_path = None

        if options.get("export_report") or options.get("export_path"):
            try:
                written = write_security_policy_report(options.get("export_path"), report)
            except ValueError as exc:
                raise CommandError(str(exc)) from exc
            export_path = str(written)
            report = {**report, "export_path": export_path}

        if options.get("json_flag"):
            self.stdout.write(json.dumps(report, indent=2, sort_keys=True, default=str))
            return

        self.stdout.write(
            "DGII inbound security policy lab (NON_PRODUCTION_LAB_ONLY — NOT_DGII_COMPLIANT)"
        )
        self.stdout.write("=" * 60)
        self.stdout.write("NOT_DGII_COMPLIANT")
        self.stdout.write(LAB_MODE)
        self.stdout.write(SECURITY_POLICY_BLOCKED)
        self.stdout.write("certification_evidence=false")
        self.stdout.write("dgii_submission_allowed=false")
        self.stdout.write(f"public_endpoints_enabled={str(report['public_endpoints_enabled']).lower()}")
        self.stdout.write("production_security_ready=false")
        self.stdout.write(f"reporting_lab_available: {report['reporting_lab_available']}")
        self.stdout.write(f"reporting_command: {report['reporting_command']}")
        self.stdout.write(f"reporting_status: {report['reporting_status']}")
        self.stdout.write("track_id=null")
        self.stdout.write("dgii_call_made=false")
        summary = report["summary"]
        self.stdout.write(f"control_count: {summary['control_count']}")
        self.stdout.write(f"pass_count: {summary['pass_count']}")
        self.stdout.write(f"fail_count: {summary['fail_count']}")
        self.stdout.write(f"warning_count: {summary['warning_count']}")
        self.stdout.write(f"not_implemented_count: {summary['not_implemented_count']}")
        self.stdout.write(f"manual_review_count: {summary['manual_review_count']}")
        self.stdout.write(f"blocker_count: {summary['blocker_count']}")
        if export_path:
            self.stdout.write(f"export_path: {export_path}")
        if not options.get("summary_only"):
            self.stdout.write("")
            for item in report["controls"]:
                self.stdout.write(
                    f"- {item['control_id']}: {item['current_status']} "
                    f"blocker={item['blocker']} family={item['family']}"
                )
        self.stdout.write("")
        self.stdout.write(
            "Security policy lab is not production approval. No network call. "
            "No DGII submission. NOT certification evidence. Endpoints remain DISABLED."
        )
