import json

from django.core.management.base import BaseCommand

from ecf.dgii.endpoints import get_software_registration_metadata


class Command(BaseCommand):
    help = (
        "Print planned DGII software registration metadata and composed endpoint URLs. "
        "Design-only; no network calls or database mutation."
    )

    def add_arguments(self, parser):
        parser.add_argument("--json", action="store_true", dest="json_flag")

    def handle(self, *args, **options):
        meta = get_software_registration_metadata()
        if options.get("json_flag"):
            self.stdout.write(json.dumps(meta, indent=2, sort_keys=True))
            return

        self.stdout.write("DGII endpoint plan (DESIGN_ONLY — NOT_DGII_COMPLIANT)")
        self.stdout.write("=" * 60)
        self.stdout.write(f"software_type: {meta['software_type']}")
        self.stdout.write(f"software_name: {meta['software_name']}")
        self.stdout.write(f"software_version: {meta['software_version']}")
        self.stdout.write(f"public_base_url: {meta['public_base_url'] or '(blank — BLOCKED)'}")
        self.stdout.write(f"endpoints_enabled: {meta['endpoints_enabled']}")
        self.stdout.write(f"readiness_status: {meta['readiness_status']}")
        self.stdout.write(f"url_status: {meta['url_status']}")
        self.stdout.write(f"deployment_readiness_status: {meta['deployment_readiness_status']}")
        self.stdout.write(f"staging_dns_status: {meta['staging_dns_status']}")
        self.stdout.write(f"staging_ssl_status: {meta['staging_ssl_status']}")
        self.stdout.write(
            f"staging_external_reachability_status: {meta['staging_external_reachability_status']}"
        )
        self.stdout.write(f"endpoint_routes_status: {meta['endpoint_routes_status']}")
        self.stdout.write(f"manual_verification_required: {meta['manual_verification_required']}")
        self.stdout.write(
            f"staging_evidence_lab_available: {meta['staging_evidence_lab_available']}"
        )
        self.stdout.write(f"staging_evidence_command: {meta['staging_evidence_command']}")
        self.stdout.write(f"staging_evidence_scope: {meta['staging_evidence_scope']}")
        self.stdout.write(f"staging_evidence_decision: {meta['staging_evidence_decision']}")
        self.stdout.write(f"production_staging_ready: {meta['production_staging_ready']}")
        self.stdout.write(f"external_dns_verified: {meta['external_dns_verified']}")
        self.stdout.write(f"external_tls_verified: {meta['external_tls_verified']}")
        self.stdout.write(
            f"external_disabled_routes_verified: {meta['external_disabled_routes_verified']}"
        )
        self.stdout.write(
            f"staging_manual_evidence_required: {meta['staging_manual_evidence_required']}"
        )
        self.stdout.write(f"certification_evidence: {meta['certification_evidence']}")
        self.stdout.write(
            f"certification_package_lab_available: {meta['certification_package_lab_available']}"
        )
        self.stdout.write(f"certification_package_command: {meta['certification_package_command']}")
        self.stdout.write(f"certification_package_scope: {meta['certification_package_scope']}")
        self.stdout.write(f"certification_package_status: {meta['certification_package_status']}")
        self.stdout.write(f"portal_submission_allowed: {meta['portal_submission_allowed']}")
        self.stdout.write(
            f"planned_portal_urls_available: {meta['planned_portal_urls_available']}"
        )
        self.stdout.write(
            f"public_base_url_externally_verified: {meta['public_base_url_externally_verified']}"
        )
        self.stdout.write(
            f"final_go_no_go_lab_available: {meta['final_go_no_go_lab_available']}"
        )
        self.stdout.write(f"final_go_no_go_command: {meta['final_go_no_go_command']}")
        self.stdout.write(f"final_inbound_audit_lab_available: {meta['final_inbound_audit_lab_available']}")
        self.stdout.write(f"final_inbound_audit_command: {meta['final_inbound_audit_command']}")
        self.stdout.write(f"final_audit_scope: {meta['final_audit_scope']}")
        self.stdout.write(f"final_review_scope: {meta['final_review_scope']}")
        self.stdout.write(f"final_decision: {meta['final_decision']}")
        self.stdout.write(
            f"endpoint_activation_allowed: {meta['endpoint_activation_allowed']}"
        )
        self.stdout.write(f"compliance_status: {meta['compliance_status']}")
        self.stdout.write(f"dgii_submission_allowed: {meta['dgii_submission_allowed']}")
        self.stdout.write("")
        self.stdout.write("Planned portal URLs:")
        if not meta["public_base_url"]:
            self.stdout.write("  URL Recepción: BLOCKED (no public base URL configured)")
            self.stdout.write("  URL Aprobación Comercial: BLOCKED")
            self.stdout.write("  URL Autenticación: BLOCKED")
        else:
            self.stdout.write(f"  URL Recepción: {meta['recepcion_url']}")
            self.stdout.write(f"  URL Aprobación Comercial: {meta['aprobacion_comercial_url']}")
            self.stdout.write(f"  URL Autenticación: {meta['autenticacion_url_template']}")
            if not meta["endpoints_enabled"]:
                self.stdout.write(
                    self.style.WARNING(
                        "  DESIGN_ONLY — ETAXFLOW_ENABLE_PUBLIC_DGII_ENDPOINTS is false."
                    )
                )
        self.stdout.write("")
        self.stdout.write(
            f"Example host (not configured): https://{meta['planned_host_example']}"
        )
        self.stdout.write("No network call. No DGII submission. NOT certification evidence.")
