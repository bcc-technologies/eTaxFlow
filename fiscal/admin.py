from django.contrib import admin

from .models import (
    BillingIndicator,
    ENCFSequenceRange,
    FiscalDocumentType,
    FiscalIncomeType,
    InternalDocumentCode,
    PaymentType,
    TaxRate,
    UnitOfMeasure,
)


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


@admin.register(FiscalIncomeType)
class FiscalIncomeTypeAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_active", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("code", "name")


@admin.register(PaymentType)
class PaymentTypeAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_active", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("code", "name")


@admin.register(BillingIndicator)
class BillingIndicatorAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_active", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("code", "name")


@admin.register(ENCFSequenceRange)
class ENCFSequenceRangeAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "issuer",
        "fiscal_document_type",
        "prefix",
        "start_number",
        "end_number",
        "next_number",
        "number_pad_width",
        "sequence_expiration_date",
        "environment",
        "source",
        "is_authorized_by_dgii",
        "is_active",
    )
    list_filter = (
        "issuer",
        "fiscal_document_type",
        "environment",
        "source",
        "is_authorized_by_dgii",
        "is_active",
    )
    search_fields = (
        "prefix",
        "notes",
        "issuer__legal_name",
        "issuer__commercial_name",
        "issuer__rnc",
    )
    autocomplete_fields = ("issuer", "fiscal_document_type")
    readonly_fields = ("created_at", "updated_at")
