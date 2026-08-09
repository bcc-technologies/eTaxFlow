from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Invoice(models.Model):
    INVOICE_DIRECTIONS = [("OUTBOUND", "Outbound"), ("INBOUND", "Inbound")]
    LIFECYCLE_STATUSES = [
        ("DRAFT", "Draft"),
        ("REVIEWED", "Reviewed"),
        ("APPROVED", "Approved"),
        ("ISSUED", "Issued"),
        ("CANCELLED", "Cancelled"),
        ("ARCHIVED", "Archived"),
    ]

    internal_code = models.CharField(max_length=50, unique=True)
    issuer = models.ForeignKey("organizations.Organization", on_delete=models.PROTECT, related_name="issued_invoices")
    customer = models.ForeignKey("contacts.Contact", on_delete=models.PROTECT, related_name="invoices")
    invoice_direction = models.CharField(max_length=20, choices=INVOICE_DIRECTIONS, default="OUTBOUND")
    lifecycle_status = models.CharField(max_length=20, choices=LIFECYCLE_STATUSES, default="DRAFT")
    currency = models.CharField(max_length=10, default="DOP")
    issue_date = models.DateField()
    due_date = models.DateField(null=True, blank=True)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    tax_total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    discount_total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    grand_total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    official_ncf = models.CharField(max_length=50, null=True, blank=True)
    official_encf = models.CharField(max_length=50, null=True, blank=True)
    fiscal_document_type = models.CharField(max_length=50, null=True, blank=True)
    fiscal_document_type_ref = models.ForeignKey(
        "fiscal.FiscalDocumentType",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="invoices",
    )
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_invoices")
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="approved_invoices")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    VALID_TRANSITIONS = {
        "DRAFT": {"REVIEWED", "CANCELLED"},
        "REVIEWED": {"APPROVED", "CANCELLED"},
        "APPROVED": {"ISSUED", "CANCELLED"},
        "ISSUED": {"ARCHIVED"},
        "CANCELLED": {"ARCHIVED"},
        "ARCHIVED": set(),
    }

    def save(self, *args, **kwargs):
        old = Invoice.objects.filter(pk=self.pk).first() if self.pk else None
        if old and old.lifecycle_status == "ISSUED" and self.lifecycle_status == "ISSUED":
            if old.customer_id != self.customer_id:
                raise ValidationError("Issued invoices cannot change customer.")
            if old.issue_date != self.issue_date:
                raise ValidationError("Issued invoices cannot change issue date.")
            if old.official_ncf != self.official_ncf:
                raise ValidationError("Issued invoices cannot change official NCF.")
            if old.official_encf != self.official_encf:
                raise ValidationError("Issued invoices cannot change official e-NCF.")
            if old.fiscal_document_type_ref_id != self.fiscal_document_type_ref_id:
                raise ValidationError("Issued invoices cannot change fiscal document type.")

        if old and old.lifecycle_status != self.lifecycle_status:
            from audit.models import AuditEvent

            actor = getattr(self, "_transition_actor", self.created_by)
            AuditEvent.objects.create(
                event_type="invoice_status_changed",
                entity_type="Invoice",
                entity_id=self.pk,
                message=f"Invoice status changed from {old.lifecycle_status} to {self.lifecycle_status}",
                metadata={"from_status": old.lifecycle_status, "to_status": self.lifecycle_status},
                actor=actor,
            )
            if hasattr(self, "_transition_actor"):
                del self._transition_actor
        super().save(*args, **kwargs)
        self._recalculate_totals()

    def _recalculate_totals(self):
        lines = self.lines.all()
        subtotal = sum((line.quantity * line.unit_price for line in lines), Decimal("0.00"))
        discount_total = sum((line.discount_amount for line in lines), Decimal("0.00"))
        tax_total = sum((line.tax_amount for line in lines), Decimal("0.00"))
        grand_total = subtotal - discount_total + tax_total
        self.subtotal = subtotal
        self.tax_total = tax_total
        self.discount_total = discount_total
        self.grand_total = grand_total
        Invoice.objects.filter(pk=self.pk).update(
            subtotal=subtotal,
            tax_total=tax_total,
            discount_total=discount_total,
            grand_total=grand_total,
        )

    def __str__(self):
        return self.internal_code

    def _transition_status(self, to_status, actor=None, require_approver=False):
        if to_status not in self.VALID_TRANSITIONS.get(self.lifecycle_status, set()):
            raise ValidationError(
                f"Cannot transition invoice from {self.lifecycle_status} to {to_status}."
            )

        if to_status == "APPROVED" and require_approver and not actor:
            raise ValidationError("Approval requires an approving user.")

        if to_status == "ISSUED":
            if not self.lines.exists():
                raise ValidationError("Issued invoice must have at least one invoice line.")
            if self.grand_total <= Decimal("0.00"):
                raise ValidationError("Issued invoice must have a positive grand total.")

        self.lifecycle_status = to_status
        if to_status == "APPROVED":
            self.approved_by = actor
        if actor is not None:
            self._transition_actor = actor
        self.save()

    def mark_reviewed(self):
        self._transition_status("REVIEWED")

    def approve_invoice(self, approving_user):
        self._transition_status("APPROVED", actor=approving_user, require_approver=True)

    def issue_invoice(self):
        self._transition_status("ISSUED")

    def cancel_invoice(self):
        self._transition_status("CANCELLED")

    def archive_invoice(self):
        self._transition_status("ARCHIVED")


class ProductService(models.Model):
    ITEM_TYPES = [("PRODUCT", "Product"), ("SERVICE", "Service")]

    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    item_type = models.CharField(max_length=20, choices=ITEM_TYPES, default="SERVICE")
    default_unit = models.ForeignKey(
        "fiscal.UnitOfMeasure",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="product_services",
    )
    default_tax_rate = models.ForeignKey(
        "fiscal.TaxRate",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="product_services",
    )
    default_unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} - {self.name}"


class InvoiceLine(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="lines")
    line_order = models.PositiveIntegerField(default=1)
    product_service = models.ForeignKey(
        "invoicing.ProductService",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="invoice_lines",
    )
    unit = models.ForeignKey(
        "fiscal.UnitOfMeasure",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="invoice_lines",
    )
    tax_rate_ref = models.ForeignKey(
        "fiscal.TaxRate",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="invoice_lines",
    )
    description = models.CharField(max_length=255)
    item_code_snapshot = models.CharField(max_length=50, null=True, blank=True)
    item_name_snapshot = models.CharField(max_length=255, null=True, blank=True)
    unit_snapshot = models.CharField(max_length=20, null=True, blank=True)
    tax_rate_snapshot = models.CharField(max_length=50, null=True, blank=True)
    currency_snapshot = models.CharField(max_length=10, null=True, blank=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("1.00"))
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    line_total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))

    def save(self, *args, **kwargs):
        if self.invoice and self.invoice.lifecycle_status == "ISSUED" and not getattr(self, "_allow_issued_edit", False):
            raise ValidationError("Cannot edit invoice lines for an issued invoice.")

        if self.product_service:
            if not self.item_code_snapshot:
                self.item_code_snapshot = self.product_service.code
            if not self.item_name_snapshot:
                self.item_name_snapshot = self.product_service.name
            if not self.unit and self.product_service.default_unit:
                self.unit = self.product_service.default_unit
            if self.unit and not self.unit_snapshot:
                self.unit_snapshot = self.unit.code
            if self.product_service.default_unit_price and self.unit_price == Decimal("0.00"):
                self.unit_price = self.product_service.default_unit_price
            if self.product_service.default_tax_rate and self.tax_rate == Decimal("0.00"):
                self.tax_rate = self.product_service.default_tax_rate.rate
            if self.product_service.default_tax_rate and not self.tax_rate_snapshot:
                self.tax_rate_snapshot = self.product_service.default_tax_rate.code

        if self.unit and not self.unit_snapshot:
            self.unit_snapshot = self.unit.code
        if self.tax_rate_ref:
            if self.tax_rate == Decimal("0.00"):
                self.tax_rate = self.tax_rate_ref.rate
            if not self.tax_rate_snapshot:
                self.tax_rate_snapshot = self.tax_rate_ref.code
        if self.invoice and not self.currency_snapshot:
            self.currency_snapshot = self.invoice.currency

        if self.tax_amount == Decimal("0.00") and self.tax_rate != Decimal("0.00"):
            self.tax_amount = (self.quantity * self.unit_price) * (self.tax_rate / Decimal("100"))

        self.line_total = (self.quantity * self.unit_price) - self.discount_amount + self.tax_amount

        super().save(*args, **kwargs)
        self.invoice._recalculate_totals()

    class Meta:
        ordering = ["line_order"]

    def __str__(self):
        return self.description
