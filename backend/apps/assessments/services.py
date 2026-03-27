from apps.assessments.models import (
    AssessmentStatus,
    ContradictionFlag,
    ContradictionType,
    SupportAssessment,
)
from apps.obligations.models import EvidenceLink, OutcomeCode


def _contains_any(text: str, phrases: list[str]) -> bool:
    return any(phrase in text for phrase in phrases)


def _determine_assessment_status(evidence_link) -> tuple[str, bool, str]:
    claim_text = evidence_link.claim.claim_text.lower()
    section_text = (evidence_link.section.text if evidence_link.section else "").lower()

    if _contains_any(
        section_text,
        [
            "outdated",
            "old version",
            "no longer matches",
            "does not match the current product terms",
        ],
    ):
        return (
            AssessmentStatus.STALE_SUPPORT,
            True,
            "Evidence appears stale or outdated.",
        )

    if _contains_any(
        claim_text + " " + section_text,
        [
            "24/7",
            "seven days",
            "monday to friday",
            "support hours",
        ],
    ) and (
        ("24/7" in claim_text and "monday to friday" in section_text)
        or ("seven days" in claim_text and "monday to friday" in section_text)
        or ("24/7" in section_text and "monday to friday" in claim_text)
        or ("seven days" in section_text and "monday to friday" in claim_text)
    ):
        return (
            AssessmentStatus.CONTRADICTORY_SUPPORT,
            True,
            "Conflicting service availability statements were detected.",
        )

    if evidence_link.outcome.code == OutcomeCode.CONSUMER_SUPPORT:
        if _contains_any(
            claim_text + " " + section_text,
            [
                "delay",
                "delayed",
                "not acknowledged",
                "no update",
                "backlog",
                "response times",
            ],
        ):
            return (
                AssessmentStatus.WEAK_SUPPORT,
                True,
                "Support-related delay detected and routed for review.",
            )

        if _contains_any(
            section_text,
            [
                "resolved it quickly",
                "acknowledged immediately",
                "resolved the same day",
                "explained in plain language",
            ],
        ):
            return (
                AssessmentStatus.SUPPORTED,
                False,
                "Support evidence indicates prompt and clear assistance.",
            )

    if evidence_link.outcome.code == OutcomeCode.CONSUMER_UNDERSTANDING:
        if "fee" in claim_text and not _contains_any(
            section_text,
            [
                "disclosure",
                "clearly explained",
                "explained and accepted",
                "all fees and conditions were clearly explained",
                "customer confirmed understanding",
            ],
        ):
            return (
                AssessmentStatus.MISSING_SUPPORT,
                True,
                "Fee-related claim without clear disclosure support.",
            )

        if _contains_any(
            section_text,
            [
                "clearly explained",
                "explained and accepted",
                "customer confirmed understanding",
                "all fees and conditions were clearly explained",
            ],
        ):
            return (
                AssessmentStatus.SUPPORTED,
                False,
                "Disclosure text indicates the customer was clearly informed.",
            )

    if evidence_link.outcome.code == OutcomeCode.PRICE_VALUE:
        if "fee" in claim_text and _contains_any(
            section_text,
            [
                "monthly fee",
                "£5",
                "fees may apply",
                "account fee",
            ],
        ):
            if _contains_any(
                section_text,
                [
                    "clearly explained",
                    "explained and accepted",
                    "customer confirmed understanding",
                ],
            ):
                return (
                    AssessmentStatus.SUPPORTED,
                    False,
                    "Fee evidence is clearly disclosed and supported.",
                )

            return (
                AssessmentStatus.WEAK_SUPPORT,
                True,
                "Fee evidence exists but clarity remains weak.",
            )

    if evidence_link.outcome.code == OutcomeCode.PRODUCTS_SERVICES:
        if _contains_any(
            claim_text + " " + section_text,
            [
                "did not match",
                "not suitable",
                "unsuitable",
                "flexible access",
                "easy access",
                "low penalties",
                "recommended product",
            ],
        ):
            return (
                AssessmentStatus.WEAK_SUPPORT,
                True,
                "Suitability concern detected and routed for review.",
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
            model_version="rules-v2",
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
        if assessment.status not in {
            AssessmentStatus.MISSING_SUPPORT,
            AssessmentStatus.CONTRADICTORY_SUPPORT,
        }:
            continue

        source_section = assessment.claim.source_section

        contradiction_type = (
            ContradictionType.STATEMENT_CONFLICT
            if assessment.status == AssessmentStatus.CONTRADICTORY_SUPPORT
            else ContradictionType.SUPPORT_GAP
        )

        reason = (
            "Conflicting statements were detected across the evidence."
            if assessment.status == AssessmentStatus.CONTRADICTORY_SUPPORT
            else "Required supporting evidence was not found for the mapped outcome."
        )

        flag = ContradictionFlag.objects.create(
            case=case,
            claim=assessment.claim,
            primary_section=source_section,
            secondary_section=source_section,
            contradiction_type=contradiction_type,
            severity="medium",
            reason=reason,
        )
        created_flags.append(flag)

    return created_flags
