import uuid

from django.conf import settings
from django.db import models

from apps.core.constants import CaseStatus, CaseType, Priority, ReviewStatus


class ReviewCase(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reference_code = models.CharField(max_length=64, unique=True)
    title = models.CharField(max_length=255)
    status = models.CharField(
        max_length=32,
        choices=CaseStatus.choices,
        default=CaseStatus.NEW,
    )
    review_status = models.CharField(
        max_length=32,
        choices=ReviewStatus.choices,
        default=ReviewStatus.UNASSIGNED,
    )
    priority = models.CharField(
        max_length=16,
        choices=Priority.choices,
        default=Priority.MEDIUM,
    )
    case_type = models.CharField(max_length=32, choices=CaseType.choices)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="submitted_cases",
    )
    assigned_reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="assigned_cases",
    )
    correlation_id = models.CharField(max_length=64, db_index=True)
    latest_eval_run_id = models.UUIDField(null=True, blank=True)
    eval_case_id = models.CharField(max_length=128, null=True, blank=True, db_index=True)
    degraded_mode_active = models.BooleanField(default=False)
    dedupe_key = models.CharField(max_length=255, null=True, blank=True)
    summary_snapshot = models.JSONField(default=dict, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["status", "priority", "created_at"]),
        ]

    def __str__(self):
        return f"{self.reference_code} - {self.title}"
