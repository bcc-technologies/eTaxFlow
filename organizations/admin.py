from django.contrib import admin

from .models import Organization


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("commercial_name", "legal_name", "rnc", "email", "is_default_issuer", "created_at")
    search_fields = ("legal_name", "commercial_name", "rnc")
