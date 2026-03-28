import logging

from celery import shared_task

from apps.audits.services import emit_audit_event
from apps.cases.models import ReviewCase
from apps.extraction.services import extract_claims_for_case
from apps.obligations.tasks import map_case_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=5, max_retries=2)
def extract_case_task(self, case_id: str):
    case = ReviewCase.objects.get(pk=case_id)

    emit_audit_event(
        case=case,
        event_type="case.extraction.started",
        correlation_id=case.correlation_id,
        actor_type="job",
        actor_id=self.request.id,
        payload={
            "case_id": str(case.id),
        },
    )

    logger.info(
        "Case extraction started",
        extra={
            "extra_data": {
                "case_id": str(case.id),
                "correlation_id": case.correlation_id,
                "stage": "extraction",
                "task_id": self.request.id,
            }
        },
    )

    try:
        claims = extract_claims_for_case(case)

        emit_audit_event(
            case=case,
            event_type="case.extraction.completed",
            correlation_id=case.correlation_id,
            actor_type="job",
            actor_id=self.request.id,
            payload={
                "case_id": str(case.id),
                "created_claims": len(claims),
            },
        )

        logger.info(
            "Case extraction completed",
            extra={
                "extra_data": {
                    "case_id": str(case.id),
                    "correlation_id": case.correlation_id,
                    "stage": "extraction",
                    "task_id": self.request.id,
                    "created_claims": len(claims),
                }
            },
        )

        map_case_task.delay(str(case.id))

        return {
            "case_id": str(case.id),
            "created_claims": len(claims),
        }
    except Exception as exc:
        emit_audit_event(
            case=case,
            event_type="case.extraction.failed",
            correlation_id=case.correlation_id,
            actor_type="job",
            actor_id=self.request.id,
            payload={
                "case_id": str(case.id),
                "error": str(exc),
            },
        )

        logger.exception(
            "Case extraction failed",
            extra={
                "extra_data": {
                    "case_id": str(case.id),
                    "correlation_id": case.correlation_id,
                    "stage": "extraction",
                    "task_id": self.request.id,
                    "error": str(exc),
                }
            },
        )
        raise
