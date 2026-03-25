import uuid

from django.db import models


class AssessmentStatus(models.TextChoices):
    SUPPORTED = "supported", "Supported"
    WEAK_SUPPORT = "weak_support", "Weak support"
    MISSING_SUPPORT = "missing_support", "Missing support"
    CONTRADICTORY_SUPPORT = "contradictory_support", "Contradictory support"
    STALE_SUPPORT = "stale_support", "Stale support"


class ContradictionType(models.TextChoices):
    DATE_CONFLICT = "date_conflict", "Date conflict"
    POLICY_CONFLICT = "policy_conflict", "Policy conflict"
    STATEMENT_CONFLICT = "statement_conflict", "Statement conflict"
    SUPPORT_GAP = "support_gap", "Support gap"


class SupportAssessment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey(
        "cases.ReviewCase", on_delete=models.CASCADE, related_name="assessments"
    )
    claim = models.ForeignKey(
        "extraction.Claim", on_delete=models.CASCADE, related_name="assessments"
    )
    outcome = models.ForeignKey(
        "obligations.ConsumerDutyOutcome", on_delete=models.CASCADE, related_name="assessments"
    )
    status = models.CharField(max_length=32, choices=AssessmentStatus.choices)
    confidence = models.FloatField()
    requires_review = models.BooleanField(default=False)
    assessment_reason = models.TextField()
    rules_triggered = models.JSONField(default=list, blank=True)
    model_version = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["case", "status", "requires_review"]),
        ]


class ContradictionFlag(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey(
        "cases.ReviewCase", on_delete=models.CASCADE, related_name="contradiction_flags"
    )
    claim = models.ForeignKey(
        "extraction.Claim",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="contradiction_flags",
    )
    primary_section = models.ForeignKey(
        "artifacts.DocumentSection", on_delete=models.CASCADE, related_name="primary_contradictions"
    )
    secondary_section = models.ForeignKey(
        "artifacts.DocumentSection",
        on_delete=models.CASCADE,
        related_name="secondary_contradictions",
    )
    contradiction_type = models.CharField(max_length=32, choices=ContradictionType.choices)
    severity = models.CharField(max_length=16)
    reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
