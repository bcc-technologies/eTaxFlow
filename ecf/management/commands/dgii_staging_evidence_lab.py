import json

from django.core.management.base import BaseCommand, CommandError

from ecf.dgii.staging_evidence_lab import (
    EVIDENCE_SCOPE,
    LAB_MODE,
    STAGING_EVIDENCE_BLOCKED,
    build_evidence_template,
    build_staging_evidence_lab_report,
    load_evidence_file,
    validate_evidence_payload,
    write_evidence_report,
    write_evidence_template,
)


class Command(BaseCommand):
    help = (
        "Offline staging deployment evidence collector lab. Template/validate/report only. "
        "No network checks, no DGII calls, no TrackId, not certification evidence."
    )

    def add_arguments(self, parser):
        parser.add_argument("--json", action="store_true", dest="json_flag")
        parser.add_argument(
            "--summary-only",
            action="store_true",
            dest="summary_only",
            help="Print summary without item listing (ignored with --json).",
        )
        parser.add_argument(
            "--write-template",
            action="store_true",
            dest="write_template",
            help="Write evidence template JSON under runtime/dgii_staging_evidence/.",
        )
        parser.add_argument(
            "--template-path",
            default=None,
            help="Optional template path under runtime/dgii_staging_evidence/.",
        )
        parser.add_argument(
            "--evidence-file",
            default=None,
            help="Optional evidence JSON under runtime/dgii_staging_evidence/ to validate.",
        )
        parser.add_argument(
            "--export-report",
            action="store_true",
            dest="export_report",
            help="Write metadata-only validation report under runtime/dgii_staging_evidence/.",
        )
        parser.add_argument(
            "--export-path",
            default=None,
            help="Optional report path under runtime/dgii_staging_evidence/.",
        )

    def handle(self, *args, **options):
        template_path = None
        report_path = None

        try:
            if options.get("write_template"):
                written = write_evidence_template(options.get("template_path"))
                template_path = str(written)

            if options.get("evidence_file"):
                payload = load_evidence_file(options["evidence_file"])
            else:
                payload = build_evidence_template()

            evidence_result = validate_evidence_payload(payload)

            if options.get("export_report") or options.get("export_path"):
                written_report = write_evidence_report(
                    options.get("export_path"), evidence_result
                )
                report_path = str(written_report)

            report = build_staging_evidence_lab_report(
                evidence_result=evidence_result,
                template_path=template_path,
                report_path=report_path,
            )
        except (ValueError, json.JSONDecodeError, OSError) as exc:
            raise CommandError(str(exc)) from exc

        if options.get("json_flag"):
            self.stdout.write(json.dumps(report, indent=2, sort_keys=True, default=str))
            return

        self.stdout.write(
            "DGII staging evidence lab (NON_PRODUCTION_LAB_ONLY — NOT_DGII_COMPLIANT)"
        )
        self.stdout.write("=" * 60)
        self.stdout.write("NOT_DGII_COMPLIANT")
        self.stdout.write(LAB_MODE)
        self.stdout.write(EVIDENCE_SCOPE)
        self.stdout.write(
            report.get("staging_evidence_decision") or STAGING_EVIDENCE_BLOCKED
        )
        self.stdout.write("certification_evidence=false")
        self.stdout.write("dgii_submission_allowed=false")
        self.stdout.write(
            f"public_endpoints_enabled={str(report['public_endpoints_enabled']).lower()}"
        )
        self.stdout.write("production_staging_ready=false")
        self.stdout.write("track_id=null")
        self.stdout.write("dgii_call_made=false")
        self.stdout.write("network_checks_performed=false")
        self.stdout.write(f"certification_package_lab_available: {report.get('certification_package_lab_available', True)}")
        self.stdout.write(f"certification_package_command: {report.get('certification_package_command', 'dgii_certification_package_lab')}")
        self.stdout.write(f"certification_package_status: {report.get('certification_package_status', 'NOT_RUN_BY_DEFAULT')}")
        self.stdout.write(f"final_go_no_go_lab_available: {report.get('final_go_no_go_lab_available', True)}")
        self.stdout.write(f"final_go_no_go_command: {report.get('final_go_no_go_command', 'dgii_final_go_no_go_lab')}")
        self.stdout.write(f"final_go_no_go_status: {report.get('final_go_no_go_status', 'NOT_RUN_BY_DEFAULT')}")
        self.stdout.write(f"final_inbound_audit_lab_available: {report.get('final_inbound_audit_lab_available', True)}")
        self.stdout.write("final_inbound_audit_command: dgii_final_inbound_audit_lab")
        self.stdout.write(f"final_inbound_audit_status: {report.get('final_inbound_audit_status', 'NOT_RUN_BY_DEFAULT')}")
        self.stdout.write(f"missing_count: {report['missing_count']}")
        self.stdout.write(f"incomplete_count: {report['incomplete_count']}")
        self.stdout.write(f"provided_count: {report['provided_count']}")
        self.stdout.write(f"manual_review_count: {report['manual_review_count']}")
        self.stdout.write(f"blocker_count: {report['blocker_count']}")
        if template_path:
            self.stdout.write(f"template_path: {template_path}")
        if report_path:
            self.stdout.write(f"report_path: {report_path}")
        if not options.get("summary_only"):
            self.stdout.write("")
            self.stdout.write("Evidence items:")
            for item in report.get("evidence_items") or []:
                self.stdout.write(
                    f"  - {item['evidence_id']}: {item['status']} "
                    f"(manual_review_required={item['manual_review_required']})"
                )
        self.stdout.write("")
        self.stdout.write(
            "Offline/manual evidence only. No network checks. No DGII submission. "
            "NOT certification evidence. NOT staging approval."
        )
