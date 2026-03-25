import uuid

from django.db import models


class OutcomeCode(models.TextChoices):
    PRODUCTS_SERVICES = "products_services", "Products and services"
    PRICE_VALUE = "price_value", "Price and value"
    CONSUMER_UNDERSTANDING = "consumer_understanding", "Consumer understanding"
    CONSUMER_SUPPORT = "consumer_support", "Consumer support"


class LinkType(models.TextChoices):
    SUPPORTING = "supporting", "Supporting"
    CONTRADICTING = "contradicting", "Contradicting"
    CONTEXTUAL = "contextual", "Contextual"
    MISSING_EXPECTED_SOURCE = "missing_expected_source", "Missing expected source"


class ConsumerDutyOutcome(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=64, choices=OutcomeCode.choices, unique=True)
    name = models.CharField(max_length=128)
    description = models.TextField()
    active = models.BooleanField(default=True)


class EvidenceLink(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey(
        "cases.ReviewCase", on_delete=models.CASCADE, related_name="evidence_links"
    )
    claim = models.ForeignKey(
        "extraction.Claim", on_delete=models.CASCADE, related_name="evidence_links"
    )
    outcome = models.ForeignKey(
        ConsumerDutyOutcome, on_delete=models.CASCADE, related_name="evidence_links"
    )
    section = models.ForeignKey(
        "artifacts.DocumentSection",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="evidence_links",
    )
    link_type = models.CharField(max_length=32, choices=LinkType.choices)
    rationale = models.TextField()
    score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
