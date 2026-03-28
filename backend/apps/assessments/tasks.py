import logging

from celery import shared_task

from apps.assessments.services import assess_case_support, detect_case_contradictions
from apps.audits.services import emit_audit_event
from apps.cases.models import ReviewCase
from apps.cases.services import transition_case
from apps.core.constants import CaseStatus
from apps.recommendations.tasks import recommend_case_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=5, max_retries=2)
def assess_case_task(self, case_id: str):
    case = ReviewCase.objects.get(pk=case_id)

    emit_audit_event(
        case=case,
        event_type="case.assessment.started",
        correlation_id=case.correlation_id,
        actor_type="job",
        actor_id=self.request.id,
        payload={
            "case_id": str(case.id),
        },
    )

    logger.info(
        "Case assessment started",
        extra={
            "extra_data": {
                "case_id": str(case.id),
                "correlation_id": case.correlation_id,
                "stage": "assessment",
                "task_id": self.request.id,
            }
        },
    )

    try:
        assessments = assess_case_support(case)
        contradictions = detect_case_contradictions(case)

        case.refresh_from_db(fields=["status", "review_status", "degraded_mode_active"])

        if case.status != CaseStatus.ASSESSED:
            transition_case(
                case=case,
                new_status=CaseStatus.ASSESSED,
                correlation_id=case.correlation_id,
                actor_type="job",
                actor_id=self.request.id,
                message="Assessment completed",
                payload={
                    "task_id": self.request.id,
                    "stage": "assessment",
                },
            )

        emit_audit_event(
            case=case,
            event_type="case.assessment.completed",
            correlation_id=case.correlation_id,
            actor_type="job",
            actor_id=self.request.id,
            payload={
                "case_id": str(case.id),
                "created_assessments": len(assessments),
                "created_contradictions": len(contradictions),
                "case_status": case.status,
            },
        )

        logger.info(
            "Case assessment completed",
            extra={
                "extra_data": {
                    "case_id": str(case.id),
                    "correlation_id": case.correlation_id,
                    "stage": "assessment",
                    "task_id": self.request.id,
                    "created_assessments": len(assessments),
                    "created_contradictions": len(contradictions),
                    "case_status": case.status,
                }
            },
        )

        recommend_case_task.delay(str(case.id))

        return {
            "case_id": str(case.id),
            "created_assessments": len(assessments),
            "created_contradictions": len(contradictions),
            "queued_recommendation": True,
            "case_status": case.status,
        }
    except Exception as exc:
        emit_audit_event(
            case=case,
            event_type="case.assessment.failed",
            correlation_id=case.correlation_id,
            actor_type="job",
            actor_id=self.request.id,
            payload={
                "case_id": str(case.id),
                "error": str(exc),
            },
        )

        logger.exception(
            "Case assessment failed",
            extra={
                "extra_data": {
                    "case_id": str(case.id),
                    "correlation_id": case.correlation_id,
                    "stage": "assessment",
                    "task_id": self.request.id,
                    "error": str(exc),
                }
            },
        )
        raise
