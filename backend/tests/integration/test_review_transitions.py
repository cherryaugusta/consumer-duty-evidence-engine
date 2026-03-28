from datetime import timedelta

import pytest
from django.utils import timezone

from apps.core.constants import CaseStatus, CaseType, Priority, ReviewStatus
from apps.recommendations.models import RecommendedAction
from apps.reviews.models import ReviewReasonCode, ReviewTask
from apps.reviews.services import approve_review_task, override_review_task


@pytest.mark.django_db
def test_approve_review_task_routes_case_through_transition_service(django_user_model):
    reviewer = django_user_model.objects.create_user(
        username="reviewer_approve",
        email="reviewer_approve@example.com",
        password="testpass123!",
    )

    case = reviewer.submitted_cases.model.objects.create(
        reference_code="TEST-REVIEW-APPROVE-001",
        title="Review approval transition test",
        case_type=CaseType.SUPPORT_REVIEW,
        priority=Priority.HIGH,
        submitted_by=reviewer,
        correlation_id="corr-test-review-approve-001",
        status=CaseStatus.NEEDS_REVIEW,
        review_status=ReviewStatus.UNASSIGNED,
        dedupe_key="test::review::approve::001",
        summary_snapshot={},
    )

    review_task = ReviewTask.objects.create(
        case=case,
        queue_name="default-review",
        status=ReviewStatus.UNASSIGNED,
        reason_code=ReviewReasonCode.LOW_CONFIDENCE,
        sla_due_at=timezone.now() + timedelta(hours=4),
    )

    approve_review_task(
        review_task=review_task,
        reviewer=reviewer,
        comment="Approved after analyst review.",
    )

    case.refresh_from_db()
    review_task.refresh_from_db()

    assert case.status == CaseStatus.APPROVED
    assert case.review_status == ReviewStatus.APPROVED
    assert review_task.status == ReviewStatus.APPROVED

    status_change_event = case.audit_events.filter(event_type="case.status_changed").latest(
        "created_at"
    )
    assert status_change_event.actor_type == "reviewer"
    assert status_change_event.actor_id == str(reviewer.id)
    assert status_change_event.payload["old_status"] == CaseStatus.NEEDS_REVIEW
    assert status_change_event.payload["new_status"] == CaseStatus.APPROVED

    assert case.audit_events.filter(event_type="review.task_approved").exists()


@pytest.mark.django_db
def test_override_review_task_routes_assessed_case_to_needs_review_via_transition_service(
    django_user_model,
):
    reviewer = django_user_model.objects.create_user(
        username="reviewer_override",
        email="reviewer_override@example.com",
        password="testpass123!",
    )

    case = reviewer.submitted_cases.model.objects.create(
        reference_code="TEST-REVIEW-OVERRIDE-001",
        title="Review override transition test",
        case_type=CaseType.SUPPORT_REVIEW,
        priority=Priority.MEDIUM,
        submitted_by=reviewer,
        correlation_id="corr-test-review-override-001",
        status=CaseStatus.ASSESSED,
        review_status=ReviewStatus.UNASSIGNED,
        dedupe_key="test::review::override::001",
        summary_snapshot={},
    )

    review_task = ReviewTask.objects.create(
        case=case,
        queue_name="default-review",
        status=ReviewStatus.UNASSIGNED,
        reason_code=ReviewReasonCode.LOW_CONFIDENCE,
        sla_due_at=timezone.now() + timedelta(hours=24),
    )

    override_review_task(
        review_task=review_task,
        reviewer=reviewer,
        recommended_action=RecommendedAction.REVIEW,
        comment="Keep in manual review.",
        override_reason_code="manual_sampling",
    )

    case.refresh_from_db()
    review_task.refresh_from_db()

    assert case.status == CaseStatus.NEEDS_REVIEW
    assert case.review_status == ReviewStatus.OVERRIDDEN
    assert review_task.status == ReviewStatus.OVERRIDDEN

    status_change_event = case.audit_events.filter(event_type="case.status_changed").latest(
        "created_at"
    )
    assert status_change_event.actor_type == "reviewer"
    assert status_change_event.actor_id == str(reviewer.id)
    assert status_change_event.payload["old_status"] == CaseStatus.ASSESSED
    assert status_change_event.payload["new_status"] == CaseStatus.NEEDS_REVIEW

    assert case.audit_events.filter(event_type="review.task_overridden").exists()


@pytest.mark.django_db
def test_override_review_task_rejects_invalid_bypass_status(django_user_model):
    reviewer = django_user_model.objects.create_user(
        username="reviewer_invalid_override",
        email="reviewer_invalid_override@example.com",
        password="testpass123!",
    )

    case = reviewer.submitted_cases.model.objects.create(
        reference_code="TEST-REVIEW-INVALID-001",
        title="Invalid review override state test",
        case_type=CaseType.SUPPORT_REVIEW,
        priority=Priority.MEDIUM,
        submitted_by=reviewer,
        correlation_id="corr-test-review-invalid-001",
        status=CaseStatus.APPROVED,
        review_status=ReviewStatus.UNASSIGNED,
        dedupe_key="test::review::invalid::001",
        summary_snapshot={},
    )

    review_task = ReviewTask.objects.create(
        case=case,
        queue_name="default-review",
        status=ReviewStatus.UNASSIGNED,
        reason_code=ReviewReasonCode.MANUAL_SAMPLING,
        sla_due_at=timezone.now() + timedelta(hours=24),
    )

    with pytest.raises(ValueError, match="Invalid case status for override action"):
        override_review_task(
            review_task=review_task,
            reviewer=reviewer,
            recommended_action=RecommendedAction.REVIEW,
            comment="Attempt invalid override.",
            override_reason_code="manual_sampling",
        )
