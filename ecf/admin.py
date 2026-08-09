from django.contrib import admin

from .models import ECFDocument


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
