from django.contrib import admin

from .models import FiscalDocumentType, InternalDocumentCode, TaxRate, UnitOfMeasure


@admin.register(InternalDocumentCode)
class InternalDocumentCodeAdmin(admin.ModelAdmin):
    list_display = ("prefix", "year", "last_number")
    search_fields = ("prefix",)


@admin.register(FiscalDocumentType)
class FiscalDocumentTypeAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "name",
        "document_group",
        "direction",
        "is_electronic",
        "is_active",
    )
    list_filter = ("document_group", "direction", "is_electronic", "is_active")
    search_fields = ("code", "name")


@admin.register(TaxRate)
class TaxRateAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "rate", "tax_type", "is_default", "is_active")
    list_filter = ("tax_type", "is_default", "is_active")
    search_fields = ("code", "name")


@admin.register(UnitOfMeasure)
class UnitOfMeasureAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "symbol", "is_active")
    list_filter = ("is_active",)
    search_fields = ("code", "name")
