from datetime import datetime

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class InternalDocumentCode(models.Model):
    prefix = models.CharField(max_length=10)
    year = models.PositiveIntegerField()
    last_number = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("prefix", "year")

    @classmethod
    def generate_code(cls, prefix, year):
        record, created = cls.objects.get_or_create(prefix=prefix, year=year, defaults={"last_number": 0})
        record.last_number += 1
        record.save(update_fields=["last_number"])
        return f"BCC-{prefix}-{year}-{record.last_number:06d}"

    def __str__(self):
        return f"{self.prefix}-{self.year}-{self.last_number}"


class FiscalDocumentType(models.Model):
    DOCUMENT_GROUPS = [
        ("INVOICE", "Invoice"),
        ("CONSUMER_INVOICE", "Consumer Invoice"),
        ("DEBIT_NOTE", "Debit Note"),
        ("CREDIT_NOTE", "Credit Note"),
        ("GOVERNMENT", "Government"),
        ("SPECIAL_REGIME", "Special Regime"),
        ("EXPORT", "Export"),
        ("FOREIGN_PAYMENT", "Foreign Payment"),
        ("OTHER", "Other"),
    ]
    DIRECTIONS = [("OUTBOUND", "Outbound"), ("INBOUND", "Inbound"), ("BOTH", "Both")]

    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    document_group = models.CharField(max_length=30, choices=DOCUMENT_GROUPS)
    direction = models.CharField(max_length=20, choices=DIRECTIONS, default="BOTH")
    is_electronic = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    requires_customer_rnc = models.BooleanField(default=True)
    requires_printed_representation = models.BooleanField(default=False)
    affects_accounts_receivable = models.BooleanField(default=True)
    affects_accounts_payable = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.code} - {self.name}"


class TaxRate(models.Model):
    TAX_TYPES = [
        ("ITBIS", "ITBIS"),
        ("EXEMPT", "Exempt"),
        ("ZERO_RATE", "Zero Rate"),
        ("OTHER", "Other"),
    ]

    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    rate = models.DecimalField(max_digits=6, decimal_places=2)
    tax_type = models.CharField(max_length=20, choices=TAX_TYPES, default="OTHER")
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    valid_from = models.DateField(null=True, blank=True)
    valid_to = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["code"]

    def clean(self):
        if self.is_default and self.is_active:
            conflict = TaxRate.objects.filter(
                tax_type=self.tax_type,
                is_default=True,
                is_active=True,
            )
            if self.pk:
                conflict = conflict.exclude(pk=self.pk)
            if conflict.exists():
                raise ValidationError(
                    {"is_default": "Only one active default rate may exist per tax type."}
                )
        if self.rate < 0:
            raise ValidationError({"rate": "Tax rate must be zero or positive."})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.code} ({self.rate}%)"


class UnitOfMeasure(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=255)
    symbol = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return self.code


class FiscalIncomeType(models.Model):
    """TipoIngresos catalog (Formato e-CF / XSD enums 01-06).

    Internal master data only — not a DGII compliance claim.
    """

    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["code"]
        verbose_name = "Fiscal income type"
        verbose_name_plural = "Fiscal income types"

    def __str__(self):
        return f"{self.code} - {self.name}"


class PaymentType(models.Model):
    """TipoPago catalog (Formato e-CF / XSD enums 1|2|3).

    Internal master data only — not a payments module and not DGII-compliant.
    """

    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["code"]
        verbose_name = "Payment type"
        verbose_name_plural = "Payment types"

    def __str__(self):
        return f"{self.code} - {self.name}"


class BillingIndicator(models.Model):
    """IndicadorFacturacion catalog (Formato e-CF / XSD enums 0|1|2|3|4).

    Line-level ITBIS/exempt/no-facturable indicator. Internal only.
    """

    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["code"]
        verbose_name = "Billing indicator"
        verbose_name_plural = "Billing indicators"

    def __str__(self):
        return f"{self.code} - {self.name}"
