import logging

from celery import shared_task

from apps.artifacts.models import ParseStatus, SourceArtifact
from apps.audits.services import emit_audit_event
from apps.extraction.tasks import extract_case_task
from apps.parsing.services import parse_artifact_to_sections

logger = logging.getLogger(__name__)


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=5, max_retries=3)
def parse_artifact_task(self, artifact_id: str):
    artifact = SourceArtifact.objects.select_related("case").get(pk=artifact_id)

    emit_audit_event(
        case=artifact.case,
        event_type="case.parsing.started",
        correlation_id=artifact.case.correlation_id,
        actor_type="job",
        actor_id=self.request.id,
        payload={
            "artifact_id": str(artifact.id),
            "artifact_filename": artifact.filename,
            "artifact_type": artifact.artifact_type,
        },
    )

    logger.info(
        "Artifact parsing started",
        extra={
            "extra_data": {
                "case_id": str(artifact.case_id),
                "artifact_id": str(artifact.id),
                "correlation_id": artifact.case.correlation_id,
                "stage": "parsing",
                "task_id": self.request.id,
            }
        },
    )

    artifact.parse_status = ParseStatus.RUNNING
    artifact.parse_error_code = None
    artifact.save(update_fields=["parse_status", "parse_error_code"])

    try:
        parse_artifact_to_sections(artifact)

        artifact.parse_status = ParseStatus.PARSED
        artifact.save(update_fields=["parse_status"])

        emit_audit_event(
            case=artifact.case,
            event_type="case.parsing.completed",
            correlation_id=artifact.case.correlation_id,
            actor_type="job",
            actor_id=self.request.id,
            payload={
                "artifact_id": str(artifact.id),
                "artifact_filename": artifact.filename,
                "artifact_type": artifact.artifact_type,
                "text_length": artifact.text_length,
                "parse_status": artifact.parse_status,
            },
        )

        logger.info(
            "Artifact parsing completed",
            extra={
                "extra_data": {
                    "case_id": str(artifact.case_id),
                    "artifact_id": str(artifact.id),
                    "correlation_id": artifact.case.correlation_id,
                    "stage": "parsing",
                    "task_id": self.request.id,
                    "text_length": artifact.text_length,
                }
            },
        )

        extract_case_task.delay(str(artifact.case_id))
    except Exception as exc:
        artifact.parse_status = ParseStatus.FAILED
        artifact.parse_error_code = "parse_error"
        artifact.save(update_fields=["parse_status", "parse_error_code"])

        emit_audit_event(
            case=artifact.case,
            event_type="case.parsing.failed",
            correlation_id=artifact.case.correlation_id,
            actor_type="job",
            actor_id=self.request.id,
            payload={
                "artifact_id": str(artifact.id),
                "artifact_filename": artifact.filename,
                "artifact_type": artifact.artifact_type,
                "error": str(exc),
                "parse_status": artifact.parse_status,
                "parse_error_code": artifact.parse_error_code,
            },
        )

        logger.exception(
            "Artifact parsing failed",
            extra={
                "extra_data": {
                    "case_id": str(artifact.case_id),
                    "artifact_id": str(artifact.id),
                    "correlation_id": artifact.case.correlation_id,
                    "stage": "parsing",
                    "task_id": self.request.id,
                    "error": str(exc),
                }
            },
        )
        raise

    return {
        "artifact_id": str(artifact.id),
        "case_id": str(artifact.case_id),
        "parse_status": artifact.parse_status,
        "text_length": artifact.text_length,
    }
