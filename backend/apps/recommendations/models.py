import uuid

from django.db import models


class PromptPurpose(models.TextChoices):
    EXTRACTION = "extraction", "Extraction"
    MAPPING = "mapping", "Mapping"
    ASSESSMENT = "assessment", "Assessment"
    RECOMMENDATION = "recommendation", "Recommendation"


class RecommendedAction(models.TextChoices):
    APPROVE = "approve", "Approve"
    REVIEW = "review", "Review"
    ESCALATE = "escalate", "Escalate"
    REQUEST_MORE_EVIDENCE = "request_more_evidence", "Request more evidence"


class PromptVersion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=128)
    version_label = models.CharField(max_length=64)
    purpose = models.CharField(max_length=32, choices=PromptPurpose.choices)
    template_text = models.TextField()
    schema_version = models.CharField(max_length=64)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Recommendation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.OneToOneField(
        "cases.ReviewCase", on_delete=models.CASCADE, related_name="recommendation"
    )
    recommended_action = models.CharField(max_length=32, choices=RecommendedAction.choices)
    recommended_priority = models.CharField(max_length=16)
    executive_summary = models.TextField()
    structured_rationale = models.JSONField(default=dict, blank=True)
    confidence = models.FloatField()
    citation_count = models.IntegerField(default=0)
    model_version = models.CharField(max_length=64)
    prompt_version = models.ForeignKey(
        PromptVersion,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="recommendations",
    )
    created_at = models.DateTimeField(auto_now_add=True)
