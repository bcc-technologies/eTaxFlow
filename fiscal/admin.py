from django.contrib import admin

from .models import InternalDocumentCode


@admin.register(InternalDocumentCode)
class InternalDocumentCodeAdmin(admin.ModelAdmin):
    list_display = ("prefix", "year", "last_number")
    search_fields = ("prefix",)
