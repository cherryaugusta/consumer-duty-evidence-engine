import uuid

from django.conf import settings
from django.db import models

from apps.core.constants import ReviewStatus


class ReviewReasonCode(models.TextChoices):
    LOW_CONFIDENCE = "low_confidence", "Low confidence"
    SCHEMA_FAILURE = "schema_failure", "Schema failure"
    CONTRADICTION = "contradiction", "Contradiction"
    MISSING_SUPPORT = "missing_support", "Missing support"
    MANUAL_SAMPLING = "manual_sampling", "Manual sampling"
    MODEL_UNAVAILABLE = "model_unavailable", "Model unavailable"


class ReviewerActionType(models.TextChoices):
    APPROVE = "approve", "Approve"
    OVERRIDE = "override", "Override"
    ESCALATE = "escalate", "Escalate"
    REQUEST_MORE_EVIDENCE = "request_more_evidence", "Request more evidence"
    MARK_FALSE_POSITIVE = "mark_false_positive", "Mark false positive"
    CLOSE = "close", "Close"


class ReviewTask(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.OneToOneField(
        "cases.ReviewCase", on_delete=models.CASCADE, related_name="review_task"
    )
    queue_name = models.CharField(max_length=64)
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="review_tasks",
    )
    status = models.CharField(
        max_length=32, choices=ReviewStatus.choices, default=ReviewStatus.UNASSIGNED
    )
    reason_code = models.CharField(max_length=32, choices=ReviewReasonCode.choices)
    sla_due_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["status", "queue_name", "sla_due_at"]),
        ]


class ReviewerAction(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    review_task = models.ForeignKey(ReviewTask, on_delete=models.CASCADE, related_name="actions")
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviewer_actions"
    )
    action_type = models.CharField(max_length=32, choices=ReviewerActionType.choices)
    old_value = models.JSONField(null=True, blank=True)
    new_value = models.JSONField(null=True, blank=True)
    comment = models.TextField()
    override_reason_code = models.CharField(max_length=64, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
