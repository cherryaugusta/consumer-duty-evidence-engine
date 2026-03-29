from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.cases.models import ReviewCase
from apps.core.constants import CaseStatus, CaseType, Priority
from apps.evals.views import EvalCaseLookupView


@pytest.mark.django_db
def test_eval_case_lookup_returns_newest_matching_review_case(django_user_model):
    user = django_user_model.objects.create_user(
        username="eval_lookup_user",
        email="eval_lookup_user@example.com",
        password="testpass123!",
    )

    eval_case_id = "eval-001-unclear-fee"

    older_case = ReviewCase.objects.create(
        reference_code="TEST-EVAL-LOOKUP-OLDER-001",
        title="Eval: eval-001-unclear-fee older",
        case_type=CaseType.COMPLAINT_REVIEW,
        priority=Priority.MEDIUM,
        submitted_by=user,
        correlation_id="corr-test-eval-lookup-older-001",
        status=CaseStatus.NEEDS_REVIEW,
        dedupe_key="test::eval-lookup::older::001",
        summary_snapshot={},
        eval_case_id=eval_case_id,
    )

    newer_case = ReviewCase.objects.create(
        reference_code="TEST-EVAL-LOOKUP-NEWER-001",
        title="Eval: eval-001-unclear-fee newer",
        case_type=CaseType.COMPLAINT_REVIEW,
        priority=Priority.HIGH,
        submitted_by=user,
        correlation_id="corr-test-eval-lookup-newer-001",
        status=CaseStatus.APPROVED,
        dedupe_key="test::eval-lookup::newer::001",
        summary_snapshot={},
        eval_case_id=eval_case_id,
    )

    older_timestamp = timezone.now() - timedelta(days=1)
    newer_timestamp = timezone.now()

    ReviewCase.objects.filter(pk=older_case.pk).update(
        created_at=older_timestamp,
        updated_at=older_timestamp,
    )
    ReviewCase.objects.filter(pk=newer_case.pk).update(
        created_at=newer_timestamp,
        updated_at=newer_timestamp,
    )

    older_case.refresh_from_db()
    newer_case.refresh_from_db()

    request = APIRequestFactory().get(f"/api/evals/lookup/{eval_case_id}/")
    force_authenticate(request, user=user)

    response = EvalCaseLookupView.as_view()(request, eval_case_id=eval_case_id)

    assert response.status_code == 200
    assert response.data == {"case_id": str(newer_case.id)}
    assert response.data["case_id"] != str(older_case.id)


@pytest.mark.django_db
def test_eval_case_lookup_returns_404_when_no_matching_review_case(django_user_model):
    user = django_user_model.objects.create_user(
        username="eval_lookup_missing_user",
        email="eval_lookup_missing_user@example.com",
        password="testpass123!",
    )

    request = APIRequestFactory().get("/api/evals/lookup/eval-missing-case/")
    force_authenticate(request, user=user)

    response = EvalCaseLookupView.as_view()(
        request,
        eval_case_id="eval-missing-case",
    )

    assert response.status_code == 404
