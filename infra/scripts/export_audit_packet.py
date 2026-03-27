import json
import os
import sys
from pathlib import Path

import django

BASE_DIR = Path(__file__).resolve().parents[2]
BACKEND_DIR = BASE_DIR / "backend"

sys.path.append(str(BACKEND_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
django.setup()

from django.conf import settings  # noqa: E402

from apps.artifacts.models import SourceArtifact  # noqa: E402
from apps.assessments.models import ContradictionFlag, SupportAssessment  # noqa: E402
from apps.cases.models import ReviewCase  # noqa: E402
from apps.extraction.models import Claim  # noqa: E402
from apps.obligations.models import EvidenceLink  # noqa: E402


def read_artifact_text(storage_path: str) -> str:
    file_path = Path(settings.MEDIA_ROOT) / storage_path
    if not file_path.exists():
        return ""
    return file_path.read_text(encoding="utf-8")


def serialize_case(case: ReviewCase) -> dict:
    return {
        "id": str(case.id),
        "reference_code": case.reference_code,
        "title": case.title,
        "status": case.status,
        "review_status": case.review_status,
        "priority": case.priority,
        "case_type": case.case_type,
        "correlation_id": case.correlation_id,
        "degraded_mode_active": case.degraded_mode_active,
        "submitted_by": case.submitted_by.username if case.submitted_by else None,
        "assigned_reviewer": (case.assigned_reviewer.username if case.assigned_reviewer else None),
        "created_at": case.created_at.isoformat() if case.created_at else None,
        "updated_at": case.updated_at.isoformat() if case.updated_at else None,
        "summary_snapshot": case.summary_snapshot,
    }


def serialize_artifacts(case: ReviewCase) -> list[dict]:
    artifacts = SourceArtifact.objects.filter(case=case).order_by("uploaded_at", "filename")

    payload = []

    for artifact in artifacts:
        payload.append(
            {
                "id": str(artifact.id),
                "artifact_type": artifact.artifact_type,
                "filename": artifact.filename,
                "mime_type": artifact.mime_type,
                "source_channel": artifact.source_channel,
                "storage_path": artifact.storage_path,
                "sha256_checksum": artifact.sha256_checksum,
                "parse_status": artifact.parse_status,
                "parse_error_code": artifact.parse_error_code,
                "text_length": artifact.text_length,
                "uploaded_at": (artifact.uploaded_at.isoformat() if artifact.uploaded_at else None),
                "text": read_artifact_text(artifact.storage_path),
                "sections": [
                    {
                        "id": str(section.id),
                        "section_index": section.section_index,
                        "heading": section.heading,
                        "text": section.text,
                        "char_start": section.char_start,
                        "char_end": section.char_end,
                        "page_number": section.page_number,
                        "parser_confidence": section.parser_confidence,
                    }
                    for section in artifact.sections.all().order_by("section_index")
                ],
            }
        )

    return payload


def serialize_claims(case: ReviewCase) -> list[dict]:
    claims = (
        Claim.objects.filter(case=case)
        .select_related("source_section", "source_section__artifact")
        .order_by("created_at", "id")
    )

    payload = []

    for claim in claims:
        payload.append(
            {
                "id": str(claim.id),
                "claim_type": claim.claim_type,
                "claim_text": claim.claim_text,
                "normalized_claim_text": claim.normalized_claim_text,
                "extraction_confidence": claim.extraction_confidence,
                "schema_valid": claim.schema_valid,
                "extraction_version": claim.extraction_version,
                "created_at": claim.created_at.isoformat() if claim.created_at else None,
                "source_section": {
                    "id": str(claim.source_section.id),
                    "artifact_id": str(claim.source_section.artifact_id),
                    "artifact_filename": claim.source_section.artifact.filename,
                    "section_index": claim.source_section.section_index,
                    "heading": claim.source_section.heading,
                    "text": claim.source_section.text,
                    "char_start": claim.source_section.char_start,
                    "char_end": claim.source_section.char_end,
                    "page_number": claim.source_section.page_number,
                },
            }
        )

    return payload


def serialize_evidence_links(case: ReviewCase) -> list[dict]:
    evidence_links = (
        EvidenceLink.objects.filter(case=case)
        .select_related("claim", "outcome", "section", "section__artifact")
        .order_by("id")
    )

    payload = []

    for link in evidence_links:
        payload.append(
            {
                "id": str(link.id),
                "claim_id": str(link.claim_id),
                "claim_type": link.claim.claim_type,
                "outcome_code": link.outcome.code,
                "outcome_name": link.outcome.name,
                "link_type": link.link_type,
                "rationale": link.rationale,
                "score": float(link.score) if link.score is not None else None,
                "section": (
                    {
                        "id": str(link.section.id),
                        "artifact_id": str(link.section.artifact_id),
                        "artifact_filename": link.section.artifact.filename,
                        "section_index": link.section.section_index,
                        "heading": link.section.heading,
                        "text": link.section.text,
                        "char_start": link.section.char_start,
                        "char_end": link.section.char_end,
                        "page_number": link.section.page_number,
                    }
                    if link.section
                    else None
                ),
            }
        )

    return payload


def serialize_assessments(case: ReviewCase) -> list[dict]:
    assessments = (
        SupportAssessment.objects.filter(case=case)
        .select_related("claim", "outcome")
        .order_by("created_at", "id")
    )

    payload = []

    for assessment in assessments:
        payload.append(
            {
                "id": str(assessment.id),
                "claim_id": str(assessment.claim_id),
                "claim_type": assessment.claim.claim_type,
                "outcome_code": assessment.outcome.code,
                "outcome_name": assessment.outcome.name,
                "status": assessment.status,
                "confidence": assessment.confidence,
                "requires_review": assessment.requires_review,
                "assessment_reason": assessment.assessment_reason,
                "rules_triggered": assessment.rules_triggered,
                "model_version": assessment.model_version,
                "created_at": (
                    assessment.created_at.isoformat() if assessment.created_at else None
                ),
            }
        )

    return payload


def serialize_contradictions(case: ReviewCase) -> list[dict]:
    contradictions = (
        ContradictionFlag.objects.filter(case=case)
        .select_related(
            "claim",
            "primary_section",
            "primary_section__artifact",
            "secondary_section",
            "secondary_section__artifact",
        )
        .order_by("created_at", "id")
    )

    payload = []

    for contradiction in contradictions:
        payload.append(
            {
                "id": str(contradiction.id),
                "claim_id": str(contradiction.claim_id) if contradiction.claim_id else None,
                "claim_type": contradiction.claim.claim_type if contradiction.claim else None,
                "contradiction_type": contradiction.contradiction_type,
                "severity": contradiction.severity,
                "reason": contradiction.reason,
                "created_at": (
                    contradiction.created_at.isoformat() if contradiction.created_at else None
                ),
                "primary_section": {
                    "id": str(contradiction.primary_section.id),
                    "artifact_id": str(contradiction.primary_section.artifact_id),
                    "artifact_filename": contradiction.primary_section.artifact.filename,
                    "section_index": contradiction.primary_section.section_index,
                    "heading": contradiction.primary_section.heading,
                    "text": contradiction.primary_section.text,
                    "char_start": contradiction.primary_section.char_start,
                    "char_end": contradiction.primary_section.char_end,
                    "page_number": contradiction.primary_section.page_number,
                },
                "secondary_section": {
                    "id": str(contradiction.secondary_section.id),
                    "artifact_id": str(contradiction.secondary_section.artifact_id),
                    "artifact_filename": contradiction.secondary_section.artifact.filename,
                    "section_index": contradiction.secondary_section.section_index,
                    "heading": contradiction.secondary_section.heading,
                    "text": contradiction.secondary_section.text,
                    "char_start": contradiction.secondary_section.char_start,
                    "char_end": contradiction.secondary_section.char_end,
                    "page_number": contradiction.secondary_section.page_number,
                },
            }
        )

    return payload


def serialize_recommendation(case: ReviewCase) -> dict | None:
    if not hasattr(case, "recommendation"):
        return None

    recommendation = case.recommendation

    return {
        "id": str(recommendation.id),
        "recommended_action": recommendation.recommended_action,
        "recommended_priority": recommendation.recommended_priority,
        "executive_summary": recommendation.executive_summary,
        "structured_rationale": recommendation.structured_rationale,
        "confidence": recommendation.confidence,
        "citation_count": recommendation.citation_count,
        "model_version": recommendation.model_version,
        "prompt_version": (
            {
                "id": str(recommendation.prompt_version.id),
                "name": recommendation.prompt_version.name,
                "version_label": recommendation.prompt_version.version_label,
                "purpose": recommendation.prompt_version.purpose,
                "schema_version": recommendation.prompt_version.schema_version,
            }
            if recommendation.prompt_version
            else None
        ),
        "created_at": (
            recommendation.created_at.isoformat() if recommendation.created_at else None
        ),
    }


def build_audit_packet(case: ReviewCase) -> dict:
    return {
        "exported_at": django.utils.timezone.now().isoformat(),
        "case": serialize_case(case),
        "artifacts": serialize_artifacts(case),
        "claims": serialize_claims(case),
        "evidence_links": serialize_evidence_links(case),
        "assessments": serialize_assessments(case),
        "contradictions": serialize_contradictions(case),
        "recommendation": serialize_recommendation(case),
    }


def export_audit_packet(reference_code: str) -> Path:
    case = ReviewCase.objects.get(reference_code=reference_code)
    packet = build_audit_packet(case)

    output_dir = Path(settings.MEDIA_ROOT) / "audit_packets"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / f"{reference_code}.json"
    output_path.write_text(json.dumps(packet, indent=2), encoding="utf-8")

    return output_path


def main():
    if len(sys.argv) != 2:
        print("Usage: python .\\infra\\scripts\\export_audit_packet.py <REFERENCE_CODE>")
        sys.exit(1)

    reference_code = sys.argv[1]
    output_path = export_audit_packet(reference_code)

    print("\n=== Audit Packet Exported ===")
    print(f"Reference code: {reference_code}")
    print(f"Output file: {output_path}")


if __name__ == "__main__":
    main()
