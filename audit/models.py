from django.db import models


class AuditEvent(models.Model):
    actor = models.ForeignKey("auth.User", null=True, blank=True, on_delete=models.SET_NULL)
    event_type = models.CharField(max_length=100)
    entity_type = models.CharField(max_length=100)
    entity_id = models.PositiveIntegerField(null=True, blank=True)
    message = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.event_type} @ {self.created_at}"
