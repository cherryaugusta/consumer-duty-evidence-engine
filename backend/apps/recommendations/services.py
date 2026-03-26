from __future__ import annotations

from collections import Counter
from typing import Any

from django.db import transaction

from apps.assessments.models import AssessmentStatus
from apps.audits.services import create_audit_event
from apps.cases.models import ReviewCase
from apps.cases.state_machine import assert_transition
from apps.core.constants import CaseStatus, Priority
from apps.recommendations.models import (
    PromptPurpose,
    PromptVersion,
    Recommendation,
    RecommendedAction,
)
from apps.reviews.services import create_or_update_review_task, determine_review_reason


def _safe_prompt_version() -> PromptVersion | None:
    return (
        PromptVersion.objects.filter(
            purpose=PromptPurpose.RECOMMENDATION,
            is_active=True,
        )
        .order_by("-created_at")
        .first()
    )


def _average_confidence(case: ReviewCase) -> float:
    assessments = list(case.assessments.values_list("confidence", flat=True))
    if not assessments:
        return 0.0
    return round(sum(assessments) / len(assessments), 4)


def _support_distribution(case: ReviewCase) -> dict[str, int]:
    counter = Counter(case.assessments.values_list("status", flat=True))
    return {
        AssessmentStatus.SUPPORTED: counter.get(AssessmentStatus.SUPPORTED, 0),
        AssessmentStatus.WEAK_SUPPORT: counter.get(AssessmentStatus.WEAK_SUPPORT, 0),
        AssessmentStatus.MISSING_SUPPORT: counter.get(AssessmentStatus.MISSING_SUPPORT, 0),
        AssessmentStatus.CONTRADICTORY_SUPPORT: counter.get(
            AssessmentStatus.CONTRADICTORY_SUPPORT,
            0,
        ),
        AssessmentStatus.STALE_SUPPORT: counter.get(AssessmentStatus.STALE_SUPPORT, 0),
    }


def _recommended_action(case: ReviewCase, distribution: dict[str, int]) -> str:
    contradiction_count = case.contradiction_flags.count()
    requires_review_count = case.assessments.filter(requires_review=True).count()

    if case.degraded_mode_active:
        return RecommendedAction.REVIEW

    if contradiction_count >= 2 and case.priority in {Priority.HIGH, Priority.CRITICAL}:
        return RecommendedAction.ESCALATE

    if contradiction_count > 0:
        return RecommendedAction.REVIEW

    if distribution[AssessmentStatus.CONTRADICTORY_SUPPORT] > 0:
        return RecommendedAction.REVIEW

    if distribution[AssessmentStatus.MISSING_SUPPORT] > 0:
        return RecommendedAction.REVIEW

    if distribution[AssessmentStatus.STALE_SUPPORT] > 0:
        return RecommendedAction.REVIEW

    if requires_review_count > 0:
        return RecommendedAction.REVIEW

    if distribution[AssessmentStatus.WEAK_SUPPORT] > 0:
        return RecommendedAction.REVIEW

    if distribution[AssessmentStatus.SUPPORTED] > 0:
        return RecommendedAction.APPROVE

    return RecommendedAction.REQUEST_MORE_EVIDENCE


def _recommended_priority(case: ReviewCase, action: str) -> str:
    if action == RecommendedAction.ESCALATE and case.priority != Priority.CRITICAL:
        return Priority.CRITICAL
    if action == RecommendedAction.REVIEW and case.priority == Priority.LOW:
        return Priority.MEDIUM
    return case.priority


def _build_summary(
    *,
    case: ReviewCase,
    distribution: dict[str, int],
    action: str,
    citation_count: int,
    contradiction_count: int,
) -> str:
    supported = distribution[AssessmentStatus.SUPPORTED]
    weak = distribution[AssessmentStatus.WEAK_SUPPORT]
    missing = distribution[AssessmentStatus.MISSING_SUPPORT]
    contradictory = distribution[AssessmentStatus.CONTRADICTORY_SUPPORT]
    stale = distribution[AssessmentStatus.STALE_SUPPORT]

    lines = [
        (
            f"Case {case.reference_code} was assessed across "
            f"{case.assessments.count()} mapped support checks."
        ),
        (
            "Support distribution: "
            f"supported={supported}, "
            f"weak_support={weak}, "
            f"missing_support={missing}, "
            f"contradictory_support={contradictory}, "
            f"stale_support={stale}."
        ),
        f"Contradiction flags detected: {contradiction_count}.",
        f"Degraded mode active: {'yes' if case.degraded_mode_active else 'no'}.",
        f"Citation count: {citation_count}.",
    ]

    if action == RecommendedAction.APPROVE:
        lines.append(
            "Recommended action: approve. Current evidence is sufficiently "
            "consistent and no blocking review trigger was detected."
        )
    elif action == RecommendedAction.ESCALATE:
        lines.append(
            "Recommended action: escalate. Contradictions or risk severity "
            "exceed the safe auto-resolution threshold."
        )
    elif action == RecommendedAction.REQUEST_MORE_EVIDENCE:
        lines.append(
            "Recommended action: request more evidence. The case lacks enough "
            "support to make a safe recommendation."
        )
    else:
        lines.append(
            "Recommended action: review. Human review is required because "
            "support is weak, missing, contradictory, stale, or the workflow "
            "is in degraded mode."
        )

    return " ".join(lines)


def _structured_rationale(
    *,
    case: ReviewCase,
    distribution: dict[str, int],
    action: str,
    citation_count: int,
    contradiction_count: int,
    confidence: float,
) -> dict[str, Any]:
    return {
        "support_distribution": distribution,
        "contradiction_count": contradiction_count,
        "degraded_mode_active": case.degraded_mode_active,
        "citation_count": citation_count,
        "requires_review_count": case.assessments.filter(requires_review=True).count(),
        "assessment_count": case.assessments.count(),
        "confidence": confidence,
        "recommended_action": action,
        "review_reason": (
            determine_review_reason(case)
            if action
            in {
                RecommendedAction.REVIEW,
                RecommendedAction.ESCALATE,
                RecommendedAction.REQUEST_MORE_EVIDENCE,
            }
            else None
        ),
    }


def _transition_case(case: ReviewCase, new_status: str) -> None:
    if case.status != new_status:
        assert_transition(case.status, new_status)
        case.status = new_status
        case.save(update_fields=["status", "updated_at"])


@transaction.atomic
def generate_case_recommendation(*, case: ReviewCase) -> Recommendation:
    distribution = _support_distribution(case)
    contradiction_count = case.contradiction_flags.count()
    citation_count = case.evidence_links.exclude(section__isnull=True).count()
    confidence = _average_confidence(case)
    action = _recommended_action(case, distribution)
    priority = _recommended_priority(case, action)
    prompt_version = _safe_prompt_version()

    recommendation, _ = Recommendation.objects.update_or_create(
        case=case,
        defaults={
            "recommended_action": action,
            "recommended_priority": priority,
            "executive_summary": _build_summary(
                case=case,
                distribution=distribution,
                action=action,
                citation_count=citation_count,
                contradiction_count=contradiction_count,
            ),
            "structured_rationale": _structured_rationale(
                case=case,
                distribution=distribution,
                action=action,
                citation_count=citation_count,
                contradiction_count=contradiction_count,
                confidence=confidence,
            ),
            "confidence": confidence,
            "citation_count": citation_count,
            "model_version": "rules-recommendation-v1",
            "prompt_version": prompt_version,
        },
    )

    if action == RecommendedAction.APPROVE:
        _transition_case(case, CaseStatus.APPROVED)
    elif action == RecommendedAction.ESCALATE:
        _transition_case(case, CaseStatus.ESCALATED)
        create_or_update_review_task(
            case=case,
            reason_code=determine_review_reason(case),
        )
    else:
        _transition_case(case, CaseStatus.NEEDS_REVIEW)
        create_or_update_review_task(
            case=case,
            reason_code=determine_review_reason(case),
        )

    create_audit_event(
        case=case,
        event_type="recommendation.generated",
        payload={
            "recommendation_id": str(recommendation.id),
            "recommended_action": recommendation.recommended_action,
            "recommended_priority": recommendation.recommended_priority,
            "confidence": recommendation.confidence,
            "citation_count": recommendation.citation_count,
            "degraded_mode_active": case.degraded_mode_active,
        },
    )

    return recommendation


@transaction.atomic
def generate_source_only_recommendation(
    *,
    case: ReviewCase,
    reason: str,
) -> Recommendation:
    citation_count = case.evidence_links.exclude(section__isnull=True).count()

    recommendation, _ = Recommendation.objects.update_or_create(
        case=case,
        defaults={
            "recommended_action": RecommendedAction.REVIEW,
            "recommended_priority": case.priority,
            "executive_summary": (
                "Source-only fallback recommendation generated. "
                "Human review is required because recommendation generation "
                f"could not complete safely: {reason}."
            ),
            "structured_rationale": {
                "mode": "source_only",
                "reason": reason,
                "citation_count": citation_count,
                "assessment_count": case.assessments.count(),
                "contradiction_count": case.contradiction_flags.count(),
                "degraded_mode_active": True,
            },
            "confidence": 0.0,
            "citation_count": citation_count,
            "model_version": "source-only-fallback-v1",
            "prompt_version": None,
        },
    )

    case.degraded_mode_active = True
    case.save(update_fields=["degraded_mode_active", "updated_at"])

    if case.status == CaseStatus.ASSESSED:
        _transition_case(case, CaseStatus.NEEDS_REVIEW)
    elif case.status not in {
        CaseStatus.NEEDS_REVIEW,
        CaseStatus.ESCALATED,
        CaseStatus.APPROVED,
    }:
        case.status = CaseStatus.NEEDS_REVIEW
        case.save(update_fields=["status", "updated_at"])

    create_or_update_review_task(
        case=case,
        reason_code=determine_review_reason(case),
    )

    create_audit_event(
        case=case,
        event_type="recommendation.source_only_generated",
        payload={
            "recommendation_id": str(recommendation.id),
            "reason": reason,
            "citation_count": citation_count,
        },
    )

    return recommendation
