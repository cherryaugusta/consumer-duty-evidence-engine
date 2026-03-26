from apps.extraction.models import Claim, ClaimType
from apps.obligations.models import ConsumerDutyOutcome, EvidenceLink, LinkType


def _map_claim_to_outcomes(claim: Claim):
    """
    Map claim types to EXISTING DB codes (must match exactly).
    """

    if claim.claim_type == ClaimType.UNCLEAR_FEE:
        return ["fair_value", "consumer_understanding"]

    elif claim.claim_type == ClaimType.SUPPORT_DELAY:
        return ["consumer_support"]

    elif claim.claim_type == ClaimType.INADEQUATE_DISCLOSURE:
        return ["consumer_understanding"]

    return []


def map_case_outcomes(case):
    """
    Create EvidenceLink records from claims → outcomes.
    Safe: skips missing outcomes instead of crashing Celery.
    """

    claims = Claim.objects.filter(case=case)

    # clear old links
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
