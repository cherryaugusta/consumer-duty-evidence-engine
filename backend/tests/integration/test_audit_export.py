import importlib.util
import json
from pathlib import Path

import pytest
from django.conf import settings

from apps.artifacts.models import SourceArtifact, SourceChannel
from apps.cases.models import ReviewCase
from apps.core.constants import CaseStatus, CaseType, Priority

REPO_ROOT = Path(__file__).resolve().parents[3]
EXPORT_SCRIPT_PATH = REPO_ROOT / "infra" / "scripts" / "export_audit_packet.py"

spec = importlib.util.spec_from_file_location(
    "export_audit_packet_module",
    EXPORT_SCRIPT_PATH,
)
export_audit_packet_module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(export_audit_packet_module)
export_audit_packet = export_audit_packet_module.export_audit_packet


@pytest.mark.django_db
def test_export_audit_packet_includes_required_top_level_sections(django_user_model):
    user = django_user_model.objects.create_user(
        username="export_test_user",
        email="export_test_user@example.com",
        password="testpass123!",
    )

    case = ReviewCase.objects.create(
        reference_code="TEST-AUDIT-001",
        title="Audit export integrity test case",
        case_type=CaseType.COMPLAINT_REVIEW,
        priority=Priority.HIGH,
        submitted_by=user,
        correlation_id="corr-test-audit-001",
        status=CaseStatus.NEEDS_REVIEW,
        dedupe_key="test::audit-export::001",
        summary_snapshot={"seed": "integration-test"},
    )

    storage_path = "test_exports/TEST-AUDIT-001/source.txt"
    media_file = Path(settings.MEDIA_ROOT) / storage_path
    media_file.parent.mkdir(parents=True, exist_ok=True)
    media_file.write_text(
        "Customer states the fee was not clearly explained and caused confusion.",
        encoding="utf-8",
    )

    SourceArtifact.objects.create(
        case=case,
        artifact_type="complaint",
        filename="source.txt",
        mime_type="text/plain",
        source_channel=SourceChannel.SEEDED_DEMO,
        storage_path=storage_path,
        sha256_checksum="test-checksum-audit-001",
        parse_status="parsed",
        text_length=67,
    )

    output_path = export_audit_packet("TEST-AUDIT-001")

    assert output_path.exists()

    payload = json.loads(output_path.read_text(encoding="utf-8"))

    assert "exported_at" in payload
    assert "case" in payload
    assert "artifacts" in payload
    assert "claims" in payload
    assert "evidence_links" in payload
    assert "assessments" in payload
    assert "contradictions" in payload
    assert "recommendation" in payload

    assert payload["case"]["reference_code"] == "TEST-AUDIT-001"
    assert payload["case"]["title"] == "Audit export integrity test case"
    assert payload["case"]["status"] == CaseStatus.NEEDS_REVIEW

    assert isinstance(payload["artifacts"], list)
    assert len(payload["artifacts"]) == 1
    assert payload["artifacts"][0]["filename"] == "source.txt"
    assert payload["artifacts"][0]["text"] == (
        "Customer states the fee was not clearly explained and caused confusion."
    )

    assert payload["claims"] == []
    assert payload["evidence_links"] == []
    assert payload["assessments"] == []
    assert payload["contradictions"] == []
    assert payload["recommendation"] is None
