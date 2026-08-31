import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from ecf.dgii.inbound_lab import DEFAULT_FIXTURE_DIR, SYNTHETIC_SAMPLE_MARKER
from ecf.dgii.inbound_workflow_lab import (
    LAB_MODE,
    build_workflow_lab_report,
    route_lab_records,
    route_path_via_persistence_lab,
)
from ecf.models import InboundXMLLabRecord


class Command(BaseCommand):
    help = (
        "Non-production inbound workflow routing lab. Dry-run by default. "
        "Writes only InboundXMLLabWorkflowEvent when --apply-lab-workflow is set. "
        "No DGII calls, no TrackId, not certification evidence."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--path",
            default=None,
            help="Fixture file or directory for lab analysis routing.",
        )
        parser.add_argument(
            "--from-lab-records",
            action="store_true",
            dest="from_lab_records",
            help="Route existing InboundXMLLabRecord rows.",
        )
        parser.add_argument(
            "--record-id",
            type=int,
            default=None,
            dest="record_id",
            help="Route one InboundXMLLabRecord by primary key.",
        )
        parser.add_argument("--json", action="store_true", dest="json_flag")
        parser.add_argument(
            "--apply-lab-workflow",
            action="store_true",
            dest="apply_lab_workflow",
            help="Write InboundXMLLabWorkflowEvent rows (off by default).",
        )
        parser.add_argument(
            "--summary-only",
            action="store_true",
            dest="summary_only",
            help="Print summary without per-record details (ignored with --json).",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Limit number of records routed.",
        )

    def handle(self, *args, **options):
        apply = bool(options.get("apply_lab_workflow"))
        limit = options.get("limit")
        source = "unknown"

        try:
            if options.get("record_id") is not None:
                record_id = options["record_id"]
                try:
                    record = InboundXMLLabRecord.objects.get(pk=record_id)
                except InboundXMLLabRecord.DoesNotExist as exc:
                    raise CommandError(f"InboundXMLLabRecord not found: {record_id}") from exc
                source = f"record_id:{record_id}"
                results = route_lab_records([record], apply=apply, limit=limit)
            elif options.get("from_lab_records"):
                source = "from_lab_records"
                results = route_lab_records(
                    InboundXMLLabRecord.objects.all(),
                    apply=apply,
                    limit=limit,
                )
            else:
                target = Path(options.get("path") or DEFAULT_FIXTURE_DIR)
                if not target.exists():
                    raise CommandError(f"Path not found: {target}")
                source = f"path:{target}"
                results = route_path_via_persistence_lab(target, apply=apply, limit=limit)
        except FileNotFoundError as exc:
            raise CommandError(str(exc)) from exc

        report = build_workflow_lab_report(results, dry_run=not apply, source=source)

        if options.get("json_flag"):
            self.stdout.write(json.dumps(report, indent=2, sort_keys=True, default=str))
            return

        self.stdout.write(
            "DGII inbound workflow lab (NON_PRODUCTION_LAB_ONLY — NOT_DGII_COMPLIANT)"
        )
        self.stdout.write("=" * 60)
        self.stdout.write("NOT_DGII_COMPLIANT")
        self.stdout.write(LAB_MODE)
        self.stdout.write("certification_evidence=false")
        self.stdout.write("dgii_submission_allowed=false")
        self.stdout.write("track_id=null")
        self.stdout.write("dgii_call_made=false")
        self.stdout.write(f"synthetic_marker: {SYNTHETIC_SAMPLE_MARKER}")
        self.stdout.write(f"dry_run: {report['dry_run']}")
        self.stdout.write(f"apply_lab_workflow: {report['apply_lab_workflow']}")
        self.stdout.write(f"source: {report['source']}")
        self.stdout.write(f"result_count: {report['result_count']}")
        self.stdout.write(f"applied_count: {report['applied_count']}")
        self.stdout.write(f"route_counts: {report['route_counts']}")
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
        if not options.get("summary_only"):
            self.stdout.write("")
            for item in report["results"]:
                name = item.get("filename") or str(item.get("raw_sha256", ""))[:12]
                self.stdout.write(
                    f"- {name}: route={item.get('route')} "
                    f"status={item.get('status')} reason={item.get('reason')} "
                    f"applied={item.get('applied', False)}"
                )
        self.stdout.write("")
        self.stdout.write(
            "Lab workflow routes are not fiscal acceptance. No network call. "
            "No DGII submission. NOT certification evidence."
        )
