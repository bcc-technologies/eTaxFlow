from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from ecf.services.internal_xml_documents import generate_internal_xml_document
from ecf.services.signing_placeholder import (
    SigningPlaceholderError,
    prepare_signing_placeholder,
)
from fiscal.services.encf_sequences import ENCFAllocationError, allocate_next_encf
from .models import Invoice, InvoiceLine, ProductService


class InvoiceLineInline(admin.TabularInline):
    model = InvoiceLine
    extra = 1
    fields = (
        "line_order",
        "product_service",
        "description",
        "quantity",
        "unit",
        "unit_price",
        "discount_amount",
        "tax_rate_ref",
        "billing_indicator",
        "tax_rate",
        "tax_amount",
        "line_total",
        "item_code_snapshot",
        "item_name_snapshot",
        "unit_snapshot",
        "tax_rate_snapshot",
        "currency_snapshot",
    )
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
        "income_type",
        "payment_type",
        "sequence_expiration_date",
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
    list_filter = (
        "invoice_direction",
        "lifecycle_status",
        "currency",
        "issue_date",
        "income_type",
        "payment_type",
        "created_at",
    )
    readonly_fields = ("subtotal", "tax_total", "discount_total", "grand_total")
    autocomplete_fields = ("income_type", "payment_type", "fiscal_document_type_ref", "customer", "issuer")
    actions = [
        "action_mark_reviewed",
        "action_approve_invoices",
        "action_mark_issued",
        "action_archive_invoices",
        "action_generate_internal_xml_drafts",
        "action_allocate_demo_encf",
        "action_prepare_signing_placeholder",
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

    def action_allocate_demo_encf(self, request, queryset):
        """Explicit demo-only allocation; never silent production allocation."""
        errors = []
        allocated = []
        for invoice in queryset:
            try:
                value = allocate_next_encf(
                    invoice,
                    actor=request.user,
                    allow_demo=True,
                )
                allocated.append(f"{invoice.internal_code} -> {value}")
            except (ValidationError, ENCFAllocationError) as exc:
                msgs = getattr(exc, "messages", None) or [str(exc)]
                errors.append(f"{invoice.internal_code}: {'; '.join(msgs)}")
        if allocated:
            self.message_user(
                request,
                _("Allocated demo eNCF (NOT DGII-authorized): ") + "; ".join(allocated),
                level=messages.SUCCESS,
            )
        if errors:
            self.message_user(
                request,
                _("Some demo eNCF allocations failed:"),
                level=messages.ERROR,
            )
            for error in errors:
                self.message_user(request, error, level=messages.ERROR)
    action_allocate_demo_encf.short_description = (
        "Allocate demo eNCF from configured range (NOT DGII-authorized)"
    )

    def action_prepare_signing_placeholder(self, request, queryset):
        """Prepare FechaHoraFirma placeholder only — never real signing/submission."""
        errors = []
        prepared = []
        for invoice in queryset:
            try:
                before_status = invoice.lifecycle_status
                ecf = prepare_signing_placeholder(
                    invoice,
                    actor=request.user,
                    note="Admin action: local signing placeholder only; no real digital signature.",
                )
                invoice.refresh_from_db()
                if invoice.lifecycle_status != before_status:
                    errors.append(
                        f"{invoice.internal_code}: lifecycle_status unexpectedly changed "
                        f"from {before_status} to {invoice.lifecycle_status}"
                    )
                    continue
                prepared.append(
                    f"{invoice.internal_code} -> ECF#{ecf.pk} ({ecf.signing_status})"
                )
            except (ValidationError, SigningPlaceholderError) as exc:
                msgs = getattr(exc, "messages", None) or [str(exc)]
                errors.append(f"{invoice.internal_code}: {'; '.join(msgs)}")
        if prepared:
            self.message_user(
                request,
                _("Prepared signing placeholder (NOT real signing): ") + "; ".join(prepared),
                level=messages.SUCCESS,
            )
        if errors:
            self.message_user(
                request,
                _("Some signing placeholder preparations failed:"),
                level=messages.ERROR,
            )
            for error in errors:
                self.message_user(request, error, level=messages.ERROR)
    action_prepare_signing_placeholder.short_description = (
        "Prepare signing placeholder (NOT real digital signing)"
    )


@admin.register(InvoiceLine)
class InvoiceLineAdmin(admin.ModelAdmin):
    list_display = (
        "invoice",
        "description",
        "quantity",
        "unit_price",
        "billing_indicator",
        "line_total",
    )
    list_filter = ("billing_indicator",)
    autocomplete_fields = ("billing_indicator", "product_service", "unit", "tax_rate_ref")
