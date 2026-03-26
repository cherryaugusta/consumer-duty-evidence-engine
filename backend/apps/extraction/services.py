from apps.artifacts.models import DocumentSection
from apps.extraction.models import Claim, ClaimType


def extract_claims_for_case(case):
    sections = DocumentSection.objects.filter(artifact__case=case)

    created = []

    for section in sections:
        text = section.text.lower()

        if "fee" in text:
            claim = Claim.objects.create(
                case=case,
                claim_type=ClaimType.UNCLEAR_FEE,
                claim_text=section.text[:300],
                normalized_claim_text=section.text[:300],
                source_section=section,
                extraction_confidence=0.8,
                schema_valid=True,
                extraction_version="v1",
            )
            created.append(claim)

        elif "delay" in text:
            claim = Claim.objects.create(
                case=case,
                claim_type=ClaimType.SUPPORT_DELAY,
                claim_text=section.text[:300],
                normalized_claim_text=section.text[:300],
                source_section=section,
                extraction_confidence=0.8,
                schema_valid=True,
                extraction_version="v1",
            )
            created.append(claim)

    return created
