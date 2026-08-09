import hashlib
from django.conf import settings
from django.db import models

from audit.models import AuditEvent


class Document(models.Model):
    DOCUMENT_DIRECTIONS = [
        ("INBOUND", "Inbound"),
        ("OUTBOUND", "Outbound"),
        ("INTERNAL", "Internal"),
    ]
    DOCUMENT_KINDS = [
        ("INVOICE", "Invoice"),
        ("QUOTATION", "Quotation"),
        ("CREDIT_NOTE", "Credit Note"),
        ("DEBIT_NOTE", "Debit Note"),
        ("RECEIPT", "Receipt"),
        ("CONTRACT", "Contract"),
        ("XML", "XML"),
        ("PDF", "PDF"),
        ("IMAGE", "Image"),
        ("OTHER", "Other"),
    ]
    SOURCES = [
        ("MANUAL_UPLOAD", "Manual Upload"),
        ("GENERATED", "Generated"),
        ("EMAIL", "Email"),
        ("API", "API"),
        ("LEGACY_IMPORT", "Legacy Import"),
    ]
    STATUSES = [
        ("DRAFT", "Draft"),
        ("STORED", "Stored"),
        ("LINKED", "Linked"),
        ("ARCHIVED", "Archived"),
        ("VOIDED", "Voided"),
    ]

    internal_code = models.CharField(max_length=50, unique=True)
    document_direction = models.CharField(max_length=20, choices=DOCUMENT_DIRECTIONS)
    document_kind = models.CharField(max_length=20, choices=DOCUMENT_KINDS)
    source = models.CharField(max_length=20, choices=SOURCES)
    original_filename = models.CharField(max_length=255)
    file = models.FileField(upload_to="documents/%Y/%m/%d")
    mime_type = models.CharField(max_length=100, blank=True)
    file_size = models.PositiveIntegerField(default=0)
    sha256_hash = models.CharField(max_length=64, blank=True)
    status = models.CharField(max_length=20, choices=STATUSES, default="DRAFT")
    issuer = models.ForeignKey("organizations.Organization", null=True, blank=True, on_delete=models.SET_NULL, related_name="documents")
    related_contact = models.ForeignKey("contacts.Contact", null=True, blank=True, on_delete=models.SET_NULL, related_name="documents")
    related_invoice = models.ForeignKey(
        "invoicing.Invoice",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="documents",
    )
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        previous_invoice = None
        if not is_new:
            previous = Document.objects.filter(pk=self.pk).first()
            previous_invoice = previous.related_invoice if previous else None

        file_obj = self.file
        if file_obj:
            self.file_size = file_obj.size
            file_obj.open("rb")
            content = file_obj.read()
            file_obj.seek(0)
            self.sha256_hash = hashlib.sha256(content).hexdigest()
            if not self.mime_type:
                self.mime_type = getattr(file_obj, "content_type", None) or "application/octet-stream"

        super().save(*args, **kwargs)

        if is_new:
            AuditEvent.objects.create(
                actor=self.created_by,
                event_type="document_uploaded",
                entity_type="Document",
                entity_id=self.pk,
                message="Document uploaded and stored",
                metadata={"filename": self.original_filename, "sha256": self.sha256_hash},
            )

        if self.related_invoice and self.related_invoice != previous_invoice:
            AuditEvent.objects.create(
                actor=self.created_by,
                event_type="document_linked_to_invoice",
                entity_type="Document",
                entity_id=self.pk,
                message=f"Document linked to invoice {self.related_invoice.internal_code}",
                metadata={
                    "related_invoice": self.related_invoice.internal_code,
                    "invoice_id": self.related_invoice.pk,
                },
            )

    def __str__(self):
        return self.internal_code
