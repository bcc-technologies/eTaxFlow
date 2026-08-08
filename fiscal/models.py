from datetime import datetime

from django.db import models


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
