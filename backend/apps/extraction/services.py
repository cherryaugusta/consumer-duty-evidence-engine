from apps.artifacts.models import DocumentSection
from apps.extraction.models import Claim, ClaimType


def _contains_any(text: str, phrases: list[str]) -> bool:
    return any(phrase in text for phrase in phrases)


def _classify_section_text(text: str) -> str | None:
    if _contains_any(
        text,
        [
            "did not match",
            "not match",
            "not suitable",
            "unsuitable",
            "flexible access",
            "easy access",
            "low penalties",
            "penalties",
            "recommended product",
        ],
    ):
        return ClaimType.POOR_OUTCOME_INDICATOR

    if _contains_any(
        text,
        [
            "monthly fee",
            "account fee",
            "charged",
            "fee information",
            "fees may apply",
            "no fee information",
        ],
    ):
        return ClaimType.UNCLEAR_FEE

    if "fee" in text and _contains_any(
        text,
        [
            "no longer matches",
            "does not match the current product terms",
            "outdated",
            "old version",
        ],
    ):
        return ClaimType.UNCLEAR_FEE

    if _contains_any(
        text,
        [
            "possible confusion about terms",
            "possible confusion",
            "confusion about terms",
        ],
    ):
        return ClaimType.UNCLEAR_FEE

    if _contains_any(
        text,
        [
            "not right",
            "something was not right",
            "cannot clearly explain",
            "vaguely mentions",
            "ambiguous",
            "no issues",
        ],
    ):
        return ClaimType.OTHER

    if _contains_any(
        text,
        [
            "24/7",
            "seven days",
            "7 days",
            "monday to friday",
            "support hours",
            "available seven days",
            "available 24/7",
            "told support was available",
        ],
    ):
        return ClaimType.MISLEADING_EXPLANATION

    if _contains_any(
        text,
        [
            "delay",
            "delayed",
            "not acknowledged",
            "no update",
            "backlog",
            "response times",
            "service issue",
            "resolved it quickly",
            "acknowledged immediately",
            "resolved the same day",
        ],
    ):
        return ClaimType.SUPPORT_DELAY

    if _contains_any(
        text,
        [
            "disclosure",
            "clearly explained",
            "explained and accepted",
            "explained in plain language",
            "customer confirmed understanding",
            "all fees and conditions were clearly explained",
        ],
    ):
        return ClaimType.INADEQUATE_DISCLOSURE

    if "fee" in text:
        return ClaimType.UNCLEAR_FEE

    return None


def extract_claims_for_case(case):
    sections = (
        DocumentSection.objects.filter(artifact__case=case)
        .select_related("artifact")
        .order_by("artifact__uploaded_at", "section_index")
    )

    Claim.objects.filter(case=case).delete()

    created = []

    for section in sections:
        text = section.text.lower().strip()
        claim_type = _classify_section_text(text)

        if not claim_type:
            continue

        claim = Claim.objects.create(
            case=case,
            claim_type=claim_type,
            claim_text=section.text[:300],
            normalized_claim_text=section.text[:300].lower(),
            source_section=section,
            extraction_confidence=0.8,
            schema_valid=True,
            extraction_version="v3",
        )
        created.append(claim)

    return created
