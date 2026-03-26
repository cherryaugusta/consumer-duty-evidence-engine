from celery import shared_task
from django.db import transaction

from apps.artifacts.models import DocumentSection, ParseStatus, SourceArtifact


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=5, max_retries=3)
def parse_artifact_task(self, artifact_id: str):
    """
    Minimal parsing implementation:
    - Reads text file
    - Creates a single DocumentSection
    """

    artifact = SourceArtifact.objects.get(id=artifact_id)

    artifact.parse_status = ParseStatus.RUNNING
    artifact.save(update_fields=["parse_status"])

    try:
        with open(artifact.storage_path, encoding="utf-8") as f:
            text = f.read()

        with transaction.atomic():
            DocumentSection.objects.create(
                artifact=artifact,
                section_index=0,
                heading=None,
                text=text,
                char_start=0,
                char_end=len(text),
                page_number=None,
                parser_confidence=1.0,
            )

        artifact.parse_status = ParseStatus.PARSED
        artifact.text_length = len(text)
        artifact.save(update_fields=["parse_status", "text_length"])

    except Exception as e:
        artifact.parse_status = ParseStatus.FAILED
        artifact.parse_error_code = str(e)
        artifact.save(update_fields=["parse_status", "parse_error_code"])
        raise
