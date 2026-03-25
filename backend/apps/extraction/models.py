import uuid

from django.db import models


class ClaimType(models.TextChoices):
    CUSTOMER_HARM = "customer_harm", "Customer harm"
    MISLEADING_EXPLANATION = "misleading_explanation", "Misleading explanation"
    SUPPORT_DELAY = "support_delay", "Support delay"
    UNCLEAR_FEE = "unclear_fee", "Unclear fee"
    INADEQUATE_DISCLOSURE = "inadequate_disclosure", "Inadequate disclosure"
    POOR_OUTCOME_INDICATOR = "poor_outcome_indicator", "Poor outcome indicator"
    OTHER = "other", "Other"


class Claim(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey("cases.ReviewCase", on_delete=models.CASCADE, related_name="claims")
    claim_type = models.CharField(max_length=32, choices=ClaimType.choices)
    claim_text = models.TextField()
    normalized_claim_text = models.TextField()
    source_section = models.ForeignKey(
        "artifacts.DocumentSection", on_delete=models.CASCADE, related_name="claims"
    )
    extraction_confidence = models.FloatField()
    schema_valid = models.BooleanField(default=True)
    extraction_version = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["case", "claim_type"]),
        ]
