import uuid

from django.db import models
from pgvector.django import VectorField


class ArtifactType(models.TextChoices):
    COMPLAINT = "complaint", "Complaint"
    SUPPORT_TRANSCRIPT = "support_transcript", "Support transcript"
    DISCLOSURE = "disclosure", "Disclosure"
    POLICY_EXCERPT = "policy_excerpt", "Policy excerpt"
    SCRIPT = "script", "Script"
    INTERNAL_NOTE = "internal_note", "Internal note"


class SourceChannel(models.TextChoices):
    UPLOAD = "upload", "Upload"
    SEEDED_DEMO = "seeded_demo", "Seeded demo"
    API = "api", "API"
    MANUAL_ENTRY = "manual_entry", "Manual entry"


class ParseStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    RUNNING = "running", "Running"
    PARSED = "parsed", "Parsed"
    FAILED = "failed", "Failed"


class SourceArtifact(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey("cases.ReviewCase", on_delete=models.CASCADE, related_name="artifacts")
    artifact_type = models.CharField(max_length=32, choices=ArtifactType.choices)
    filename = models.CharField(max_length=255)
    mime_type = models.CharField(max_length=128)
    source_channel = models.CharField(max_length=32, choices=SourceChannel.choices)
    storage_path = models.CharField(max_length=500)
    sha256_checksum = models.CharField(max_length=64)
    parse_status = models.CharField(
        max_length=16, choices=ParseStatus.choices, default=ParseStatus.PENDING
    )
    parse_error_code = models.CharField(max_length=64, null=True, blank=True)
    text_length = models.IntegerField(default=0)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["case", "artifact_type"]),
            models.Index(fields=["case", "sha256_checksum"]),
        ]
        constraints = [
            models.UniqueConstraint(fields=["case", "sha256_checksum"], name="uq_case_checksum")
        ]


class DocumentSection(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    artifact = models.ForeignKey(SourceArtifact, on_delete=models.CASCADE, related_name="sections")
    section_index = models.IntegerField()
    heading = models.CharField(max_length=255, null=True, blank=True)
    text = models.TextField()
    char_start = models.IntegerField()
    char_end = models.IntegerField()
    page_number = models.IntegerField(null=True, blank=True)
    parser_confidence = models.FloatField(null=True, blank=True)
    embedding_vector = VectorField(dimensions=1536, null=True, blank=True)

    class Meta:
        ordering = ["artifact", "section_index"]
        constraints = [
            models.UniqueConstraint(
                fields=["artifact", "section_index"],
                name="uq_artifact_section_index",
            )
        ]
