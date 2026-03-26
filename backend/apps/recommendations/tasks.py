from __future__ import annotations

import logging

from celery import shared_task
from django.db import transaction

from apps.audits.services import create_audit_event
from apps.cases.models import ReviewCase
from apps.core.constants import CaseStatus
from apps.recommendations.services import (
    generate_case_recommendation,
    generate_source_only_recommendation,
)

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=1, default_retry_delay=15)
def recommend_case_task(self, case_id: str) -> str:
    try:
        with transaction.atomic():
            case = ReviewCase.objects.select_for_update().get(id=case_id)

            create_audit_event(
                case=case,
                event_type="recommendation.started",
                payload={
                    "task_id": self.request.id,
                    "current_status": case.status,
                },
            )

            recommendation = generate_case_recommendation(case=case)

            logger.info(
                "recommendation_completed",
                extra={
                    "extra_data": {
                        "case_id": str(case.id),
                        "recommendation_id": str(recommendation.id),
                        "recommended_action": recommendation.recommended_action,
                        "task_id": self.request.id,
                    }
                },
            )

            return str(recommendation.id)

    except Exception as exc:
        logger.exception(
            "recommendation_failed",
            extra={
                "extra_data": {
                    "case_id": case_id,
                    "task_id": self.request.id,
                    "retry_count": self.request.retries,
                }
            },
        )

        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc) from exc

        with transaction.atomic():
            case = ReviewCase.objects.select_for_update().get(id=case_id)

            recommendation = generate_source_only_recommendation(
                case=case,
                reason=str(exc),
            )

            create_audit_event(
                case=case,
                event_type="recommendation.failed_fallback_review",
                payload={
                    "task_id": self.request.id,
                    "error": str(exc),
                    "case_status": case.status,
                    "fallback_recommendation_id": str(recommendation.id),
                },
            )

            if case.status not in {
                CaseStatus.NEEDS_REVIEW,
                CaseStatus.ESCALATED,
                CaseStatus.APPROVED,
            }:
                case.status = CaseStatus.NEEDS_REVIEW
                case.save(update_fields=["status", "updated_at"])

            return str(recommendation.id)
