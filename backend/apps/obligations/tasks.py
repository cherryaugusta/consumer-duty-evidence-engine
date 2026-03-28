import logging

from celery import shared_task

from apps.assessments.tasks import assess_case_task
from apps.audits.services import emit_audit_event
from apps.cases.models import ReviewCase
from apps.obligations.services import map_case_outcomes

logger = logging.getLogger(__name__)


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=5, max_retries=2)
def map_case_task(self, case_id: str):
    case = ReviewCase.objects.get(pk=case_id)

    emit_audit_event(
        case=case,
        event_type="case.mapping.started",
        correlation_id=case.correlation_id,
        actor_type="job",
        actor_id=self.request.id,
        payload={
            "case_id": str(case.id),
        },
    )

    logger.info(
        "Case mapping started",
        extra={
            "extra_data": {
                "case_id": str(case.id),
                "correlation_id": case.correlation_id,
                "stage": "mapping",
                "task_id": self.request.id,
            }
        },
    )

    try:
        links = map_case_outcomes(case)

        emit_audit_event(
            case=case,
            event_type="case.mapping.completed",
            correlation_id=case.correlation_id,
            actor_type="job",
            actor_id=self.request.id,
            payload={
                "case_id": str(case.id),
                "created_links": len(links),
            },
        )

        logger.info(
            "Case mapping completed",
            extra={
                "extra_data": {
                    "case_id": str(case.id),
                    "correlation_id": case.correlation_id,
                    "stage": "mapping",
                    "task_id": self.request.id,
                    "created_links": len(links),
                }
            },
        )

        assess_case_task.delay(str(case.id))

        return {
            "case_id": str(case.id),
            "created_links": len(links),
        }
    except Exception as exc:
        emit_audit_event(
            case=case,
            event_type="case.mapping.failed",
            correlation_id=case.correlation_id,
            actor_type="job",
            actor_id=self.request.id,
            payload={
                "case_id": str(case.id),
                "error": str(exc),
            },
        )

        logger.exception(
            "Case mapping failed",
            extra={
                "extra_data": {
                    "case_id": str(case.id),
                    "correlation_id": case.correlation_id,
                    "stage": "mapping",
                    "task_id": self.request.id,
                    "error": str(exc),
                }
            },
        )
        raise
