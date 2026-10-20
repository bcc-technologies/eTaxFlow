import json

from django.core.management.base import BaseCommand, CommandError

from ecf.dgii.final_go_no_go_lab import (
    FINAL_DECISION_BLOCKED,
    REVIEW_SCOPE,
    evaluate_final_go_no_go,
    write_final_go_no_go_review,
)


class Command(BaseCommand):
    help = (
        "Final non-production pre-cert go/no-go review lab. FINAL_REVIEW_LAB_ONLY; "
        "no portal upload, no signing, no DGII calls, no TrackId, not certification evidence."
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
            "--export-review",
            action="store_true",
            dest="export_review",
            help="Write JSON/Markdown/manifest under runtime/dgii_final_reviews/.",
        )
        parser.add_argument(
            "--output-dir",
            default=None,
            help="Optional directory under runtime/dgii_final_reviews/.",
        )

    def handle(self, *args, **options):
        try:
            if options.get("export_review") or options.get("output_dir"):
                report = write_final_go_no_go_review(options.get("output_dir"))
            else:
                report = evaluate_final_go_no_go()
                report["final_go_no_go_status"] = "RUN"
                report["files_exported"] = []
                report["output_dir"] = None
        except ValueError as exc:
            raise CommandError(str(exc)) from exc

        if options.get("json_flag"):
            self.stdout.write(json.dumps(report, indent=2, sort_keys=True, default=str))
            return

        self.stdout.write(
            "DGII final go/no-go lab (FINAL_REVIEW_LAB_ONLY — NOT_DGII_COMPLIANT)"
        )
        self.stdout.write("=" * 60)
        self.stdout.write("NOT_DGII_COMPLIANT")
        self.stdout.write(REVIEW_SCOPE)
        self.stdout.write(FINAL_DECISION_BLOCKED)
        self.stdout.write("dgii_submission_allowed=false")
        self.stdout.write("portal_submission_allowed=false")
        self.stdout.write("certification_evidence=false")
        self.stdout.write(
            f"public_endpoints_enabled={str(report.get('public_endpoints_enabled')).lower()}"
        )
        self.stdout.write("production_staging_ready=false")
        self.stdout.write("production_security_ready=false")
        self.stdout.write("production_signature_ready=false")
        self.stdout.write("production_signature_verification_ready=false")
        self.stdout.write("track_id=null")
        self.stdout.write("dgii_call_made=false")
        self.stdout.write(f"readiness_status: {report.get('readiness_status')}")
        self.stdout.write(f"blocker_count: {report.get('blocker_count')}")
        if report.get("output_dir"):
            self.stdout.write(f"output_dir: {report['output_dir']}")
        if report.get("files_exported"):
            self.stdout.write(f"files_exported: {len(report['files_exported'])}")
        if not options.get("summary_only"):
            self.stdout.write("")
            self.stdout.write("Decision reasons:")
            for item in report.get("decision_reasons") or []:
                self.stdout.write(f"  - {item}")
            self.stdout.write("")
            self.stdout.write("Human decisions required:")
            for item in report.get("human_decisions_required") or []:
                self.stdout.write(f"  - {item}")
            self.stdout.write("")
            self.stdout.write("Blockers (first 15):")
            for blocker in (report.get("blockers") or [])[:15]:
                self.stdout.write(f"  - {blocker}")
        self.stdout.write("")
        self.stdout.write(
            "FINAL_REVIEW_LAB_ONLY. No portal submission. No endpoint activation. "
            "No signing. No DGII submission. NOT certification evidence."
        )
