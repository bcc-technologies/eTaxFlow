from django.db import models


class Organization(models.Model):
    legal_name = models.CharField(max_length=255)
    commercial_name = models.CharField(max_length=255, blank=True)
    rnc = models.CharField(max_length=50, unique=True)
    address = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True)
    is_default_issuer = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.commercial_name or self.legal_name

    class Meta:
        verbose_name = "Organization"
        verbose_name_plural = "Organizations"
