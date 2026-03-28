import logging

from celery import shared_task

from apps.audits.services import emit_audit_event
from apps.cases.models import ReviewCase
from apps.cases.services import transition_case
from apps.core.constants import CaseStatus
from apps.extraction.services import extract_claims_for_case
from apps.obligations.tasks import map_case_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=5, max_retries=2)
def extract_case_task(self, case_id: str):
    case = ReviewCase.objects.get(pk=case_id)

    if case.status != CaseStatus.EXTRACTION_PENDING:
        logger.info(
            "Case extraction skipped; unexpected state",
            extra={
                "extra_data": {
                    "case_id": str(case.id),
                    "correlation_id": case.correlation_id,
                    "stage": "extraction",
                    "task_id": self.request.id,
                    "case_status": case.status,
                    "expected_status": CaseStatus.EXTRACTION_PENDING,
                }
            },
        )
        return {
            "case_id": str(case.id),
            "created_claims": 0,
            "skipped": True,
            "case_status": case.status,
        }

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

        transition_case(
            case=case,
            new_status=CaseStatus.EXTRACTED,
            correlation_id=case.correlation_id,
            actor_type="job",
            actor_id=self.request.id,
            message="Extraction completed",
            payload={
                "task_id": self.request.id,
                "stage": "extraction",
                "created_claims": len(claims),
            },
        )

        case.refresh_from_db(fields=["status"])

        transition_case(
            case=case,
            new_status=CaseStatus.MAPPING_PENDING,
            correlation_id=case.correlation_id,
            actor_type="job",
            actor_id=self.request.id,
            message="Mapping queued",
            payload={
                "task_id": self.request.id,
                "stage": "extraction",
            },
        )

        emit_audit_event(
            case=case,
            event_type="case.extraction.completed",
            correlation_id=case.correlation_id,
            actor_type="job",
            actor_id=self.request.id,
            payload={
                "case_id": str(case.id),
                "created_claims": len(claims),
                "case_status": case.status,
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
                    "case_status": case.status,
                }
            },
        )

        map_case_task.delay(str(case.id))

        return {
            "case_id": str(case.id),
            "created_claims": len(claims),
            "case_status": case.status,
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
