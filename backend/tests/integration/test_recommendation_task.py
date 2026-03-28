import pytest

from apps.cases.models import ReviewCase
from apps.core.constants import CaseStatus, CaseType, Priority
from apps.recommendations.models import RecommendedAction
from apps.recommendations.tasks import recommend_case_task
from apps.reviews.models import ReviewTask


@pytest.mark.django_db
def test_recommend_case_task_skips_when_case_not_assessed(django_user_model):
    user = django_user_model.objects.create_user(
        username="recommend_skip_user",
        email="recommend_skip_user@example.com",
        password="testpass123!",
    )

    case = ReviewCase.objects.create(
        reference_code="TEST-RECOMMEND-SKIP-001",
        title="Recommendation skip test case",
        case_type=CaseType.SUPPORT_REVIEW,
        priority=Priority.MEDIUM,
        submitted_by=user,
        correlation_id="corr-test-recommend-skip-001",
        status=CaseStatus.NEEDS_REVIEW,
        dedupe_key="test::recommend::skip::001",
        summary_snapshot={},
    )

    result = recommend_case_task.delay(str(case.id)).get()

    case.refresh_from_db()

    assert result["case_id"] == str(case.id)
    assert result["skipped"] is True
    assert result["case_status"] == CaseStatus.NEEDS_REVIEW
    assert case.audit_events.filter(event_type="case.recommendation.started").count() == 0
    assert case.audit_events.filter(event_type="recommendation.started").count() == 0


@pytest.mark.django_db
def test_recommend_case_task_retries_then_uses_source_only_fallback(
    django_user_model,
    monkeypatch,
):
    user = django_user_model.objects.create_user(
        username="recommend_fallback_user",
        email="recommend_fallback_user@example.com",
        password="testpass123!",
    )

    case = ReviewCase.objects.create(
        reference_code="TEST-RECOMMEND-FALLBACK-001",
        title="Recommendation fallback test case",
        case_type=CaseType.SUPPORT_REVIEW,
        priority=Priority.HIGH,
        submitted_by=user,
        correlation_id="corr-test-recommend-fallback-001",
        status=CaseStatus.ASSESSED,
        dedupe_key="test::recommend::fallback::001",
        summary_snapshot={},
    )

    retry_calls = {"count": 0}

    def fake_generate_case_recommendation(*, case):
        raise RuntimeError("synthetic recommendation failure")

    def fake_retry(*args, **kwargs):
        retry_calls["count"] += 1
        raise kwargs["exc"]

    monkeypatch.setattr(
        "apps.recommendations.tasks.generate_case_recommendation",
        fake_generate_case_recommendation,
    )
    monkeypatch.setattr(
        recommend_case_task,
        "retry",
        fake_retry,
    )

    with pytest.raises(RuntimeError, match="synthetic recommendation failure"):
        recommend_case_task.apply(
            args=[str(case.id)],
            throw=True,
        )

    assert retry_calls["count"] == 1

    case.refresh_from_db()
    assert case.audit_events.filter(event_type="case.recommendation.retrying").count() == 1

    recommend_case_task.apply(
        args=[str(case.id)],
        throw=True,
        retries=1,
    )

    case.refresh_from_db()

    assert case.status == CaseStatus.NEEDS_REVIEW
    assert case.degraded_mode_active is True
    assert case.recommendation.recommended_action == RecommendedAction.REVIEW
    assert case.recommendation.model_version == "source-only-fallback-v1"
    assert ReviewTask.objects.filter(case=case).exists()

    assert (
        case.audit_events.filter(event_type="case.recommendation.failed_fallback_review").count()
        == 1
    )
    assert case.audit_events.filter(event_type="recommendation.failed_fallback_review").count() == 1
    assert case.audit_events.filter(event_type="recommendation.source_only_generated").count() == 1

    status_change_events = case.audit_events.filter(event_type="case.status_changed").order_by(
        "created_at"
    )
    assert status_change_events.exists()
    last_status_change = status_change_events.last()
    assert last_status_change.payload["old_status"] == CaseStatus.ASSESSED
    assert last_status_change.payload["new_status"] == CaseStatus.NEEDS_REVIEW


@pytest.mark.django_db
def test_recommend_case_task_fallback_does_not_retransition_terminal_case(
    django_user_model,
    monkeypatch,
):
    user = django_user_model.objects.create_user(
        username="recommend_terminal_user",
        email="recommend_terminal_user@example.com",
        password="testpass123!",
    )

    case = ReviewCase.objects.create(
        reference_code="TEST-RECOMMEND-TERMINAL-001",
        title="Recommendation terminal fallback test case",
        case_type=CaseType.SUPPORT_REVIEW,
        priority=Priority.HIGH,
        submitted_by=user,
        correlation_id="corr-test-recommend-terminal-001",
        status=CaseStatus.APPROVED,
        degraded_mode_active=False,
        dedupe_key="test::recommend::terminal::001",
        summary_snapshot={},
    )

    result = recommend_case_task.delay(str(case.id)).get()

    case.refresh_from_db()

    assert result["skipped"] is True
    assert result["case_status"] == CaseStatus.APPROVED
    assert case.audit_events.filter(event_type="case.status_changed").count() == 0
