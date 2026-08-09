from django.conf import settings
from django.db import models


class ECFDocument(models.Model):
    ENVIRONMENTS = [
        ("DEV", "Development"),
        ("PRE_CERTIFICATION", "Pre-certification"),
        ("CERTIFICATION", "Certification"),
        ("PRODUCTION", "Production"),
    ]
    DGII_STATUSES = [
        ("NOT_SENT", "Not Sent"),
        ("SENT", "Sent"),
        ("IN_PROCESS", "In Process"),
        ("ACCEPTED", "Accepted"),
        ("ACCEPTED_CONDITIONAL", "Accepted Conditional"),
        ("REJECTED", "Rejected"),
        ("ERROR", "Error"),
    ]
    SIGNING_STATUSES = [
        ("UNSIGNED", "Unsigned"),
        ("SIGNING_PLACEHOLDER", "Signing placeholder only"),
        ("SIGNING_READY", "Signing ready (future)"),
        ("SIGNED", "Signed (reserved — not implemented)"),
        ("SIGNING_FAILED", "Signing failed"),
    ]
    SIGNING_MODES = [
        ("NONE", "None"),
        ("PLACEHOLDER_ONLY", "Placeholder only (non-production)"),
        ("EXTERNAL_FUTURE_SERVICE", "External future service"),
    ]

    invoice = models.OneToOneField("invoicing.Invoice", on_delete=models.CASCADE, related_name="ecf_document")
    environment = models.CharField(max_length=30, choices=ENVIRONMENTS, default="DEV")
    ecf_type = models.CharField(max_length=100, blank=True)
    xml_unsigned_file = models.FileField(upload_to="ecf/unsigned/%Y/%m/%d", null=True, blank=True)
    xml_signed_file = models.FileField(upload_to="ecf/signed/%Y/%m/%d", null=True, blank=True)
    printed_representation_file = models.FileField(upload_to="ecf/printed/%Y/%m/%d", null=True, blank=True)
    dgii_track_id = models.CharField(max_length=255, null=True, blank=True)
    dgii_status = models.CharField(max_length=30, choices=DGII_STATUSES, default="NOT_SENT")
    dgii_status_message = models.TextField(blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    last_status_check_at = models.DateTimeField(null=True, blank=True)

    # Signing placeholder / readiness (NOT real digital signing).
    signing_status = models.CharField(
        max_length=30,
        choices=SIGNING_STATUSES,
        default="UNSIGNED",
    )
    signing_mode = models.CharField(
        max_length=40,
        choices=SIGNING_MODES,
        default="NONE",
    )
    signature_datetime = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Placeholder FechaHoraFirma only; not a real digital signature timestamp.",
    )
    signature_digest_algorithm = models.CharField(max_length=64, null=True, blank=True)
    signature_method = models.CharField(max_length=128, null=True, blank=True)
    signature_reference_uri = models.CharField(max_length=255, null=True, blank=True)
    signature_placeholder_note = models.TextField(blank=True)
    signed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="ecf_signing_placeholder_actions",
    )
    signing_attempted_at = models.DateTimeField(null=True, blank=True)
    signing_completed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"ECF for {self.invoice.internal_code}"

    @property
    def has_real_signed_artifact(self) -> bool:
        """True only when a signed XML file exists — never set by placeholder flow."""
        return bool(self.xml_signed_file)
