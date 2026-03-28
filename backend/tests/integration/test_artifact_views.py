from pathlib import Path

import pytest
from django.conf import settings
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.artifacts.models import DocumentSection, SourceArtifact, SourceChannel
from apps.artifacts.views import ArtifactDetailView, ArtifactSectionsView
from apps.cases.models import ReviewCase
from apps.core.constants import CaseStatus, CaseType, Priority


@pytest.mark.django_db
def test_artifact_detail_and_sections(django_user_model):
    user = django_user_model.objects.create_user(
        username="artifact_user",
        email="artifact_user@example.com",
        password="testpass123!",
    )

    case = ReviewCase.objects.create(
        reference_code="TEST-ARTIFACT-001",
        title="Artifact test",
        case_type=CaseType.SUPPORT_REVIEW,
        priority=Priority.MEDIUM,
        submitted_by=user,
        correlation_id="corr-artifact-001",
        status=CaseStatus.PARSING,
        dedupe_key="artifact::001",
        summary_snapshot={},
    )

    storage_path = f"test_artifacts/{case.reference_code}/file.txt"
    media_file = Path(settings.MEDIA_ROOT) / storage_path
    media_file.parent.mkdir(parents=True, exist_ok=True)
    media_file.write_text("Artifact text", encoding="utf-8")

    artifact = SourceArtifact.objects.create(
        case=case,
        artifact_type="complaint",
        filename="file.txt",
        mime_type="text/plain",
        source_channel=SourceChannel.SEEDED_DEMO,
        storage_path=storage_path,
        sha256_checksum="checksum",
    )

    section = DocumentSection.objects.create(
        artifact=artifact,
        section_index=1,
        heading="Test",
        text="Section text",
        char_start=0,
        char_end=12,
        page_number=1,
        parser_confidence=1.0,
    )

    factory = APIRequestFactory()

    # Artifact detail
    req1 = factory.get(f"/api/artifacts/{artifact.id}/")
    force_authenticate(req1, user=user)
    res1 = ArtifactDetailView.as_view()(req1, pk=artifact.id)

    assert res1.status_code == 200
    assert res1.data["id"] == str(artifact.id)

    # Sections
    req2 = factory.get(f"/api/artifacts/{artifact.id}/sections/")
    force_authenticate(req2, user=user)
    res2 = ArtifactSectionsView.as_view()(req2, pk=artifact.id)

    assert res2.status_code == 200
    assert len(res2.data) == 1
    assert res2.data[0]["id"] == str(section.id)
