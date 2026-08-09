from django.contrib import admin

from .models import ECFDocument


@admin.register(ECFDocument)
class ECFDocumentAdmin(admin.ModelAdmin):
    list_display = (
        "invoice",
        "environment",
        "dgii_status",
        "dgii_track_id",
        "signature_datetime",
        "created_at",
    )
    search_fields = ("invoice__internal_code", "dgii_track_id")
    list_filter = ("environment", "dgii_status")
    readonly_fields = ("signature_datetime",)
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
            "Signature placeholder (NOT implemented)",
            {
                "fields": ("signature_datetime",),
                "description": (
                    "signature_datetime is a placeholder for future FechaHoraFirma mapping only. "
                    "Digital signing, certificates, and private keys are not implemented."
                ),
            },
        ),
    )
