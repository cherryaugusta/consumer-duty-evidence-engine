from django.db import models


class Priority(models.TextChoices):
    LOW = "low", "Low"
    MEDIUM = "medium", "Medium"
    HIGH = "high", "High"
    CRITICAL = "critical", "Critical"


class CaseType(models.TextChoices):
    COMPLAINT_REVIEW = "complaint_review", "Complaint review"
    SUPPORT_REVIEW = "support_review", "Support review"
    DISCLOSURE_REVIEW = "disclosure_review", "Disclosure review"


class CaseStatus(models.TextChoices):
    NEW = "new", "New"
    INGESTION_PENDING = "ingestion_pending", "Ingestion pending"
    PARSING = "parsing", "Parsing"
    PARSED = "parsed", "Parsed"
    EXTRACTION_PENDING = "extraction_pending", "Extraction pending"
    EXTRACTED = "extracted", "Extracted"
    MAPPING_PENDING = "mapping_pending", "Mapping pending"
    MAPPED = "mapped", "Mapped"
    ASSESSMENT_PENDING = "assessment_pending", "Assessment pending"
    ASSESSED = "assessed", "Assessed"
    NEEDS_REVIEW = "needs_review", "Needs review"
    APPROVED = "approved", "Approved"
    ESCALATED = "escalated", "Escalated"
    ARCHIVED = "archived", "Archived"
    FAILED = "failed", "Failed"


class ReviewStatus(models.TextChoices):
    UNASSIGNED = "unassigned", "Unassigned"
    ASSIGNED = "assigned", "Assigned"
    IN_REVIEW = "in_review", "In review"
    OVERRIDDEN = "overridden", "Overridden"
    APPROVED = "approved", "Approved"
    ESCALATED = "escalated", "Escalated"
    CLOSED = "closed", "Closed"


class TaskState(models.TextChoices):
    QUEUED = "queued", "Queued"
    RUNNING = "running", "Running"
    SUCCEEDED = "succeeded", "Succeeded"
    FAILED = "failed", "Failed"
    RETRYING = "retrying", "Retrying"
    CANCELLED = "cancelled", "Cancelled"
