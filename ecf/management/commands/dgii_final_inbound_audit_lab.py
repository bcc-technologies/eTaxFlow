import json

from django.core.management.base import BaseCommand, CommandError

from ecf.dgii.final_inbound_audit_lab import (
    FINAL_DECISION_BLOCKED,
    REPORT_SCOPE,
    build_final_inbound_audit_report,
    write_final_inbound_audit_report,
)


class Command(BaseCommand):
    help = (
        "Final inbound lab audit report (Phase 024-039). FINAL_AUDIT_LAB_ONLY; "
        "no portal upload, no endpoint activation, no DGII calls, not certification evidence."
    )

    def add_arguments(self, parser):
        parser.add_argument("--json", action="store_true", dest="json_flag")
        parser.add_argument(
            "--summary-only",
            action="store_true",
            dest="summary_only",
            help="Print summary without blocker listing (ignored with --json).",
        )
        parser.add_argument(
            "--export-json",
            action="store_true",
            dest="export_json",
            help="Write JSON report under runtime/dgii_final_audit_reports/.",
        )
        parser.add_argument(
            "--export-markdown",
            action="store_true",
            dest="export_markdown",
            help="Write Markdown report under runtime/dgii_final_audit_reports/.",
        )
        parser.add_argument(
            "--output-dir",
            default=None,
            help="Optional directory under runtime/dgii_final_audit_reports/.",
        )

    def handle(self, *args, **options):
        export_any = options.get("export_json") or options.get("export_markdown")
        try:
            if export_any or options.get("output_dir"):
                report = write_final_inbound_audit_report(options.get("output_dir"))
            else:
                report = build_final_inbound_audit_report()
                report["final_inbound_audit_status"] = "RUN"
                report["files_exported"] = []
                report["output_dir"] = None
        except ValueError as exc:
            raise CommandError(str(exc)) from exc

        if options.get("json_flag"):
            self.stdout.write(json.dumps(report, indent=2, sort_keys=True, default=str))
            return

        self.stdout.write(
            "DGII final inbound audit lab (FINAL_AUDIT_LAB_ONLY — NOT_DGII_COMPLIANT)"
        )
        self.stdout.write("=" * 60)
        self.stdout.write("NOT_DGII_COMPLIANT")
        self.stdout.write(REPORT_SCOPE)
        self.stdout.write(FINAL_DECISION_BLOCKED)
        self.stdout.write("dgii_submission_allowed=false")
        self.stdout.write("portal_submission_allowed=false")
        self.stdout.write("certification_evidence=false")
        self.stdout.write(
            f"public_endpoints_enabled={str(report.get('public_endpoints_enabled')).lower()}"
        )
        self.stdout.write("endpoint_activation_allowed=false")
        self.stdout.write("production_staging_ready=false")
        self.stdout.write("production_security_ready=false")
        self.stdout.write("production_signature_ready=false")
        self.stdout.write("production_signature_verification_ready=false")
        self.stdout.write("track_id=null")
        self.stdout.write("dgii_call_made=false")
        self.stdout.write(f"phase_range: {report.get('phase_range')}")
        self.stdout.write(f"blocker_count: {report.get('blocker_count')}")
        if report.get("output_dir"):
            self.stdout.write(f"output_dir: {report['output_dir']}")
        if report.get("files_exported"):
            self.stdout.write(f"files_exported: {len(report['files_exported'])}")
        if not options.get("summary_only"):
            self.stdout.write("")
            self.stdout.write("Next operational steps:")
            for item in (report.get("next_operational_steps") or [])[:6]:
                self.stdout.write(f"  - {item}")
            self.stdout.write("")
            self.stdout.write("Blockers (first 12):")
            for blocker in (report.get("blockers") or [])[:12]:
                self.stdout.write(f"  - {blocker}")
        self.stdout.write("")
        self.stdout.write(
            "FINAL_AUDIT_LAB_ONLY. No portal submission. No endpoint activation. "
            "No signing. No DGII submission. NOT certification evidence."
        )
