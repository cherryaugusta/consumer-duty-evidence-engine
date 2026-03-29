from pathlib import Path

import pytest
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.artifacts.models import ParseStatus, SourceArtifact, SourceChannel
from apps.artifacts.services import create_artifact_from_upload
from apps.cases.models import ReviewCase
from apps.core.constants import CaseStatus, CaseType, Priority


@pytest.mark.django_db
def test_create_artifact_from_upload_dedupes_same_file_for_same_case(django_user_model):
    user = django_user_model.objects.create_user(
        username="artifact_dedupe_user",
        email="artifact_dedupe_user@example.com",
        password="testpass123!",
    )

    case = ReviewCase.objects.create(
        reference_code="TEST-ARTIFACT-DEDUPE-001",
        title="Artifact dedupe integration test",
        case_type=CaseType.SUPPORT_REVIEW,
        priority=Priority.MEDIUM,
        submitted_by=user,
        correlation_id="corr-artifact-dedupe-001",
        status=CaseStatus.INGESTION_PENDING,
        dedupe_key="test::artifact::dedupe::001",
        summary_snapshot={},
    )

    file_bytes = (
        b"Customer says the disclosure wording was unclear and the fee explanation "
        b"was inconsistent across materials."
    )

    first_upload = SimpleUploadedFile(
        "Disclosure Copy.PDF",
        file_bytes,
        content_type="application/pdf",
    )
    second_upload = SimpleUploadedFile(
        "Disclosure Copy.PDF",
        file_bytes,
        content_type="application/pdf",
    )

    artifact_one = create_artifact_from_upload(
        case=case,
        uploaded_file=first_upload,
        artifact_type="disclosure",
        uploaded_by=user,
        correlation_id="corr-artifact-dedupe-001",
    )

    artifact_two = create_artifact_from_upload(
        case=case,
        uploaded_file=second_upload,
        artifact_type="disclosure",
        uploaded_by=user,
        correlation_id="corr-artifact-dedupe-001",
    )

    case.refresh_from_db()
    artifact_one.refresh_from_db()

    artifacts = SourceArtifact.objects.filter(case=case)

    assert artifact_one.id == artifact_two.id
    assert artifacts.count() == 1

    artifact = artifacts.get()
    assert artifact.case == case
    assert artifact.artifact_type == "disclosure"
    assert artifact.filename == "DisclosureCopy.pdf"
    assert artifact.source_channel == SourceChannel.UPLOAD
    assert artifact.parse_status == ParseStatus.PENDING
    assert artifact.text_length == 0

    absolute_path = Path(settings.MEDIA_ROOT) / artifact.storage_path
    assert absolute_path.exists()
    assert absolute_path.read_bytes() == file_bytes

    upload_events = case.audit_events.filter(event_type="artifact.uploaded")
    assert upload_events.count() == 1

    upload_event = upload_events.get()
    assert upload_event.actor_type == "user"
    assert upload_event.actor_id == str(user.id)
    assert upload_event.correlation_id == "corr-artifact-dedupe-001"
    assert upload_event.payload["artifact_id"] == str(artifact.id)
    assert upload_event.payload["artifact_type"] == "disclosure"
    assert upload_event.payload["filename"] == "DisclosureCopy.pdf"
    assert upload_event.payload["mime_type"] == "application/pdf"
    assert upload_event.payload["storage_path"] == artifact.storage_path
    assert upload_event.payload["sha256_checksum"] == artifact.sha256_checksum
