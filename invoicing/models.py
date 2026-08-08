from decimal import Decimal

from django.conf import settings
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
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_invoices")
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="approved_invoices")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        old = Invoice.objects.filter(pk=self.pk).first() if self.pk else None
        if old and old.lifecycle_status != self.lifecycle_status:
            from audit.models import AuditEvent

            AuditEvent.objects.create(
                event_type="invoice_status_changed",
                entity_type="Invoice",
                entity_id=self.pk,
                message=f"Invoice status changed from {old.lifecycle_status} to {self.lifecycle_status}",
                metadata={"from_status": old.lifecycle_status, "to_status": self.lifecycle_status},
                actor=self.created_by,
            )
        super().save(*args, **kwargs)
        self._recalculate_totals()

    def _recalculate_totals(self):
        lines = self.lines.all()
        subtotal = sum((line.quantity * line.unit_price for line in lines), Decimal("0.00"))
        discount_total = sum((line.discount_amount for line in lines), Decimal("0.00"))
        tax_total = sum((line.tax_amount for line in lines), Decimal("0.00"))
        grand_total = subtotal - discount_total + tax_total
        Invoice.objects.filter(pk=self.pk).update(
            subtotal=subtotal,
            tax_total=tax_total,
            discount_total=discount_total,
            grand_total=grand_total,
        )

    def __str__(self):
        return self.internal_code


class InvoiceLine(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="lines")
    description = models.CharField(max_length=255)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("1.00"))
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    line_total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    product_code = models.CharField(max_length=50, null=True, blank=True)
    service_type = models.CharField(max_length=50, null=True, blank=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.invoice._recalculate_totals()

    def __str__(self):
        return self.description
