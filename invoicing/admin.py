from django.contrib import admin

from .models import Invoice, InvoiceLine


class InvoiceLineInline(admin.TabularInline):
    model = InvoiceLine
    extra = 1


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    inlines = [InvoiceLineInline]
    list_display = ("internal_code", "customer", "lifecycle_status", "grand_total", "issue_date", "created_at")
    search_fields = ("internal_code", "official_ncf", "official_encf")
    list_filter = ("lifecycle_status", "invoice_direction")


@admin.register(InvoiceLine)
class InvoiceLineAdmin(admin.ModelAdmin):
    list_display = ("invoice", "description", "quantity", "unit_price", "line_total")
