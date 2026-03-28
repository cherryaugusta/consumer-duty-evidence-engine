import pytest
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.cases.models import ReviewCase
from apps.cases.views import CaseRetryView
from apps.core.constants import CaseStatus, CaseType, Priority


@pytest.mark.django_db
def test_case_retry_view_retries_failed_case_via_transition_service(
    django_user_model,
    monkeypatch,
):
    user = django_user_model.objects.create_user(
        username="retry_view_user",
        email="retry_view_user@example.com",
        password="testpass123!",
    )

    case = ReviewCase.objects.create(
        reference_code="TEST-CASE-RETRY-001",
        title="Retry view integration test",
        case_type=CaseType.SUPPORT_REVIEW,
        priority=Priority.MEDIUM,
        submitted_by=user,
        correlation_id="corr-test-case-retry-001",
        status=CaseStatus.FAILED,
        dedupe_key="test::case::retry::001",
        summary_snapshot={},
    )

    queued_case_ids = []

    def fake_delay(case_id: str):
        queued_case_ids.append(case_id)

    monkeypatch.setattr(
        "apps.cases.views.queue_case_parsing_if_ready.delay",
        fake_delay,
    )

    request = APIRequestFactory().post(
        f"/api/cases/{case.id}/retry/",
        {"reason": "retry after operational fix"},
        format="json",
    )
    force_authenticate(request, user=user)

    response = CaseRetryView.as_view()(request, pk=case.id)

    case.refresh_from_db()

    assert response.status_code == 202
    assert response.data["case_id"] == str(case.id)
    assert response.data["status"] == CaseStatus.PARSING
    assert case.status == CaseStatus.PARSING
    assert queued_case_ids == [str(case.id)]

    status_change_events = list(
        case.audit_events.filter(event_type="case.status_changed")
        .order_by("created_at")
        .values_list("payload", flat=True)
    )

    assert len(status_change_events) == 2
    assert status_change_events[0]["old_status"] == CaseStatus.FAILED
    assert status_change_events[0]["new_status"] == CaseStatus.INGESTION_PENDING
    assert status_change_events[1]["old_status"] == CaseStatus.INGESTION_PENDING
    assert status_change_events[1]["new_status"] == CaseStatus.PARSING


@pytest.mark.django_db
def test_case_retry_view_rejects_non_failed_case(django_user_model, monkeypatch):
    user = django_user_model.objects.create_user(
        username="retry_view_invalid_user",
        email="retry_view_invalid_user@example.com",
        password="testpass123!",
    )

    case = ReviewCase.objects.create(
        reference_code="TEST-CASE-RETRY-002",
        title="Retry view invalid state test",
        case_type=CaseType.SUPPORT_REVIEW,
        priority=Priority.MEDIUM,
        submitted_by=user,
        correlation_id="corr-test-case-retry-002",
        status=CaseStatus.NEEDS_REVIEW,
        dedupe_key="test::case::retry::002",
        summary_snapshot={},
    )

    queued_case_ids = []

    def fake_delay(case_id: str):
        queued_case_ids.append(case_id)

    monkeypatch.setattr(
        "apps.cases.views.queue_case_parsing_if_ready.delay",
        fake_delay,
    )

    request = APIRequestFactory().post(
        f"/api/cases/{case.id}/retry/",
        {"reason": "should be rejected"},
        format="json",
    )
    force_authenticate(request, user=user)

    response = CaseRetryView.as_view()(request, pk=case.id)

    case.refresh_from_db()

    assert response.status_code == 400
    assert case.status == CaseStatus.NEEDS_REVIEW
    assert queued_case_ids == []
    assert case.audit_events.filter(event_type="case.status_changed").count() == 0
