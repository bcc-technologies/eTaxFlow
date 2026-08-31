import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from ecf.dgii.inbound_reporting_lab import (
    LAB_MODE,
    REPORT_SCOPE,
    build_csv_summary,
    build_json_report,
    build_markdown_summary,
    build_reporting_lab_report,
    collect_lab_report_data,
    resolve_output_dir,
    write_report_bundle,
)


class Command(BaseCommand):
    help = (
        "Non-production inbound reporting export lab. Metadata-only; no DB writes. "
        "No DGII calls, no TrackId, no raw XML export, not certification evidence."
    )

    def add_arguments(self, parser):
        parser.add_argument("--json", action="store_true", dest="json_flag")
        parser.add_argument(
            "--summary-only",
            action="store_true",
            dest="summary_only",
            help="Print summary without detailed breakdowns (ignored with --json).",
        )
        parser.add_argument("--export-json", action="store_true", dest="export_json")
        parser.add_argument("--export-csv", action="store_true", dest="export_csv")
        parser.add_argument(
            "--export-markdown", action="store_true", dest="export_markdown"
        )
        parser.add_argument(
            "--export-bundle",
            action="store_true",
            dest="export_bundle",
            help="Write JSON/CSV/Markdown/manifest under runtime/dgii_lab_reports/.",
        )
        parser.add_argument(
            "--output-dir",
            default=None,
            help="Optional directory under runtime/dgii_lab_reports/ (traversal rejected).",
        )

    def handle(self, *args, **options):
        data = collect_lab_report_data()
        files_exported: list[str] = []
        output_dir = None

        export_any = any(
            [
                options.get("export_bundle"),
                options.get("export_json"),
                options.get("export_csv"),
                options.get("export_markdown"),
                options.get("output_dir"),
            ]
        )

        try:
            if options.get("export_bundle") or (
                options.get("output_dir")
                and not any(
                    [
                        options.get("export_json"),
                        options.get("export_csv"),
                        options.get("export_markdown"),
                    ]
                )
            ):
                report = write_report_bundle(options.get("output_dir"), data=data)
                files_exported = list(report.get("files_exported") or [])
                output_dir = report.get("output_dir")
            elif export_any:
                target = resolve_output_dir(options.get("output_dir"))
                target.mkdir(parents=True, exist_ok=True)
                output_dir = str(target)
                if options.get("export_json"):
                    path = target / "inbound_lab_report.json"
                    path.write_text(
                        json.dumps(
                            build_json_report(data),
                            indent=2,
                            sort_keys=True,
                            default=str,
                        )
                        + "\n",
                        encoding="utf-8",
                    )
                    files_exported.append(str(path))
                if options.get("export_csv"):
                    path = target / "inbound_lab_summary.csv"
                    path.write_text(build_csv_summary(data), encoding="utf-8")
                    files_exported.append(str(path))
                if options.get("export_markdown"):
                    path = target / "inbound_lab_summary.md"
                    path.write_text(build_markdown_summary(data), encoding="utf-8")
                    files_exported.append(str(path))
                report = build_reporting_lab_report(
                    data=data,
                    files_exported=files_exported,
                    output_dir=output_dir,
                )
            else:
                report = build_reporting_lab_report(data=data)
        except ValueError as exc:
            raise CommandError(str(exc)) from exc

        if options.get("json_flag"):
            self.stdout.write(json.dumps(report, indent=2, sort_keys=True, default=str))
            return

        self.stdout.write(
            "DGII inbound reporting lab (NON_PRODUCTION_LAB_ONLY — NOT_DGII_COMPLIANT)"
        )
        self.stdout.write("=" * 60)
        self.stdout.write("NOT_DGII_COMPLIANT")
        self.stdout.write(LAB_MODE)
        self.stdout.write(REPORT_SCOPE)
        self.stdout.write("certification_evidence=false")
        self.stdout.write("dgii_submission_allowed=false")
        self.stdout.write(
            f"public_endpoints_enabled={str(report['public_endpoints_enabled']).lower()}"
        )
        self.stdout.write("track_id=null")
        self.stdout.write("dgii_call_made=false")
        self.stdout.write(f"record_count: {report['record_count']}")
        self.stdout.write(f"workflow_event_count: {report['workflow_event_count']}")
        self.stdout.write(f"audit_event_count: {report['audit_event_count']}")
        self.stdout.write(f"blocker_count: {report['blocker_count']}")
        self.stdout.write(f"staging_evidence_lab_available: {report['staging_evidence_lab_available']}")
        self.stdout.write(f"staging_evidence_command: {report['staging_evidence_command']}")
        self.stdout.write(f"staging_evidence_status: {report.get('staging_evidence_status', 'NOT_RUN_BY_DEFAULT')}")
        self.stdout.write(f"certification_package_lab_available: {report.get('certification_package_lab_available', True)}")
        self.stdout.write(f"certification_package_command: {report.get('certification_package_command', 'dgii_certification_package_lab')}")
        self.stdout.write(f"certification_package_status: {report.get('certification_package_status', 'NOT_RUN_BY_DEFAULT')}")
        self.stdout.write(f"final_go_no_go_lab_available: {report.get('final_go_no_go_lab_available', True)}")
        self.stdout.write(f"final_go_no_go_command: {report.get('final_go_no_go_command', 'dgii_final_go_no_go_lab')}")
        self.stdout.write(f"final_go_no_go_status: {report.get('final_go_no_go_status', 'NOT_RUN_BY_DEFAULT')}")
        if output_dir:
            self.stdout.write(f"output_dir: {output_dir}")
        if files_exported:
            self.stdout.write(f"files_exported: {len(files_exported)}")
        if not options.get("summary_only"):
            self.stdout.write("")
            self.stdout.write(f"document_type_breakdown: {report['document_type_breakdown']}")
            self.stdout.write(f"schema_status_breakdown: {report['schema_status_breakdown']}")
            self.stdout.write(
                f"signature_status_breakdown: {report['signature_status_breakdown']}"
            )
            self.stdout.write(
                f"workflow_route_breakdown: {report['workflow_route_breakdown']}"
            )
            self.stdout.write(
                f"retention_decision_breakdown: {report['retention_decision_breakdown']}"
            )
        self.stdout.write("")
        self.stdout.write(
            "Metadata-only report. No raw XML. No network call. "
            "No DGII submission. NOT certification evidence."
        )
