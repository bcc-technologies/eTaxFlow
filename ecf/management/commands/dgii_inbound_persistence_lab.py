import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from ecf.dgii.inbound_lab import DEFAULT_FIXTURE_DIR, SYNTHETIC_SAMPLE_MARKER
from ecf.dgii.inbound_persistence_lab import (
    LAB_MODE,
    analyze_path_payloads,
    build_persistence_lab_report,
    persist_path,
)


class Command(BaseCommand):
    help = (
        "Non-production inbound persistence lab. Dry-run by default. "
        "Writes only InboundXMLLabRecord when --persist-lab-records is set. "
        "No DGII calls, no TrackId, not certification evidence."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--path",
            default=str(DEFAULT_FIXTURE_DIR),
            help="Fixture file or directory (default: tests/fixtures/dgii/inbound_lab/)",
        )
        parser.add_argument("--json", action="store_true", dest="json_flag")
        parser.add_argument(
            "--persist-lab-records",
            action="store_true",
            dest="persist_lab_records",
            help="Write InboundXMLLabRecord rows (off by default; dry-run otherwise).",
        )
        parser.add_argument(
            "--store-raw-lab-xml",
            action="store_true",
            dest="store_raw_lab_xml",
            help="Store raw XML text on lab rows (off by default).",
        )
        parser.add_argument(
            "--allow-duplicates",
            action="store_true",
            dest="allow_duplicates",
            help="Accepted but unique raw_sha256 still upserts; no true duplicates.",
        )
        parser.add_argument(
            "--summary-only",
            action="store_true",
            dest="summary_only",
            help="Print summary without per-file details (ignored with --json).",
        )

    def handle(self, *args, **options):
        target = Path(options["path"])
        if not target.exists():
            raise CommandError(f"Path not found: {target}")

        persist = bool(options.get("persist_lab_records"))
        store_raw = bool(options.get("store_raw_lab_xml"))
        allow_duplicates = bool(options.get("allow_duplicates"))

        try:
            if persist:
                results = persist_path(
                    target,
                    store_raw_xml=store_raw,
                    allow_duplicates=allow_duplicates,
                )
            else:
                results = analyze_path_payloads(target)
        except FileNotFoundError as exc:
            raise CommandError(str(exc)) from exc

        report = build_persistence_lab_report(
            results,
            dry_run=not persist,
            store_raw_xml=store_raw,
        )

        if options.get("json_flag"):
            self.stdout.write(json.dumps(report, indent=2, sort_keys=True, default=str))
            return

        self.stdout.write(
            "DGII inbound persistence lab (NON_PRODUCTION_LAB_ONLY — NOT_DGII_COMPLIANT)"
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
        self.stdout.write(f"persist_lab_records: {report['persist_lab_records']}")
        self.stdout.write(f"store_raw_lab_xml: {report['store_raw_lab_xml']}")
        self.stdout.write(f"result_count: {report['result_count']}")
        self.stdout.write(f"created_count: {report['created_count']}")
        self.stdout.write(f"updated_count: {report['updated_count']}")
        self.stdout.write(f"workflow_lab_available: {report['workflow_lab_available']}")
        self.stdout.write(f"workflow_command: {report['workflow_command']}")
        self.stdout.write(f"workflow_status: {report['workflow_status']}")
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
        self.stdout.write(f"final_go_no_go_lab_available: {report['final_go_no_go_lab_available']}")
        self.stdout.write(f"final_go_no_go_command: {report['final_go_no_go_command']}")
        self.stdout.write(f"final_go_no_go_status: {report['final_go_no_go_status']}")
        if not options.get("summary_only"):
            self.stdout.write("")
            for item in report["results"]:
                name = item.get("filename") or item.get("raw_sha256", "")[:12]
                self.stdout.write(
                    f"- {name}: type={item.get('document_type')} "
                    f"sha256={str(item.get('raw_sha256', ''))[:12]}... "
                    f"created={item.get('created')} updated={item.get('updated')} "
                    f"raw_xml={item.get('persisted_raw_xml', False)}"
                )
        self.stdout.write("")
        self.stdout.write(
            "Lab records are not fiscal documents. No network call. "
            "No DGII submission. NOT certification evidence."
        )
