from pathlib import Path

import pytest
from django.conf import settings
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.artifacts.models import DocumentSection, SourceArtifact, SourceChannel
from apps.assessments.models import ContradictionFlag, SupportAssessment
from apps.audits.services import create_audit_event
from apps.cases.models import ReviewCase
from apps.cases.views import (
    CaseAssessmentsView,
    CaseAuditEventsView,
    CaseClaimsView,
    CaseEvidenceLinksView,
    CaseTimelineView,
)
from apps.core.constants import CaseStatus, CaseType, Priority
from apps.extraction.models import Claim
from apps.obligations.models import ConsumerDutyOutcome, EvidenceLink


def create_section(case: ReviewCase, index: int = 1) -> DocumentSection:
    storage_path = f"test_sections/{case.reference_code}/{index:02d}.txt"
    media_file = Path(settings.MEDIA_ROOT) / storage_path
    media_file.parent.mkdir(parents=True, exist_ok=True)
    media_file.write_text("Test section content", encoding="utf-8")

    artifact = SourceArtifact.objects.create(
        case=case,
        artifact_type="complaint",
        filename=f"section_{index}.txt",
        mime_type="text/plain",
        source_channel=SourceChannel.SEEDED_DEMO,
        storage_path=storage_path,
        sha256_checksum=f"test-section-checksum-{case.reference_code}-{index}",
    )

    return DocumentSection.objects.create(
        artifact=artifact,
        section_index=index,
        heading=f"Section {index}",
        text="Test section content",
        char_start=0,
        char_end=len("Test section content"),
        page_number=1,
        parser_confidence=1.0,
    )


@pytest.mark.django_db
def test_case_claims_view_returns_case_claims(django_user_model):
    user = django_user_model.objects.create_user(
        username="case_claims_user",
        email="case_claims_user@example.com",
        password="testpass123!",
    )

    case = ReviewCase.objects.create(
        reference_code="TEST-CASE-CLAIMS-001",
        title="Case claims view test",
        case_type=CaseType.SUPPORT_REVIEW,
        priority=Priority.MEDIUM,
        submitted_by=user,
        correlation_id="corr-test-case-claims-001",
        status=CaseStatus.EXTRACTED,
        dedupe_key="test::case::claims::001",
        summary_snapshot={},
    )

    section = create_section(case)

    claim = Claim.objects.create(
        case=case,
        claim_type="support_delay",
        claim_text="Customer experienced support delay.",
        normalized_claim_text="customer experienced support delay",
        source_section=section,
        extraction_confidence=0.91,
        schema_valid=True,
        extraction_version="test-v1",
    )

    request = APIRequestFactory().get(f"/api/cases/{case.id}/claims/")
    force_authenticate(request, user=user)

    response = CaseClaimsView.as_view()(request, pk=case.id)

    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]["id"] == str(claim.id)
    assert str(response.data[0]["case"]) == str(case.id)


@pytest.mark.django_db
def test_case_evidence_links_view_returns_case_links(django_user_model):
    user = django_user_model.objects.create_user(
        username="case_links_user",
        email="case_links_user@example.com",
        password="testpass123!",
    )

    case = ReviewCase.objects.create(
        reference_code="TEST-CASE-LINKS-001",
        title="Case evidence links view test",
        case_type=CaseType.SUPPORT_REVIEW,
        priority=Priority.MEDIUM,
        submitted_by=user,
        correlation_id="corr-test-case-links-001",
        status=CaseStatus.MAPPED,
        dedupe_key="test::case::links::001",
        summary_snapshot={},
    )

    section = create_section(case)

    outcome = ConsumerDutyOutcome.objects.create(
        code="consumer_support",
        name="Consumer support",
        description="Consumer support responsiveness and accessibility.",
        active=True,
    )

    claim = Claim.objects.create(
        case=case,
        claim_type="support_delay",
        claim_text="Customer experienced support delay.",
        normalized_claim_text="customer experienced support delay",
        source_section=section,
        extraction_confidence=0.91,
        schema_valid=True,
        extraction_version="test-v1",
    )

    link = EvidenceLink.objects.create(
        case=case,
        claim=claim,
        outcome=outcome,
        section=section,
        link_type="supporting",
        rationale="Section supports the delay claim.",
        score=0.85,
    )

    request = APIRequestFactory().get(f"/api/cases/{case.id}/evidence-links/")
    force_authenticate(request, user=user)

    response = CaseEvidenceLinksView.as_view()(request, pk=case.id)

    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]["id"] == str(link.id)
    assert str(response.data[0]["case"]) == str(case.id)


@pytest.mark.django_db
def test_case_assessments_view_returns_assessments_and_contradictions(django_user_model):
    user = django_user_model.objects.create_user(
        username="case_assessments_user",
        email="case_assessments_user@example.com",
        password="testpass123!",
    )

    case = ReviewCase.objects.create(
        reference_code="TEST-CASE-ASSESSMENTS-001",
        title="Case assessments view test",
        case_type=CaseType.SUPPORT_REVIEW,
        priority=Priority.HIGH,
        submitted_by=user,
        correlation_id="corr-test-case-assessments-001",
        status=CaseStatus.ASSESSED,
        dedupe_key="test::case::assessments::001",
        summary_snapshot={},
    )

    section = create_section(case)

    outcome = ConsumerDutyOutcome.objects.create(
        code="price_value",
        name="Price and value",
        description="Fair price and value considerations.",
        active=True,
    )

    claim = Claim.objects.create(
        case=case,
        claim_type="unclear_fee",
        claim_text="Customer could not understand the monthly fee.",
        normalized_claim_text="customer could not understand the monthly fee",
        source_section=section,
        extraction_confidence=0.88,
        schema_valid=True,
        extraction_version="test-v1",
    )

    assessment = SupportAssessment.objects.create(
        case=case,
        claim=claim,
        outcome=outcome,
        status="weak_support",
        confidence=0.72,
        requires_review=True,
        assessment_reason="Support exists but is weak.",
        rules_triggered=["weak_support"],
        model_version="rules-v1",
    )

    contradiction = ContradictionFlag.objects.create(
        case=case,
        claim=claim,
        primary_section=section,
        secondary_section=section,
        contradiction_type="statement_conflict",
        severity="medium",
        reason="Two statements conflict.",
    )

    request = APIRequestFactory().get(f"/api/cases/{case.id}/assessments/")
    force_authenticate(request, user=user)

    response = CaseAssessmentsView.as_view()(request, pk=case.id)

    assert response.status_code == 200
    assert "assessments" in response.data
    assert "contradictions" in response.data
    assert len(response.data["assessments"]) == 1
    assert len(response.data["contradictions"]) == 1
    assert response.data["assessments"][0]["id"] == str(assessment.id)
    assert response.data["contradictions"][0]["id"] == str(contradiction.id)


@pytest.mark.django_db
def test_case_audit_events_and_timeline_views_return_ordered_events(django_user_model):
    user = django_user_model.objects.create_user(
        username="case_audit_user",
        email="case_audit_user@example.com",
        password="testpass123!",
    )

    case = ReviewCase.objects.create(
        reference_code="TEST-CASE-AUDIT-001",
        title="Case audit views test",
        case_type=CaseType.SUPPORT_REVIEW,
        priority=Priority.MEDIUM,
        submitted_by=user,
        correlation_id="corr-test-case-audit-001",
        status=CaseStatus.PARSING,
        dedupe_key="test::case::audit::001",
        summary_snapshot={},
    )

    create_audit_event(
        case=case,
        event_type="case.parsing.started",
        correlation_id=case.correlation_id,
        payload={"step": 1},
    )
    create_audit_event(
        case=case,
        event_type="case.parsing.completed",
        correlation_id=case.correlation_id,
        payload={"step": 2},
    )

    audit_request = APIRequestFactory().get(f"/api/cases/{case.id}/audit-events/")
    force_authenticate(audit_request, user=user)
    audit_response = CaseAuditEventsView.as_view()(audit_request, pk=case.id)

    timeline_request = APIRequestFactory().get(f"/api/cases/{case.id}/timeline/")
    force_authenticate(timeline_request, user=user)
    timeline_response = CaseTimelineView.as_view()(timeline_request, pk=case.id)

    assert audit_response.status_code == 200
    assert timeline_response.status_code == 200
    assert len(audit_response.data) == 2
    assert len(timeline_response.data) == 2
    assert audit_response.data[0]["event_type"] == "case.parsing.started"
    assert audit_response.data[1]["event_type"] == "case.parsing.completed"
    assert timeline_response.data[0]["event_type"] == "case.parsing.started"
    assert timeline_response.data[1]["event_type"] == "case.parsing.completed"
