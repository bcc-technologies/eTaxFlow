from django.contrib import admin

from .models import Contact


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ("commercial_name", "legal_name", "contact_type", "rnc_or_id", "email", "is_active", "created_at")
    search_fields = ("legal_name", "commercial_name", "rnc_or_id")
    list_filter = ("contact_type", "is_active")
