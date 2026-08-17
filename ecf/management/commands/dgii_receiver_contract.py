import json

from django.core.management.base import BaseCommand

from ecf.dgii.receiver import get_receiver_contract_metadata


class Command(BaseCommand):
    help = (
        "Print internal DGII receiver contract support matrix. "
        "Design-only; no network calls or database mutation."
    )

    def add_arguments(self, parser):
        parser.add_argument("--json", action="store_true", dest="json_flag")

    def handle(self, *args, **options):
        meta = get_receiver_contract_metadata()
        if options.get("json_flag"):
            self.stdout.write(json.dumps(meta, indent=2, sort_keys=True))
            return

        self.stdout.write("DGII receiver contract (DESIGN_ONLY — NOT_DGII_COMPLIANT)")
        self.stdout.write("=" * 60)
        self.stdout.write(f"public_endpoints_enabled: {meta['public_endpoints_enabled']}")
        self.stdout.write(f"receiver_processing_enabled: {meta['receiver_processing_enabled']}")
        self.stdout.write(f"supported_roots: {', '.join(meta['supported_roots'])}")
        self.stdout.write(f"signature_verification: {meta['signature_verification']}")
        self.stdout.write(f"persistence: {meta['persistence']}")
        self.stdout.write(f"readiness_status: {meta['readiness_status']}")
        self.stdout.write(f"compliance_status: {meta['compliance_status']}")
        self.stdout.write(f"dgii_submission_allowed: {meta['dgii_submission_allowed']}")
        self.stdout.write(f"track_id_creation: {meta['track_id_creation']}")
        self.stdout.write("No network call. No DGII submission. NOT certification evidence.")
