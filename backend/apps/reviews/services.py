from __future__ import annotations

from datetime import timedelta
from typing import Any

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from apps.audits.services import create_audit_event
from apps.cases.models import ReviewCase
from apps.cases.state_machine import assert_transition
from apps.core.constants import CaseStatus, Priority, ReviewStatus
from apps.recommendations.models import Recommendation, RecommendedAction
from apps.reviews.models import ReviewerAction, ReviewerActionType, ReviewReasonCode, ReviewTask

User = get_user_model()


def _default_sla_due_at(case: ReviewCase):
    now = timezone.now()

    if case.priority == Priority.CRITICAL:
        return now + timedelta(hours=2)
    if case.priority == Priority.HIGH:
        return now + timedelta(hours=4)
    if case.priority == Priority.MEDIUM:
        return now + timedelta(hours=24)
    return now + timedelta(hours=48)


def determine_review_reason(case: ReviewCase) -> str:
    if case.degraded_mode_active:
        return ReviewReasonCode.MODEL_UNAVAILABLE

    if case.contradiction_flags.exists():
        return ReviewReasonCode.CONTRADICTION

    if case.assessments.filter(
        status__in=[
            "missing_support",
            "contradictory_support",
            "stale_support",
        ]
    ).exists():
        return ReviewReasonCode.MISSING_SUPPORT

    if case.assessments.filter(requires_review=True).exists():
        return ReviewReasonCode.LOW_CONFIDENCE

    return ReviewReasonCode.MANUAL_SAMPLING


@transaction.atomic
def create_or_update_review_task(
    *,
    case: ReviewCase,
    reason_code: str | None = None,
    queue_name: str = "default-review",
) -> ReviewTask:
    task, created = ReviewTask.objects.select_for_update().get_or_create(
        case=case,
        defaults={
            "queue_name": queue_name,
            "reason_code": reason_code or determine_review_reason(case),
            "status": ReviewStatus.UNASSIGNED,
            "sla_due_at": _default_sla_due_at(case),
        },
    )

    if not created:
        task.queue_name = queue_name
        task.reason_code = reason_code or determine_review_reason(case)
        if task.status in {
            ReviewStatus.APPROVED,
            ReviewStatus.ESCALATED,
            ReviewStatus.CLOSED,
        }:
            task.status = ReviewStatus.UNASSIGNED
        task.sla_due_at = _default_sla_due_at(case)
        task.save(
            update_fields=[
                "queue_name",
                "reason_code",
                "status",
                "sla_due_at",
                "updated_at",
            ]
        )

    if case.review_status == ReviewStatus.UNASSIGNED:
        case.review_status = ReviewStatus.UNASSIGNED
        case.save(update_fields=["review_status", "updated_at"])

    create_audit_event(
        case=case,
        event_type="review.task_created" if created else "review.task_updated",
        correlation_id=case.correlation_id,
        payload={
            "review_task_id": str(task.id),
            "reason_code": task.reason_code,
            "queue_name": task.queue_name,
            "status": task.status,
            "sla_due_at": task.sla_due_at.isoformat(),
        },
    )

    return task


@transaction.atomic
def assign_review_task(
    *,
    review_task: ReviewTask,
    reviewer: User,
    assignee: User | None = None,
    comment: str = "",
) -> ReviewTask:
    assignee = assignee or reviewer

    review_task.assigned_to = assignee
    review_task.status = ReviewStatus.ASSIGNED
    review_task.save(update_fields=["assigned_to", "status", "updated_at"])

    case = review_task.case
    case.assigned_reviewer = assignee
    case.review_status = ReviewStatus.ASSIGNED
    case.save(update_fields=["assigned_reviewer", "review_status", "updated_at"])

    ReviewerAction.objects.create(
        review_task=review_task,
        reviewer=reviewer,
        action_type=ReviewerActionType.CLOSE,
        old_value={},
        new_value={
            "assigned_to": assignee.id,
            "status": ReviewStatus.ASSIGNED,
        },
        comment=comment or "Review task assigned.",
    )

    create_audit_event(
        case=case,
        event_type="review.task_assigned",
        correlation_id=case.correlation_id,
        actor_type="reviewer",
        actor_id=str(reviewer.id),
        payload={
            "review_task_id": str(review_task.id),
            "assigned_to": assignee.username,
            "assigned_to_id": assignee.id,
        },
    )

    return review_task


def _transition_case(case: ReviewCase, new_status: str) -> None:
    if case.status != new_status:
        assert_transition(case.status, new_status)
        case.status = new_status
        case.save(update_fields=["status", "updated_at"])


@transaction.atomic
def approve_review_task(
    *,
    review_task: ReviewTask,
    reviewer: User,
    comment: str,
) -> ReviewTask:
    case = review_task.case

    _transition_case(case, CaseStatus.APPROVED)

    review_task.status = ReviewStatus.APPROVED
    review_task.save(update_fields=["status", "updated_at"])

    case.review_status = ReviewStatus.APPROVED
    case.save(update_fields=["review_status", "updated_at"])

    ReviewerAction.objects.create(
        review_task=review_task,
        reviewer=reviewer,
        action_type=ReviewerActionType.APPROVE,
        old_value={"case_status": case.status},
        new_value={"case_status": CaseStatus.APPROVED},
        comment=comment,
    )

    create_audit_event(
        case=case,
        event_type="review.task_approved",
        correlation_id=case.correlation_id,
        actor_type="reviewer",
        actor_id=str(reviewer.id),
        payload={
            "review_task_id": str(review_task.id),
            "comment": comment,
        },
    )

    return review_task


@transaction.atomic
def override_review_task(
    *,
    review_task: ReviewTask,
    reviewer: User,
    recommended_action: str,
    comment: str,
    override_reason_code: str,
    recommended_priority: str | None = None,
    executive_summary: str | None = None,
    structured_rationale: dict[str, Any] | None = None,
) -> ReviewTask:
    case = review_task.case

    recommendation, _ = Recommendation.objects.get_or_create(
        case=case,
        defaults={
            "recommended_action": recommended_action,
            "recommended_priority": recommended_priority or case.priority,
            "executive_summary": executive_summary or "Reviewer override applied.",
            "structured_rationale": structured_rationale or {},
            "confidence": 0.5,
            "citation_count": case.evidence_links.count(),
            "model_version": "reviewer-override",
        },
    )

    recommendation.recommended_action = recommended_action
    recommendation.recommended_priority = (
        recommended_priority or recommendation.recommended_priority
    )
    if executive_summary:
        recommendation.executive_summary = executive_summary
    if structured_rationale is not None:
        recommendation.structured_rationale = structured_rationale
    recommendation.model_version = "reviewer-override"
    recommendation.save()

    old_case_status = case.status

    if recommended_action == RecommendedAction.APPROVE:
        _transition_case(case, CaseStatus.APPROVED)
    elif recommended_action == RecommendedAction.ESCALATE:
        _transition_case(case, CaseStatus.ESCALATED)
    else:
        if case.status != CaseStatus.NEEDS_REVIEW:
            if case.status == CaseStatus.ASSESSED:
                _transition_case(case, CaseStatus.NEEDS_REVIEW)
            else:
                case.status = CaseStatus.NEEDS_REVIEW
                case.save(update_fields=["status", "updated_at"])

    review_task.status = ReviewStatus.OVERRIDDEN
    review_task.save(update_fields=["status", "updated_at"])

    case.review_status = ReviewStatus.OVERRIDDEN
    case.save(update_fields=["review_status", "updated_at"])

    ReviewerAction.objects.create(
        review_task=review_task,
        reviewer=reviewer,
        action_type=ReviewerActionType.OVERRIDE,
        old_value={
            "case_status": old_case_status,
            "recommended_action": recommendation.recommended_action,
        },
        new_value={
            "case_status": case.status,
            "recommended_action": recommended_action,
            "recommended_priority": recommendation.recommended_priority,
        },
        comment=comment,
        override_reason_code=override_reason_code,
    )

    create_audit_event(
        case=case,
        event_type="review.task_overridden",
        correlation_id=case.correlation_id,
        actor_type="reviewer",
        actor_id=str(reviewer.id),
        payload={
            "review_task_id": str(review_task.id),
            "recommended_action": recommended_action,
            "recommended_priority": recommendation.recommended_priority,
            "override_reason_code": override_reason_code,
            "comment": comment,
        },
    )

    return review_task


@transaction.atomic
def escalate_review_task(
    *,
    review_task: ReviewTask,
    reviewer: User,
    comment: str,
) -> ReviewTask:
    case = review_task.case

    _transition_case(case, CaseStatus.ESCALATED)

    review_task.status = ReviewStatus.ESCALATED
    review_task.save(update_fields=["status", "updated_at"])

    case.review_status = ReviewStatus.ESCALATED
    case.save(update_fields=["review_status", "updated_at"])

    ReviewerAction.objects.create(
        review_task=review_task,
        reviewer=reviewer,
        action_type=ReviewerActionType.ESCALATE,
        old_value={},
        new_value={"case_status": CaseStatus.ESCALATED},
        comment=comment,
    )

    create_audit_event(
        case=case,
        event_type="review.task_escalated",
        correlation_id=case.correlation_id,
        actor_type="reviewer",
        actor_id=str(reviewer.id),
        payload={
            "review_task_id": str(review_task.id),
            "comment": comment,
        },
    )

    return review_task
