from django.contrib import admin

from .models import ECFDocument, InboundXMLLabRecord


@admin.register(ECFDocument)
class ECFDocumentAdmin(admin.ModelAdmin):
    list_display = (
        "invoice",
        "environment",
        "signing_status",
        "signing_mode",
        "signature_datetime",
        "signing_attempted_at",
        "signing_completed_at",
        "dgii_status",
        "dgii_track_id",
        "created_at",
    )
    search_fields = ("invoice__internal_code", "dgii_track_id")
    list_filter = ("environment", "signing_status", "signing_mode", "dgii_status")
    readonly_fields = (
        "signing_status",
        "signing_mode",
        "signature_datetime",
        "signature_digest_algorithm",
        "signature_method",
        "signature_reference_uri",
        "signature_placeholder_note",
        "signed_by",
        "signing_attempted_at",
        "signing_completed_at",
        "created_at",
        "updated_at",
    )
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "invoice",
                    "environment",
                    "ecf_type",
                    "xml_unsigned_file",
                    "xml_signed_file",
                    "printed_representation_file",
                    "dgii_track_id",
                    "dgii_status",
                    "dgii_status_message",
                    "submitted_at",
                    "last_status_check_at",
                )
            },
        ),
        (
            "Signing placeholder (NOT real digital signing)",
            {
                "fields": (
                    "signing_status",
                    "signing_mode",
                    "signature_datetime",
                    "signature_digest_algorithm",
                    "signature_method",
                    "signature_reference_uri",
                    "signature_placeholder_note",
                    "signed_by",
                    "signing_attempted_at",
                    "signing_completed_at",
                    "created_at",
                    "updated_at",
                ),
                "description": (
                    "FechaHoraFirma may be represented via signature_datetime as a local "
                    "placeholder only. Real XMLDSig, certificates, and private keys are not "
                "implemented. Signature remains missing until a future signing phase."
            ),
            },
        ),
    )


@admin.register(InboundXMLLabRecord)
class InboundXMLLabRecordAdmin(admin.ModelAdmin):
    """Read-only lab records. No submit/approve/TrackId actions."""

    list_display = (
        "filename",
        "document_type",
        "raw_sha256",
        "signature_present",
        "local_xsd_valid",
        "lab_mode",
        "compliance_status",
        "created_at",
    )
    search_fields = ("raw_sha256", "filename", "document_type")
    list_filter = ("document_type", "signature_present", "local_xsd_valid", "lab_mode")
    readonly_fields = (
        "created_at",
        "updated_at",
        "source_path",
        "filename",
        "raw_sha256",
        "raw_size_bytes",
        "root_tag",
        "document_type",
        "classification_status",
        "signature_present",
        "signature_verification_status",
        "signature_verified",
        "production_signature_ready",
        "schema_validation_scope",
        "xsd_path",
        "xsd_available",
        "xsd_compiled",
        "local_xsd_valid",
        "xsd_error_count",
        "errors_json",
        "persisted_raw_xml",
        "raw_xml_text",
        "compliance_status",
        "dgii_submission_allowed",
        "certification_evidence",
        "track_id",
        "dgii_call_made",
        "lab_mode",
    )
    fieldsets = (
        (
            "NON_PRODUCTION_LAB_ONLY — not a fiscal document, not DGII evidence",
            {
                "description": (
                    "These rows are synthetic inbound lab analysis only. "
                    "They are not received e-CF documents. No submit, approve, "
                    "certify, or TrackId actions exist."
                ),
                "fields": (
                    "lab_mode",
                    "compliance_status",
                    "dgii_submission_allowed",
                    "certification_evidence",
                    "track_id",
                    "dgii_call_made",
                    "filename",
                    "source_path",
                    "raw_sha256",
                    "raw_size_bytes",
                    "root_tag",
                    "document_type",
                    "classification_status",
                    "signature_present",
                    "signature_verification_status",
                    "signature_verified",
                    "production_signature_ready",
                    "schema_validation_scope",
                    "xsd_path",
                    "xsd_available",
                    "xsd_compiled",
                    "local_xsd_valid",
                    "xsd_error_count",
                    "errors_json",
                    "persisted_raw_xml",
                    "raw_xml_text",
                    "created_at",
                    "updated_at",
                ),
            },
        ),
    )
    actions = None

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
