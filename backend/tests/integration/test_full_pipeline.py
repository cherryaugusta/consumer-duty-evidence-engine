from pathlib import Path

import pytest
from django.conf import settings

from apps.artifacts.models import ParseStatus, SourceArtifact, SourceChannel
from apps.artifacts.tasks import queue_case_parsing_if_ready
from apps.cases.models import ReviewCase
from apps.core.constants import CaseStatus, CaseType, Priority
from apps.obligations.models import ConsumerDutyOutcome
from apps.parsing.tasks import parse_artifact_task


def create_required_outcomes() -> None:
    outcomes = [
        {
            "code": "products_services",
            "name": "Products and services",
            "description": "Product and service suitability.",
        },
        {
            "code": "price_value",
            "name": "Price and value",
            "description": "Fair price and value considerations.",
        },
        {
            "code": "fair_value",
            "name": "Fair value",
            "description": "Legacy fair value code used by current mapping rules.",
        },
        {
            "code": "consumer_understanding",
            "name": "Consumer understanding",
            "description": "Consumer understanding and clarity.",
        },
        {
            "code": "consumer_support",
            "name": "Consumer support",
            "description": "Consumer support responsiveness and accessibility.",
        },
    ]

    for outcome in outcomes:
        ConsumerDutyOutcome.objects.update_or_create(
            code=outcome["code"],
            defaults={
                "name": outcome["name"],
                "description": outcome["description"],
                "active": True,
            },
        )


def create_text_artifact(
    *,
    case: ReviewCase,
    artifact_type: str,
    filename: str,
    text: str,
    checksum: str,
) -> SourceArtifact:
    storage_path = f"test_pipeline/{case.reference_code}/{filename}"
    media_file = Path(settings.MEDIA_ROOT) / storage_path
    media_file.parent.mkdir(parents=True, exist_ok=True)
    media_file.write_text(text, encoding="utf-8")

    return SourceArtifact.objects.create(
        case=case,
        artifact_type=artifact_type,
        filename=filename,
        mime_type="text/plain",
        source_channel=SourceChannel.SEEDED_DEMO,
        storage_path=storage_path,
        sha256_checksum=checksum,
        parse_status=ParseStatus.PENDING,
    )


@pytest.mark.django_db
def test_full_pipeline_runs_end_to_end_via_tasks(django_user_model):
    create_required_outcomes()

    user = django_user_model.objects.create_user(
        username="pipeline_test_user",
        email="pipeline_test_user@example.com",
        password="testpass123!",
    )

    case = ReviewCase.objects.create(
        reference_code="TEST-PIPELINE-001",
        title="Full pipeline integration test case",
        case_type=CaseType.SUPPORT_REVIEW,
        priority=Priority.HIGH,
        submitted_by=user,
        correlation_id="corr-test-pipeline-001",
        status=CaseStatus.PARSING,
        dedupe_key="test::pipeline::001",
        summary_snapshot={},
    )

    create_text_artifact(
        case=case,
        artifact_type="complaint",
        filename="complaint.txt",
        text=(
            "Customer says support communications were confusing, the issue "
            "was not clearly explained, and they had to follow up again."
        ),
        checksum="test-pipeline-checksum-1",
    )
    create_text_artifact(
        case=case,
        artifact_type="support_transcript",
        filename="transcript.txt",
        text=(
            "Support transcript shows the issue was acknowledged and discussed, "
            "but the explanation was brief and the customer remained uncertain."
        ),
        checksum="test-pipeline-checksum-2",
    )
    create_text_artifact(
        case=case,
        artifact_type="policy_excerpt",
        filename="policy.txt",
        text=(
            "Support policy requires timely acknowledgement, clear explanations, "
            "and practical resolution support for routine servicing issues."
        ),
        checksum="test-pipeline-checksum-3",
    )

    queue_case_parsing_if_ready.delay(str(case.id))

    case.refresh_from_db()

    assert case.artifacts.count() == 3
    assert case.claims.count() > 0
    assert case.evidence_links.count() > 0
    assert case.assessments.count() > 0
    assert case.status in {
        CaseStatus.APPROVED,
        CaseStatus.NEEDS_REVIEW,
        CaseStatus.ESCALATED,
    }

    recommendation = case.recommendation
    assert recommendation.recommended_action
    assert recommendation.executive_summary
    assert recommendation.confidence is not None

    event_types = list(
        case.audit_events.order_by("created_at").values_list("event_type", flat=True)
    )

    expected_events = [
        "case.parsing.started",
        "case.parsing.completed",
        "case.status_changed",
        "case.extraction.started",
        "case.extraction.completed",
        "case.mapping.started",
        "case.mapping.completed",
        "case.assessment.started",
        "case.assessment.completed",
        "case.recommendation.started",
        "case.recommendation.completed",
    ]

    for expected_event in expected_events:
        assert expected_event in event_types

    status_changes = list(
        case.audit_events.filter(event_type="case.status_changed")
        .order_by("created_at")
        .values_list("payload", flat=True)
    )

    observed_transitions = {
        (payload["old_status"], payload["new_status"]) for payload in status_changes
    }

    expected_transitions = {
        (CaseStatus.PARSING, CaseStatus.PARSED),
        (CaseStatus.PARSED, CaseStatus.EXTRACTION_PENDING),
        (CaseStatus.EXTRACTION_PENDING, CaseStatus.EXTRACTED),
        (CaseStatus.EXTRACTED, CaseStatus.MAPPING_PENDING),
        (CaseStatus.MAPPING_PENDING, CaseStatus.MAPPED),
        (CaseStatus.MAPPED, CaseStatus.ASSESSMENT_PENDING),
        (CaseStatus.ASSESSMENT_PENDING, CaseStatus.ASSESSED),
    }

    for expected_transition in expected_transitions:
        assert expected_transition in observed_transitions

    assert any(
        payload["old_status"] == CaseStatus.ASSESSED
        and payload["new_status"]
        in {
            CaseStatus.APPROVED,
            CaseStatus.NEEDS_REVIEW,
            CaseStatus.ESCALATED,
        }
        for payload in status_changes
    )


@pytest.mark.django_db
def test_parse_artifact_task_is_idempotent_for_already_parsed_artifact(
    django_user_model,
    monkeypatch,
):
    user = django_user_model.objects.create_user(
        username="parse_idempotency_user",
        email="parse_idempotency_user@example.com",
        password="testpass123!",
    )

    case = ReviewCase.objects.create(
        reference_code="TEST-PARSE-IDEMPOTENT-001",
        title="Parsing idempotency test case",
        case_type=CaseType.SUPPORT_REVIEW,
        priority=Priority.MEDIUM,
        submitted_by=user,
        correlation_id="corr-test-parse-idempotent-001",
        status=CaseStatus.PARSING,
        dedupe_key="test::parse::idempotent::001",
        summary_snapshot={},
    )

    artifact = create_text_artifact(
        case=case,
        artifact_type="complaint",
        filename="complaint.txt",
        text="Customer says the explanation was unclear and required follow-up.",
        checksum="test-parse-idempotent-checksum-1",
    )

    monkeypatch.setattr("apps.parsing.tasks.finalize_case_parsing.delay", lambda _case_id: None)

    parse_artifact_task.delay(str(artifact.id))
    artifact.refresh_from_db()
    first_section_count = artifact.sections.count()
    first_audit_count = case.audit_events.count()

    assert artifact.parse_status == ParseStatus.PARSED
    assert first_section_count > 0

    parse_artifact_task.delay(str(artifact.id))
    artifact.refresh_from_db()

    assert artifact.parse_status == ParseStatus.PARSED
    assert artifact.sections.count() == first_section_count
    assert case.audit_events.count() == first_audit_count
