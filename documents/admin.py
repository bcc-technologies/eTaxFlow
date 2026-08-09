from django.contrib import admin

from .models import Document


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = (
        "internal_code",
        "document_direction",
        "document_kind",
        "source",
        "status",
        "related_contact",
        "issuer",
        "mime_type",
        "file_size",
        "created_at",
    )
    search_fields = (
        "internal_code",
        "original_filename",
        "sha256_hash",
        "related_contact__legal_name",
        "related_contact__commercial_name",
        "related_contact__rnc_or_id",
    )
    list_filter = ("document_direction", "document_kind", "source", "status", "created_at")

    def get_readonly_fields(self, request, obj=None):
        readonly = [
            "sha256_hash",
            "file_size",
            "mime_type",
            "original_filename",
            "internal_code",
        ]
        if obj is not None:
            return readonly
        return readonly
