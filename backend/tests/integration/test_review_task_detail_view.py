from __future__ import annotations

import pytest
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.cases.models import ReviewCase
from apps.core.constants import CaseStatus, CaseType, Priority, ReviewStatus
from apps.reviews.models import ReviewerAction, ReviewerActionType, ReviewReasonCode, ReviewTask
from apps.reviews.views import ReviewTaskDetailView


@pytest.mark.django_db
def test_review_task_detail_view_returns_review_task_with_actions(django_user_model):
    user = django_user_model.objects.create_user(
        username="review_detail_user",
        email="review_detail_user@example.com",
        password="testpass123!",
    )
    reviewer = django_user_model.objects.create_user(
        username="reviewer_detail_user",
        email="reviewer_detail_user@example.com",
        password="testpass123!",
        first_name="Detail",
        last_name="Reviewer",
    )

    case = ReviewCase.objects.create(
        reference_code="TEST-REVIEW-DETAIL-001",
        title="Review task detail view test",
        case_type=CaseType.COMPLAINT_REVIEW,
        priority=Priority.HIGH,
        submitted_by=user,
        correlation_id="corr-test-review-detail-001",
        status=CaseStatus.NEEDS_REVIEW,
        review_status=ReviewStatus.ASSIGNED,
        dedupe_key="test::review::detail::001",
        summary_snapshot={},
    )

    review_task = ReviewTask.objects.create(
        case=case,
        queue_name="default-review",
        assigned_to=reviewer,
        status=ReviewStatus.ASSIGNED,
        reason_code=ReviewReasonCode.CONTRADICTION,
        sla_due_at=case.created_at,
    )

    action = ReviewerAction.objects.create(
        review_task=review_task,
        reviewer=reviewer,
        action_type=ReviewerActionType.OVERRIDE,
        old_value={"case_status": "needs_review"},
        new_value={"case_status": "approved"},
        comment="Reviewer checked evidence.",
        override_reason_code="false_positive",
    )

    request = APIRequestFactory().get(f"/api/review-tasks/{review_task.id}/")
    force_authenticate(request, user=user)

    response = ReviewTaskDetailView.as_view()(request, pk=review_task.id)

    assert response.status_code == 200
    assert response.data["id"] == str(review_task.id)
    assert response.data["queue_name"] == "default-review"
    assert response.data["reason_code"] == ReviewReasonCode.CONTRADICTION
    assert response.data["status"] == ReviewStatus.ASSIGNED

    assert response.data["case"]["id"] == str(case.id)
    assert response.data["case"]["reference_code"] == case.reference_code
    assert response.data["case"]["status"] == case.status

    assert response.data["assigned_to"]["id"] == reviewer.id
    assert response.data["assigned_to"]["username"] == reviewer.username

    assert len(response.data["actions"]) == 1
    assert response.data["actions"][0]["id"] == str(action.id)
    assert response.data["actions"][0]["action_type"] == ReviewerActionType.OVERRIDE
    assert response.data["actions"][0]["comment"] == "Reviewer checked evidence."
    assert response.data["actions"][0]["override_reason_code"] == "false_positive"
    assert response.data["actions"][0]["reviewer"]["id"] == reviewer.id
    assert response.data["actions"][0]["reviewer"]["username"] == reviewer.username
