import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from ecf.dgii.inbound_audit_retention_lab import (
    DEFAULT_RETENTION_DAYS,
    LAB_MODE,
    audit_lab_records,
    build_audit_retention_lab_report,
    build_export_manifest,
    write_export_manifest,
)
from ecf.models import InboundXMLLabRecord


class Command(BaseCommand):
    help = (
        "Non-production inbound audit/retention lab. Dry-run by default. "
        "Writes only InboundXMLLabAuditEvent when --apply-lab-audit is set. "
        "Never deletes. No DGII calls, no TrackId, not certification evidence."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--from-lab-records",
            action="store_true",
            dest="from_lab_records",
            help="Audit existing InboundXMLLabRecord rows (default if no --record-id).",
        )
        parser.add_argument(
            "--record-id",
            type=int,
            default=None,
            dest="record_id",
            help="Audit one InboundXMLLabRecord by primary key.",
        )
        parser.add_argument("--json", action="store_true", dest="json_flag")
        parser.add_argument(
            "--apply-lab-audit",
            action="store_true",
            dest="apply_lab_audit",
            help="Write InboundXMLLabAuditEvent rows (off by default).",
        )
        parser.add_argument(
            "--export-manifest",
            action="store_true",
            dest="export_manifest",
            help="Write metadata-only export under runtime/dgii_lab_exports/.",
        )
        parser.add_argument(
            "--export-path",
            default=None,
            help="Optional path under runtime/dgii_lab_exports/ only.",
        )
        parser.add_argument(
            "--retention-days",
            type=int,
            default=DEFAULT_RETENTION_DAYS,
            dest="retention_days",
            help="Lab retention age threshold in days (default 30).",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Limit number of records audited.",
        )
        parser.add_argument(
            "--summary-only",
            action="store_true",
            dest="summary_only",
            help="Print summary without per-record details (ignored with --json).",
        )

    def handle(self, *args, **options):
        apply = bool(options.get("apply_lab_audit"))
        limit = options.get("limit")
        retention_days = options.get("retention_days", DEFAULT_RETENTION_DAYS)
        export_path_written = None

        try:
            if options.get("record_id") is not None:
                record_id = options["record_id"]
                try:
                    record = InboundXMLLabRecord.objects.get(pk=record_id)
                except InboundXMLLabRecord.DoesNotExist as exc:
                    raise CommandError(
                        f"InboundXMLLabRecord not found: {record_id}"
                    ) from exc
                records = [record]
            else:
                # Default / --from-lab-records: all lab records
                records = InboundXMLLabRecord.objects.all()

            results = audit_lab_records(
                records,
                apply=apply,
                retention_days=retention_days,
                limit=limit,
            )

            if options.get("export_manifest"):
                # Re-fetch limited set for export consistency
                if options.get("record_id") is not None:
                    export_qs = InboundXMLLabRecord.objects.filter(pk=options["record_id"])
                else:
                    export_qs = InboundXMLLabRecord.objects.all().order_by("created_at", "id")
                    if limit is not None:
                        export_qs = export_qs[:limit]
                manifest = build_export_manifest(export_qs)
                try:
                    written = write_export_manifest(options.get("export_path"), manifest)
                except ValueError as exc:
                    raise CommandError(str(exc)) from exc
                export_path_written = str(written)
        except FileNotFoundError as exc:
            raise CommandError(str(exc)) from exc

        report = build_audit_retention_lab_report(
            results,
            dry_run=not apply,
            retention_days=retention_days,
            export_path=export_path_written,
        )

        if options.get("json_flag"):
            self.stdout.write(json.dumps(report, indent=2, sort_keys=True, default=str))
            return

        self.stdout.write(
            "DGII inbound audit/retention lab (NON_PRODUCTION_LAB_ONLY — NOT_DGII_COMPLIANT)"
        )
        self.stdout.write("=" * 60)
        self.stdout.write("NOT_DGII_COMPLIANT")
        self.stdout.write(LAB_MODE)
        self.stdout.write("certification_evidence=false")
        self.stdout.write("dgii_submission_allowed=false")
        self.stdout.write("track_id=null")
        self.stdout.write("dgii_call_made=false")
        self.stdout.write("destructive_retention_actions_enabled=false")
        self.stdout.write(f"dry_run: {report['dry_run']}")
        self.stdout.write(f"apply_lab_audit: {report['apply_lab_audit']}")
        self.stdout.write(f"retention_days: {report['retention_days']}")
        self.stdout.write(f"result_count: {report['result_count']}")
        self.stdout.write(f"applied_count: {report['applied_count']}")
        self.stdout.write(f"retention_decision_counts: {report['retention_decision_counts']}")
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
        if export_path_written:
            self.stdout.write(f"export_path: {export_path_written}")
        if not options.get("summary_only"):
            self.stdout.write("")
            for item in report["results"]:
                name = item.get("filename") or str(item.get("raw_sha256", ""))[:12]
                self.stdout.write(
                    f"- {name}: decision={item.get('retention_decision')} "
                    f"event={item.get('event_type')} reason={item.get('reason')} "
                    f"applied={item.get('applied', False)}"
                )
        self.stdout.write("")
        self.stdout.write(
            "Lab audit events are not a DGII audit trail. No deletes. "
            "No network call. No DGII submission. NOT certification evidence."
        )
