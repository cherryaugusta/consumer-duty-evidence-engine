import logging

from celery import shared_task

from apps.assessments.tasks import assess_case_task
from apps.audits.services import emit_audit_event
from apps.cases.models import ReviewCase
from apps.cases.services import transition_case
from apps.core.constants import CaseStatus
from apps.obligations.services import map_case_outcomes

logger = logging.getLogger(__name__)


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=5, max_retries=2)
def map_case_task(self, case_id: str):
    case = ReviewCase.objects.get(pk=case_id)

    if case.status != CaseStatus.MAPPING_PENDING:
        logger.info(
            "Case mapping skipped; unexpected state",
            extra={
                "extra_data": {
                    "case_id": str(case.id),
                    "correlation_id": case.correlation_id,
                    "stage": "mapping",
                    "task_id": self.request.id,
                    "case_status": case.status,
                    "expected_status": CaseStatus.MAPPING_PENDING,
                }
            },
        )
        return {
            "case_id": str(case.id),
            "created_links": 0,
            "skipped": True,
            "case_status": case.status,
        }

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

        transition_case(
            case=case,
            new_status=CaseStatus.MAPPED,
            correlation_id=case.correlation_id,
            actor_type="job",
            actor_id=self.request.id,
            message="Mapping completed",
            payload={
                "task_id": self.request.id,
                "stage": "mapping",
                "created_links": len(links),
            },
        )

        case.refresh_from_db(fields=["status"])

        transition_case(
            case=case,
            new_status=CaseStatus.ASSESSMENT_PENDING,
            correlation_id=case.correlation_id,
            actor_type="job",
            actor_id=self.request.id,
            message="Assessment queued",
            payload={
                "task_id": self.request.id,
                "stage": "mapping",
            },
        )

        emit_audit_event(
            case=case,
            event_type="case.mapping.completed",
            correlation_id=case.correlation_id,
            actor_type="job",
            actor_id=self.request.id,
            payload={
                "case_id": str(case.id),
                "created_links": len(links),
                "case_status": case.status,
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
                    "case_status": case.status,
                }
            },
        )

        assess_case_task.delay(str(case.id))

        return {
            "case_id": str(case.id),
            "created_links": len(links),
            "case_status": case.status,
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
