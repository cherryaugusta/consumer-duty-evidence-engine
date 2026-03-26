from apps.extraction.models import Claim, ClaimType
from apps.obligations.models import ConsumerDutyOutcome, EvidenceLink, LinkType, OutcomeCode


def _map_claim_to_outcomes(claim: Claim):
    mappings = []

    if claim.claim_type == ClaimType.UNCLEAR_FEE:
        mappings = [OutcomeCode.PRICE_VALUE, OutcomeCode.CONSUMER_UNDERSTANDING]

    elif claim.claim_type == ClaimType.SUPPORT_DELAY:
        mappings = [OutcomeCode.CONSUMER_SUPPORT]

    elif claim.claim_type == ClaimType.INADEQUATE_DISCLOSURE:
        mappings = [OutcomeCode.CONSUMER_UNDERSTANDING]

    return mappings


def map_case_outcomes(case):
    claims = Claim.objects.filter(case=case)

    EvidenceLink.objects.filter(case=case).delete()

    created_links = []

    for claim in claims:
        outcome_codes = _map_claim_to_outcomes(claim)

        for code in outcome_codes:
            outcome = ConsumerDutyOutcome.objects.get(code=code)

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
