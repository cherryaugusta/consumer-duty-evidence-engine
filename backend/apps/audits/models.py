import uuid

from django.db import models


class ActorType(models.TextChoices):
    SYSTEM = "system", "System"
    USER = "user", "User"
    REVIEWER = "reviewer", "Reviewer"
    JOB = "job", "Job"


class AuditEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey(
        "cases.ReviewCase", on_delete=models.CASCADE, related_name="audit_events"
    )
    event_type = models.CharField(max_length=64)
    actor_type = models.CharField(max_length=16, choices=ActorType.choices)
    actor_id = models.CharField(max_length=64, null=True, blank=True)
    correlation_id = models.CharField(max_length=64, db_index=True)
    payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["case", "created_at"]),
        ]
