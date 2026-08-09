from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from ecf.services.internal_xml_documents import generate_internal_xml_document
from .models import Invoice, InvoiceLine, ProductService


class InvoiceLineInline(admin.TabularInline):
    model = InvoiceLine
    extra = 1
    readonly_fields = ("item_code_snapshot", "item_name_snapshot", "unit_snapshot", "tax_rate_snapshot", "currency_snapshot")


@admin.register(ProductService)
class ProductServiceAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "item_type", "default_unit", "default_tax_rate", "default_unit_price", "is_active")
    search_fields = ("code", "name")
    list_filter = ("item_type", "is_active")


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    inlines = [InvoiceLineInline]
    list_display = (
        "internal_code",
        "invoice_direction",
        "customer",
        "lifecycle_status",
        "currency",
        "issue_date",
        "due_date",
        "grand_total",
        "official_ncf",
        "official_encf",
        "created_at",
    )
    search_fields = (
        "internal_code",
        "customer__legal_name",
        "customer__commercial_name",
        "customer__rnc_or_id",
        "official_ncf",
        "official_encf",
    )
    list_filter = ("invoice_direction", "lifecycle_status", "currency", "issue_date", "created_at")
    readonly_fields = ("subtotal", "tax_total", "discount_total", "grand_total")
    actions = [
        "action_mark_reviewed",
        "action_approve_invoices",
        "action_mark_issued",
        "action_archive_invoices",
        "action_generate_internal_xml_drafts",
    ]

    def get_readonly_fields(self, request, obj=None):
        readonly = list(self.readonly_fields)
        if obj is not None:
            readonly.append("internal_code")
        return readonly

    def _perform_action(self, request, queryset, action_func, success_message):
        errors = []
        for invoice in queryset:
            try:
                action_func(invoice)
            except ValidationError as exc:
                errors.append(f"{invoice.internal_code}: {exc.message}")
        if errors:
            self.message_user(request, _("Some invoices could not be updated:"), level=messages.ERROR)
            for error in errors:
                self.message_user(request, error, level=messages.ERROR)
        else:
            self.message_user(request, success_message, level=messages.SUCCESS)

    def action_mark_reviewed(self, request, queryset):
        self._perform_action(request, queryset, lambda invoice: invoice.mark_reviewed(), "Selected invoices were marked as reviewed.")
    action_mark_reviewed.short_description = "Mark selected invoices as reviewed"

    def action_approve_invoices(self, request, queryset):
        approver = request.user
        self._perform_action(request, queryset, lambda invoice: invoice.approve_invoice(approver), "Selected invoices were approved.")
    action_approve_invoices.short_description = "Approve selected invoices"

    def action_mark_issued(self, request, queryset):
        self._perform_action(request, queryset, lambda invoice: invoice.issue_invoice(), "Selected invoices were marked as issued.")
    action_mark_issued.short_description = "Mark selected invoices as issued"

    def action_archive_invoices(self, request, queryset):
        self._perform_action(request, queryset, lambda invoice: invoice.archive_invoice(), "Selected invoices were archived.")
    action_archive_invoices.short_description = "Archive selected invoices"

    def action_generate_internal_xml_drafts(self, request, queryset):
        self._perform_action(
            request,
            queryset,
            lambda invoice: generate_internal_xml_document(invoice, created_by=request.user),
            "Generated internal XML draft documents for selected invoices.",
        )
    action_generate_internal_xml_drafts.short_description = "Generate internal XML draft documents"


@admin.register(InvoiceLine)
class InvoiceLineAdmin(admin.ModelAdmin):
    list_display = ("invoice", "description", "quantity", "unit_price", "line_total")
