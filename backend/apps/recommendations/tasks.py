from __future__ import annotations

import logging

from celery import shared_task
from django.db import transaction

from apps.audits.services import create_audit_event, emit_audit_event
from apps.cases.models import ReviewCase
from apps.cases.services import transition_case
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

            emit_audit_event(
                case=case,
                event_type="case.recommendation.started",
                correlation_id=case.correlation_id,
                actor_type="job",
                actor_id=self.request.id,
                payload={
                    "case_id": str(case.id),
                    "task_id": self.request.id,
                    "current_status": case.status,
                },
            )

            create_audit_event(
                case=case,
                event_type="recommendation.started",
                correlation_id=case.correlation_id,
                actor_type="job",
                actor_id=self.request.id,
                payload={
                    "task_id": self.request.id,
                    "current_status": case.status,
                },
            )

            logger.info(
                "Recommendation started",
                extra={
                    "extra_data": {
                        "case_id": str(case.id),
                        "correlation_id": case.correlation_id,
                        "stage": "recommendation",
                        "task_id": self.request.id,
                        "current_status": case.status,
                    }
                },
            )

            recommendation = generate_case_recommendation(case=case)

            emit_audit_event(
                case=case,
                event_type="case.recommendation.completed",
                correlation_id=case.correlation_id,
                actor_type="job",
                actor_id=self.request.id,
                payload={
                    "case_id": str(case.id),
                    "recommendation_id": str(recommendation.id),
                    "recommended_action": recommendation.recommended_action,
                    "task_id": self.request.id,
                    "case_status": case.status,
                },
            )

            logger.info(
                "Recommendation completed",
                extra={
                    "extra_data": {
                        "case_id": str(case.id),
                        "correlation_id": case.correlation_id,
                        "stage": "recommendation",
                        "task_id": self.request.id,
                        "recommendation_id": str(recommendation.id),
                        "recommended_action": recommendation.recommended_action,
                        "case_status": case.status,
                    }
                },
            )

            return str(recommendation.id)

    except Exception as exc:
        logger.exception(
            "Recommendation failed",
            extra={
                "extra_data": {
                    "case_id": case_id,
                    "stage": "recommendation",
                    "task_id": self.request.id,
                    "retry_count": self.request.retries,
                    "error": str(exc),
                }
            },
        )

        if self.request.retries < self.max_retries:
            try:
                case = ReviewCase.objects.get(id=case_id)
                emit_audit_event(
                    case=case,
                    event_type="case.recommendation.retrying",
                    correlation_id=case.correlation_id,
                    actor_type="job",
                    actor_id=self.request.id,
                    payload={
                        "case_id": str(case.id),
                        "task_id": self.request.id,
                        "retry_count": self.request.retries,
                        "error": str(exc),
                    },
                )
            except ReviewCase.DoesNotExist:
                pass
            raise self.retry(exc=exc) from exc

        with transaction.atomic():
            case = ReviewCase.objects.select_for_update().get(id=case_id)

            recommendation = generate_source_only_recommendation(
                case=case,
                reason=str(exc),
            )

            emit_audit_event(
                case=case,
                event_type="case.recommendation.failed_fallback_review",
                correlation_id=case.correlation_id,
                actor_type="job",
                actor_id=self.request.id,
                payload={
                    "case_id": str(case.id),
                    "task_id": self.request.id,
                    "error": str(exc),
                    "case_status": case.status,
                    "fallback_recommendation_id": str(recommendation.id),
                },
            )

            create_audit_event(
                case=case,
                event_type="recommendation.failed_fallback_review",
                correlation_id=case.correlation_id,
                actor_type="job",
                actor_id=self.request.id,
                payload={
                    "task_id": self.request.id,
                    "error": str(exc),
                    "case_status": case.status,
                    "fallback_recommendation_id": str(recommendation.id),
                },
            )

            case.refresh_from_db(fields=["status", "review_status", "degraded_mode_active"])

            if case.status not in {
                CaseStatus.NEEDS_REVIEW,
                CaseStatus.ESCALATED,
                CaseStatus.APPROVED,
            }:
                transition_case(
                    case=case,
                    new_status=CaseStatus.NEEDS_REVIEW,
                    correlation_id=case.correlation_id,
                    actor_type="job",
                    actor_id=self.request.id,
                    message="Recommendation fallback routed case to review",
                    payload={
                        "task_id": self.request.id,
                        "stage": "recommendation",
                        "fallback_recommendation_id": str(recommendation.id),
                    },
                )

            logger.info(
                "Recommendation fallback completed",
                extra={
                    "extra_data": {
                        "case_id": str(case.id),
                        "correlation_id": case.correlation_id,
                        "stage": "recommendation",
                        "task_id": self.request.id,
                        "fallback_recommendation_id": str(recommendation.id),
                        "case_status": case.status,
                        "degraded_mode_active": case.degraded_mode_active,
                    }
                },
            )

            return str(recommendation.id)
