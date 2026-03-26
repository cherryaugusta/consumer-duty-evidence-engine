from apps.assessments.models import (
    AssessmentStatus,
    ContradictionFlag,
    ContradictionType,
    SupportAssessment,
)
from apps.obligations.models import EvidenceLink, OutcomeCode


def _determine_assessment_status(evidence_link) -> tuple[str, bool, str]:
    claim_text = evidence_link.claim.claim_text.lower()
    section_text = (evidence_link.section.text if evidence_link.section else "").lower()

    if evidence_link.outcome.code == OutcomeCode.CONSUMER_SUPPORT:
        if "delay" in claim_text or "delayed" in claim_text:
            return (
                AssessmentStatus.WEAK_SUPPORT,
                True,
                "Support-related delay detected and routed for review.",
            )

    if evidence_link.outcome.code == OutcomeCode.CONSUMER_UNDERSTANDING:
        if "fee" in claim_text and "disclosure" not in section_text:
            return (
                AssessmentStatus.MISSING_SUPPORT,
                True,
                "Fee-related claim without clear disclosure support.",
            )

    if "outdated" in section_text or "old version" in section_text:
        return (
            AssessmentStatus.STALE_SUPPORT,
            True,
            "Evidence appears stale or outdated.",
        )

    return (
        AssessmentStatus.SUPPORTED,
        False,
        "Evidence link supports the mapped outcome.",
    )


def assess_case_support(case) -> list[SupportAssessment]:
    evidence_links = (
        EvidenceLink.objects.filter(case=case)
        .select_related("claim", "outcome", "section")
        .order_by("claim", "outcome")
    )

    SupportAssessment.objects.filter(case=case).delete()

    created_assessments: list[SupportAssessment] = []

    for link in evidence_links:
        status, requires_review, reason = _determine_assessment_status(link)

        assessment = SupportAssessment.objects.create(
            case=case,
            claim=link.claim,
            outcome=link.outcome,
            status=status,
            confidence=0.80 if status == AssessmentStatus.SUPPORTED else 0.65,
            requires_review=requires_review,
            assessment_reason=reason,
            rules_triggered=[f"link_type:{link.link_type}", f"status:{status}"],
            model_version="rules-v1",
        )
        created_assessments.append(assessment)

    return created_assessments


def detect_case_contradictions(case) -> list[ContradictionFlag]:
    assessments = (
        SupportAssessment.objects.filter(case=case)
        .select_related("claim", "claim__source_section")
        .order_by("created_at")
    )

    ContradictionFlag.objects.filter(case=case).delete()

    created_flags: list[ContradictionFlag] = []

    for assessment in assessments:
        if assessment.status != AssessmentStatus.MISSING_SUPPORT:
            continue

        source_section = assessment.claim.source_section

        flag = ContradictionFlag.objects.create(
            case=case,
            claim=assessment.claim,
            primary_section=source_section,
            secondary_section=source_section,
            contradiction_type=ContradictionType.SUPPORT_GAP,
            severity="medium",
            reason="Required supporting evidence was not found for the mapped outcome.",
        )
        created_flags.append(flag)

    return created_flags
