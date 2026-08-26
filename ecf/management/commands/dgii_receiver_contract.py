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
        self.stdout.write(f"schema_validation: {meta['schema_validation']}")
        self.stdout.write(
            f"local_inbound_schema_lab_available: {meta['local_inbound_schema_lab_available']}"
        )
        self.stdout.write(
            f"local_inbound_signature_lab_available: {meta['local_inbound_signature_lab_available']}"
        )
        self.stdout.write(f"signature_verification_scope: {meta['signature_verification_scope']}")
        self.stdout.write(f"signature_verification_command: {meta['signature_verification_command']}")
        self.stdout.write(f"production_signature_ready: {meta['production_signature_ready']}")
        self.stdout.write(f"schema_validation_scope: {meta['schema_validation_scope']}")
        self.stdout.write(f"schema_validation_command: {meta['schema_validation_command']}")
        self.stdout.write(
            f"schema_validation_certification_evidence: {meta['schema_validation_certification_evidence']}"
        )
        self.stdout.write(f"supported_schema_roots: {', '.join(meta['supported_schema_roots'])}")
        self.stdout.write(f"inbound_xml_lab_available: {meta['inbound_xml_lab_available']}")
        self.stdout.write(
            f"non_production_inbound_persistence_lab_available: {meta['non_production_inbound_persistence_lab_available']}"
        )
        self.stdout.write(f"persistence_scope: {meta['persistence_scope']}")
        self.stdout.write(f"persistence_command: {meta['persistence_command']}")
        self.stdout.write(f"production_persistence_ready: {meta['production_persistence_ready']}")
        self.stdout.write(
            f"public_route_persistence_enabled: {meta['public_route_persistence_enabled']}"
        )
        self.stdout.write(f"raw_xml_storage_default: {meta['raw_xml_storage_default']}")
        self.stdout.write(
            f"non_production_inbound_workflow_lab_available: {meta['non_production_inbound_workflow_lab_available']}"
        )
        self.stdout.write(f"workflow_scope: {meta['workflow_scope']}")
        self.stdout.write(f"workflow_command: {meta['workflow_command']}")
        self.stdout.write(f"production_workflow_ready: {meta['production_workflow_ready']}")
        self.stdout.write(
            f"public_route_workflow_enabled: {meta['public_route_workflow_enabled']}"
        )
        self.stdout.write(
            f"fiscal_acceptance_workflow_enabled: {meta['fiscal_acceptance_workflow_enabled']}"
        )
        self.stdout.write(f"lab_mode: {meta['lab_mode']}")
        self.stdout.write(f"synthetic_fixtures_available: {meta['synthetic_fixtures_available']}")
        self.stdout.write(f"certification_evidence: {meta['certification_evidence']}")
        self.stdout.write(f"persistence: {meta['persistence']}")
        self.stdout.write(f"readiness_status: {meta['readiness_status']}")
        self.stdout.write(f"compliance_status: {meta['compliance_status']}")
        self.stdout.write(f"dgii_submission_allowed: {meta['dgii_submission_allowed']}")
        self.stdout.write(f"track_id_creation: {meta['track_id_creation']}")
        self.stdout.write("No network call. No DGII submission. NOT certification evidence.")
