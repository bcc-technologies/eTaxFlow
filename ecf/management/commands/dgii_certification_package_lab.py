import json

from django.core.management.base import BaseCommand, CommandError

from ecf.dgii.certification_package_lab import (
    PACKAGE_BLOCKED,
    PACKAGE_SCOPE,
    build_certification_package_draft,
    write_certification_package,
)


class Command(BaseCommand):
    help = (
        "Certification portal submission package draft lab. DRAFT_ONLY; no portal upload, "
        "no signing, no DGII calls, no TrackId, not certification evidence."
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
            "--export-package",
            action="store_true",
            dest="export_package",
            help="Write JSON/Markdown/manifest under runtime/dgii_certification_package_drafts/.",
        )
        parser.add_argument(
            "--output-dir",
            default=None,
            help="Optional directory under runtime/dgii_certification_package_drafts/.",
        )

    def handle(self, *args, **options):
        try:
            if options.get("export_package") or options.get("output_dir"):
                report = write_certification_package(options.get("output_dir"))
            else:
                report = build_certification_package_draft()
                report["certification_package_status"] = "RUN"
                report["files_exported"] = []
                report["output_dir"] = None
        except ValueError as exc:
            raise CommandError(str(exc)) from exc

        if options.get("json_flag"):
            self.stdout.write(json.dumps(report, indent=2, sort_keys=True, default=str))
            return

        software = report.get("software_fields") or {}
        urls = report.get("planned_urls") or {}
        self.stdout.write(
            "DGII certification package lab (DRAFT_ONLY — NOT_DGII_COMPLIANT)"
        )
        self.stdout.write("=" * 60)
        self.stdout.write("NOT_DGII_COMPLIANT")
        self.stdout.write(PACKAGE_SCOPE)
        self.stdout.write(PACKAGE_BLOCKED)
        self.stdout.write("submission_allowed=false")
        self.stdout.write("certification_evidence=false")
        self.stdout.write("dgii_submission_allowed=false")
        self.stdout.write(
            f"public_endpoints_enabled={str(report.get('public_endpoints_enabled')).lower()}"
        )
        self.stdout.write("production_staging_ready=false")
        self.stdout.write("production_security_ready=false")
        self.stdout.write("production_signature_ready=false")
        self.stdout.write("track_id=null")
        self.stdout.write("dgii_call_made=false")
        self.stdout.write(f"final_go_no_go_lab_available: {report.get('final_go_no_go_lab_available', True)}")
        self.stdout.write(f"final_go_no_go_command: {report.get('final_go_no_go_command', 'dgii_final_go_no_go_lab')}")
        self.stdout.write(f"final_go_no_go_status: {report.get('final_go_no_go_status', 'NOT_RUN_BY_DEFAULT')}")
        self.stdout.write(f"software_type: {software.get('software_type')}")
        self.stdout.write(f"software_name: {software.get('software_name')}")
        self.stdout.write(f"software_version: {software.get('software_version')}")
        self.stdout.write(
            f"public_base_url: {software.get('public_base_url') or '(blank)'}"
        )
        self.stdout.write(f"recepcion_path: {urls.get('recepcion_path')}")
        self.stdout.write(f"blocker_count: {report.get('blocker_count')}")
        if report.get("output_dir"):
            self.stdout.write(f"output_dir: {report['output_dir']}")
        if report.get("files_exported"):
            self.stdout.write(f"files_exported: {len(report['files_exported'])}")
        if not options.get("summary_only"):
            self.stdout.write("")
            self.stdout.write("Human decisions required:")
            for item in report.get("human_decisions_required") or []:
                self.stdout.write(f"  - {item}")
            self.stdout.write("")
            self.stdout.write("Package blockers (first 12):")
            for blocker in (report.get("blockers") or [])[:12]:
                self.stdout.write(f"  - {blocker}")
        self.stdout.write("")
        self.stdout.write(
            "DRAFT_ONLY. No portal submission. No signing. No network call. "
            "No DGII submission. NOT certification evidence."
        )
