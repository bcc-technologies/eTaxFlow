from django.contrib import admin

from .models import ECFDocument


@admin.register(ECFDocument)
class ECFDocumentAdmin(admin.ModelAdmin):
    list_display = ("invoice", "environment", "dgii_status", "dgii_track_id", "created_at")
    search_fields = ("invoice__internal_code", "dgii_track_id")
    list_filter = ("environment", "dgii_status")
