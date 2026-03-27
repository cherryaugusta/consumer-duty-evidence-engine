from pathlib import Path

import pytest
from django.conf import settings

from apps.artifacts.models import SourceArtifact, SourceChannel
from apps.cases.models import ReviewCase
from apps.core.constants import CaseStatus, CaseType, Priority
from apps.extraction.services import extract_claims_for_case
from apps.parsing.services import parse_artifact_to_sections


@pytest.mark.django_db
def test_extract_claims_produces_valid_non_empty_and_deterministic_output(
    django_user_model,
):
    user = django_user_model.objects.create_user(
        username="extraction_test_user",
        email="extraction_test_user@example.com",
        password="testpass123!",
    )

    case = ReviewCase.objects.create(
        reference_code="TEST-EXTRACT-001",
        title="Extraction schema validation test case",
        case_type=CaseType.COMPLAINT_REVIEW,
        priority=Priority.HIGH,
        submitted_by=user,
        correlation_id="corr-test-extract-001",
        status=CaseStatus.PARSED,
        dedupe_key="test::extract::001",
        summary_snapshot={},
    )

    storage_path = "test_extraction/TEST-EXTRACT-001/01_complaint.txt"
    media_file = Path(settings.MEDIA_ROOT) / storage_path
    media_file.parent.mkdir(parents=True, exist_ok=True)
    media_file.write_text(
        (
            "Customer says the monthly fee was not clearly explained during onboarding "
            "and that the later disclosure remained confusing."
        ),
        encoding="utf-8",
    )

    artifact = SourceArtifact.objects.create(
        case=case,
        artifact_type="complaint",
        filename="complaint.txt",
        mime_type="text/plain",
        source_channel=SourceChannel.SEEDED_DEMO,
        storage_path=storage_path,
        sha256_checksum="test-extract-checksum-001",
    )

    parse_artifact_to_sections(artifact)

    extract_claims_for_case(case)
    case.refresh_from_db()

    first_claims = list(
        case.claims.select_related("source_section")
        .order_by("id")
        .values(
            "claim_type",
            "claim_text",
            "normalized_claim_text",
            "source_section_id",
            "extraction_confidence",
            "schema_valid",
            "extraction_version",
        )
    )

    assert len(first_claims) > 0

    for claim in first_claims:
        assert claim["claim_type"]
        assert claim["claim_text"]
        assert claim["claim_text"].strip() == claim["claim_text"]
        assert claim["normalized_claim_text"]
        assert claim["normalized_claim_text"].strip() == claim["normalized_claim_text"]
        assert claim["source_section_id"] is not None
        assert claim["extraction_confidence"] is not None
        assert 0.0 <= claim["extraction_confidence"] <= 1.0
        assert claim["schema_valid"] is True
        assert claim["extraction_version"]

    case.claims.all().delete()

    extract_claims_for_case(case)
    case.refresh_from_db()

    second_claims = list(
        case.claims.select_related("source_section")
        .order_by("id")
        .values(
            "claim_type",
            "claim_text",
            "normalized_claim_text",
            "source_section_id",
            "extraction_confidence",
            "schema_valid",
            "extraction_version",
        )
    )

    assert second_claims == first_claims
