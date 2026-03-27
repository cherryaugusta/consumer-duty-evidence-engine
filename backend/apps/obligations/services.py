from apps.extraction.models import Claim, ClaimType
from apps.obligations.models import ConsumerDutyOutcome, EvidenceLink, LinkType


def _map_claim_to_outcomes(claim: Claim) -> list[str]:
    """
    Map claim types to EXISTING DB codes used by the current project.

    Important:
    - legacy mapping logic uses "fair_value" in DB
    - eval normalization later treats "fair_value" as "price_value"
    """

    claim_text = (claim.claim_text or "").lower()

    if claim.claim_type == ClaimType.UNCLEAR_FEE:
        return ["fair_value", "consumer_understanding"]

    if claim.claim_type == ClaimType.SUPPORT_DELAY:
        return ["consumer_support"]

    if claim.claim_type == ClaimType.INADEQUATE_DISCLOSURE:
        return ["consumer_understanding"]

    if claim.claim_type == ClaimType.MISLEADING_EXPLANATION:
        if any(
            phrase in claim_text
            for phrase in [
                "24/7",
                "seven days",
                "support hours",
                "monday to friday",
                "told support was available",
            ]
        ):
            return ["consumer_support", "consumer_understanding"]

        return ["consumer_understanding"]

    if claim.claim_type == ClaimType.POOR_OUTCOME_INDICATOR:
        return ["products_services"]

    if claim.claim_type == ClaimType.OTHER:
        if any(
            phrase in claim_text
            for phrase in [
                "confusion",
                "terms",
                "not right",
                "cannot clearly explain",
                "vaguely mentions",
            ]
        ):
            return ["consumer_understanding"]

        return []

    return []


def map_case_outcomes(case):
    """
    Create EvidenceLink records from claims to outcomes.
    Safe: skips missing outcomes instead of crashing workflow execution.
    """

    claims = Claim.objects.filter(case=case).select_related("source_section")

    EvidenceLink.objects.filter(case=case).delete()

    created_links = []

    for claim in claims:
        outcome_codes = _map_claim_to_outcomes(claim)

        for code in outcome_codes:
            try:
                outcome = ConsumerDutyOutcome.objects.get(code=code)
            except ConsumerDutyOutcome.DoesNotExist:
                print(f"WARNING: Missing outcome code: {code}")
                continue

            link = EvidenceLink.objects.create(
                case=case,
                claim=claim,
                outcome=outcome,
                section=claim.source_section,
                link_type=LinkType.SUPPORTING,
                rationale="Rule-based mapping from claim type",
                score=0.8,
            )
            created_links.append(link)

    return created_links
