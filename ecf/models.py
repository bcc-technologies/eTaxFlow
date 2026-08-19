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


class InboundXMLLabRecord(models.Model):
    """NON_PRODUCTION_LAB_ONLY analysis row. Not a fiscal document. Not DGII evidence."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    source_path = models.CharField(max_length=512, blank=True)
    filename = models.CharField(max_length=255, blank=True)
    raw_sha256 = models.CharField(max_length=64, unique=True, db_index=True)
    raw_size_bytes = models.PositiveIntegerField(default=0)
    root_tag = models.CharField(max_length=64, blank=True, db_index=True)
    document_type = models.CharField(max_length=32, db_index=True)
    classification_status = models.CharField(max_length=64, blank=True)
    signature_present = models.BooleanField(default=False)
    signature_verification_status = models.CharField(max_length=64, blank=True)
    signature_verified = models.BooleanField(default=False)
    production_signature_ready = models.BooleanField(default=False)
    schema_validation_scope = models.CharField(max_length=64, blank=True)
    xsd_path = models.CharField(max_length=512, blank=True)
    xsd_available = models.BooleanField(default=False)
    xsd_compiled = models.BooleanField(default=False)
    local_xsd_valid = models.BooleanField(null=True, blank=True)
    xsd_error_count = models.PositiveIntegerField(default=0)
    errors_json = models.JSONField(default=list)
    persisted_raw_xml = models.BooleanField(default=False)
    raw_xml_text = models.TextField(blank=True, default="")
    compliance_status = models.CharField(max_length=32, default="NOT_DGII_COMPLIANT")
    dgii_submission_allowed = models.BooleanField(default=False)
    certification_evidence = models.BooleanField(default=False)
    track_id = models.CharField(max_length=255, null=True, blank=True, default=None)
    dgii_call_made = models.BooleanField(default=False)
    lab_mode = models.CharField(max_length=40, default="NON_PRODUCTION_LAB_ONLY")

    class Meta:
        verbose_name = "Inbound XML lab record (NON_PRODUCTION_LAB_ONLY)"
        verbose_name_plural = "Inbound XML lab records (NON_PRODUCTION_LAB_ONLY)"
        indexes = [
            models.Index(fields=["created_at"]),
            models.Index(fields=["document_type", "root_tag"]),
        ]

    def __str__(self) -> str:
        return f"Lab {self.document_type} {self.filename or self.raw_sha256[:12]}"
