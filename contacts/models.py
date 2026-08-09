from django.db import models


class Contact(models.Model):
    """Party master data (clients/suppliers).

    Soft uniqueness: business logic treats (contact_type, rnc_or_id) as a
    natural key, but this is not enforced with a database UniqueConstraint yet
    because local/dev databases may already contain duplicates. Prefer
    ``contacts.natural_keys.resolve_contact_by_natural_key`` for seed/demo
    resolution.
    """

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

    def natural_key_warnings(self):
        """Return soft-uniqueness warnings for this contact's natural key."""
        from contacts.natural_keys import natural_key_duplicate_warnings

        return natural_key_duplicate_warnings(self.contact_type, self.rnc_or_id)
