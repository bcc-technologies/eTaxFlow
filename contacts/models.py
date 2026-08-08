from django.db import models


class Contact(models.Model):
    CONTACT_TYPES = [
        ("CLIENT", "Client"),
        ("SUPPLIER", "Supplier"),
        ("BOTH", "Both"),
    ]

    contact_type = models.CharField(max_length=20, choices=CONTACT_TYPES)
    legal_name = models.CharField(max_length=255)
    commercial_name = models.CharField(max_length=255, blank=True)
    rnc_or_id = models.CharField(max_length=100)
    id_type = models.CharField(max_length=20, default="RNC")
    address = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    tax_category = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.commercial_name or self.legal_name
