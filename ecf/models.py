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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"ECF for {self.invoice.internal_code}"
