from celery import shared_task

from apps.artifacts.models import ParseStatus, SourceArtifact
from apps.extraction.tasks import extract_case_task
from apps.parsing.services import parse_artifact_to_sections


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=5, max_retries=3)
def parse_artifact_task(self, artifact_id: str):
    artifact = SourceArtifact.objects.get(pk=artifact_id)

    artifact.parse_status = ParseStatus.RUNNING
    artifact.parse_error_code = None
    artifact.save(update_fields=["parse_status", "parse_error_code"])

    try:
        parse_artifact_to_sections(artifact)

        artifact.parse_status = ParseStatus.PARSED
        artifact.save(update_fields=["parse_status"])

        extract_case_task.delay(str(artifact.case_id))
    except Exception:
        artifact.parse_status = ParseStatus.FAILED
        artifact.parse_error_code = "parse_error"
        artifact.save(update_fields=["parse_status", "parse_error_code"])
        raise

    return {
        "artifact_id": str(artifact.id),
        "case_id": str(artifact.case_id),
        "parse_status": artifact.parse_status,
        "text_length": artifact.text_length,
    }
