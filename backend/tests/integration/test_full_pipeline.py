from pathlib import Path

import pytest
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

from apps.artifacts.models import SourceArtifact, SourceChannel
from apps.assessments.services import assess_case_support, detect_case_contradictions
from apps.cases.models import ReviewCase
from apps.core.constants import CaseStatus, CaseType, Priority
from apps.extraction.services import extract_claims_for_case
from apps.obligations.models import ConsumerDutyOutcome
from apps.obligations.services import map_case_outcomes
from apps.parsing.services import parse_artifact_to_sections
from apps.recommendations.services import generate_case_recommendation


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


@pytest.mark.django_db
def test_full_pipeline_runs_from_parsing_to_recommendation(django_user_model):
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
        status=CaseStatus.INGESTION_PENDING,
        dedupe_key="test::pipeline::001",
        summary_snapshot={},
    )

    artifacts_data = [
        {
            "artifact_type": "complaint",
            "filename": "complaint.txt",
            "text": (
                "Customer says support communications were confusing, the issue "
                "was not clearly explained, and they had to follow up again."
            ),
        },
        {
            "artifact_type": "support_transcript",
            "filename": "transcript.txt",
            "text": (
                "Support transcript shows the issue was acknowledged and discussed, "
                "but the explanation was brief and the customer remained uncertain."
            ),
        },
        {
            "artifact_type": "policy_excerpt",
            "filename": "policy.txt",
            "text": (
                "Support policy requires timely acknowledgement, clear explanations, "
                "and practical resolution support for routine servicing issues."
            ),
        },
    ]

    created_artifacts = []

    for index, artifact_data in enumerate(artifacts_data, start=1):
        storage_path = (
            f"test_pipeline/{case.reference_code}/{index:02d}_{artifact_data['filename']}"
        )
        media_file = Path(settings.MEDIA_ROOT) / storage_path
        media_file.parent.mkdir(parents=True, exist_ok=True)
        media_file.write_text(artifact_data["text"], encoding="utf-8")

        artifact = SourceArtifact.objects.create(
            case=case,
            artifact_type=artifact_data["artifact_type"],
            filename=artifact_data["filename"],
            mime_type="text/plain",
            source_channel=SourceChannel.SEEDED_DEMO,
            storage_path=storage_path,
            sha256_checksum=f"test-pipeline-checksum-{index}",
        )
        created_artifacts.append(artifact)

    assert case.status == CaseStatus.INGESTION_PENDING

    case.status = CaseStatus.PARSING
    case.save(update_fields=["status", "updated_at"])

    for artifact in created_artifacts:
        parse_artifact_to_sections(artifact)

    case.refresh_from_db()
    assert case.artifacts.count() == 3
    assert sum(artifact.sections.count() for artifact in created_artifacts) > 0

    case.status = CaseStatus.PARSED
    case.save(update_fields=["status", "updated_at"])
    case.refresh_from_db()
    assert case.status == CaseStatus.PARSED

    extract_claims_for_case(case)

    case.status = CaseStatus.EXTRACTED
    case.save(update_fields=["status", "updated_at"])
    case.refresh_from_db()
    assert case.status == CaseStatus.EXTRACTED
    assert case.claims.count() > 0

    map_case_outcomes(case)

    case.status = CaseStatus.MAPPED
    case.save(update_fields=["status", "updated_at"])
    case.refresh_from_db()
    assert case.status == CaseStatus.MAPPED
    assert case.evidence_links.count() > 0

    assess_case_support(case)
    detect_case_contradictions(case)

    case.status = CaseStatus.ASSESSED
    case.save(update_fields=["status", "updated_at"])
    case.refresh_from_db()
    assert case.status == CaseStatus.ASSESSED
    assert case.assessments.count() > 0

    generate_case_recommendation(case=case)
    case.refresh_from_db()

    assert case.status in {
        CaseStatus.NEEDS_REVIEW,
        CaseStatus.APPROVED,
        CaseStatus.ESCALATED,
    }

    try:
        recommendation = case.recommendation
    except ObjectDoesNotExist:
        pytest.fail("Expected recommendation to exist after full pipeline execution.")

    assert recommendation.recommended_action
    assert recommendation.executive_summary
    assert recommendation.confidence is not None
