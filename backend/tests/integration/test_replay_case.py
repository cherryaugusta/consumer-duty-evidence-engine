import importlib.util
from pathlib import Path

import pytest

from apps.artifacts.models import SourceArtifact, SourceChannel
from apps.cases.models import ReviewCase
from apps.core.constants import CaseStatus, CaseType, Priority

REPO_ROOT = Path(__file__).resolve().parents[3]
REPLAY_SCRIPT_PATH = REPO_ROOT / "infra" / "scripts" / "replay_case.py"

spec = importlib.util.spec_from_file_location(
    "replay_case_module",
    REPLAY_SCRIPT_PATH,
)
replay_case_module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(replay_case_module)
replay_case = replay_case_module.replay_case


@pytest.mark.django_db
def test_replay_case_is_deterministic_for_key_summary_fields(django_user_model, settings):
    user = django_user_model.objects.create_user(
        username="replay_test_user",
        email="replay_test_user@example.com",
        password="testpass123!",
    )

    case = ReviewCase.objects.create(
        reference_code="TEST-REPLAY-001",
        title="Replay determinism integration test case",
        case_type=CaseType.SUPPORT_REVIEW,
        priority=Priority.HIGH,
        submitted_by=user,
        correlation_id="corr-test-replay-001",
        status=CaseStatus.INGESTION_PENDING,
        dedupe_key="test::replay::001",
        summary_snapshot={},
    )

    artifacts = [
        {
            "artifact_type": "complaint",
            "filename": "complaint.txt",
            "text": (
                "Customer says support communications were confusing and the issue "
                "was not resolved clearly on first contact."
            ),
        },
        {
            "artifact_type": "policy_excerpt",
            "filename": "policy.txt",
            "text": (
                "Support policy requires clear explanations, timely acknowledgement, "
                "and practical resolution support for routine servicing issues."
            ),
        },
    ]

    for index, artifact_data in enumerate(artifacts, start=1):
        storage_path = f"test_replay/{case.reference_code}/{index:02d}_{artifact_data['filename']}"
        media_file = Path(settings.MEDIA_ROOT) / storage_path
        media_file.parent.mkdir(parents=True, exist_ok=True)
        media_file.write_text(artifact_data["text"], encoding="utf-8")

        SourceArtifact.objects.create(
            case=case,
            artifact_type=artifact_data["artifact_type"],
            filename=artifact_data["filename"],
            mime_type="text/plain",
            source_channel=SourceChannel.SEEDED_DEMO,
            storage_path=storage_path,
            sha256_checksum=f"test-replay-checksum-{index}",
        )

    replay_case("TEST-REPLAY-001")
    case.refresh_from_db()

    before = {
        "status": case.status,
        "review_status": case.review_status,
        "claims": case.claims.count(),
        "assessments": case.assessments.count(),
        "recommendation": getattr(case.recommendation, "recommended_action", None),
    }

    replay_case("TEST-REPLAY-001")
    case.refresh_from_db()

    after = {
        "status": case.status,
        "review_status": case.review_status,
        "claims": case.claims.count(),
        "assessments": case.assessments.count(),
        "recommendation": getattr(case.recommendation, "recommended_action", None),
    }

    assert after == before
