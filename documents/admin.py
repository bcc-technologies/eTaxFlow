from django.contrib import admin

from .models import Document


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("internal_code", "document_kind", "status", "original_filename", "created_at")
    search_fields = ("internal_code", "original_filename")
    list_filter = ("status", "document_kind", "document_direction")
