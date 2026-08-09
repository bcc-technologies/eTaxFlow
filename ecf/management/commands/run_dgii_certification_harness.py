import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from ecf.dgii.certification.case_runner import run_certification_harness
from ecf.dgii.certification.test_set_importer import load_test_set


DEFAULT_SYNTHETIC_FIXTURE = Path("tests/fixtures/dgii/synthetic_certification_case.json")


class Command(BaseCommand):
    help = (
        "Run synthetic/sanitized DGII certification cases locally. "
        "Requires --no-submit; never calls DGII or creates real TrackId values."
    )

    def add_arguments(self, parser):
        parser.add_argument("--synthetic", action="store_true", dest="synthetic")
        parser.add_argument("--fixture", dest="fixture")
        parser.add_argument(
            "--mode",
            choices=["unsigned", "sandbox-signed"],
            default="unsigned",
        )
        parser.add_argument(
            "--no-submit",
            action="store_true",
            dest="no_submit",
            help="Required safety flag; the harness has no submit implementation.",
        )
        parser.add_argument("--json", action="store_true", dest="json_flag")

    def handle(self, *args, **options):
        if not options.get("no_submit"):
            raise CommandError("Certification harness requires explicit --no-submit.")
        fixture = options.get("fixture")
        if bool(options.get("synthetic")) == bool(fixture):
            raise CommandError("Provide exactly one of --synthetic or --fixture.")
        fixture_path = DEFAULT_SYNTHETIC_FIXTURE if options.get("synthetic") else Path(fixture)
        try:
            payload = load_test_set(fixture_path)
            report = run_certification_harness(
                payload,
                mode=options.get("mode") or "unsigned",
                no_submit=True,
            )
        except (OSError, ValueError) as exc:
            raise CommandError(str(exc)) from exc

        if options.get("json_flag"):
            self.stdout.write(json.dumps(report, indent=2, sort_keys=True, default=str))
            return
        self.stdout.write("Local DGII certification harness")
        self.stdout.write("=" * 60)
        self.stdout.write(f"fixture_kind: {report['fixture_kind']}")
        self.stdout.write(f"mode: {report['mode']}")
        self.stdout.write(f"harness_status: {report['harness_status']}")
        self.stdout.write(f"no_submit: {report['no_submit']}")
        self.stdout.write(f"submitted: {report['submitted']}")
        self.stdout.write(f"dgii_call_made: {report['dgii_call_made']}")
        self.stdout.write(f"track_ids: {report['track_ids']}")
        self.stdout.write(f"compliance_status: {report['compliance_status']}")
        for case in report["cases"]:
            self.stdout.write(
                f"case {case['case_id']}: invoice={case['invoice_internal_code']} "
                f"local_validation_passed={case['local_validation_passed']} "
                f"expected_unsigned_limitation={case['expected_unsigned_limitation']}"
            )
        for note in report["notes"]:
            self.stdout.write(f"note: {note}")
