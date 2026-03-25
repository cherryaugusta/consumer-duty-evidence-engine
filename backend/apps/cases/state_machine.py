from apps.core.constants import CaseStatus

ALLOWED_TRANSITIONS = {
    CaseStatus.NEW: [CaseStatus.INGESTION_PENDING, CaseStatus.FAILED],
    CaseStatus.INGESTION_PENDING: [CaseStatus.PARSING, CaseStatus.FAILED],
    CaseStatus.PARSING: [CaseStatus.PARSED, CaseStatus.FAILED],
    CaseStatus.PARSED: [CaseStatus.EXTRACTION_PENDING, CaseStatus.FAILED],
    CaseStatus.EXTRACTION_PENDING: [
        CaseStatus.EXTRACTED,
        CaseStatus.NEEDS_REVIEW,
        CaseStatus.FAILED,
    ],
    CaseStatus.EXTRACTED: [CaseStatus.MAPPING_PENDING, CaseStatus.FAILED],
    CaseStatus.MAPPING_PENDING: [CaseStatus.MAPPED, CaseStatus.FAILED],
    CaseStatus.MAPPED: [CaseStatus.ASSESSMENT_PENDING, CaseStatus.FAILED],
    CaseStatus.ASSESSMENT_PENDING: [
        CaseStatus.ASSESSED,
        CaseStatus.NEEDS_REVIEW,
        CaseStatus.FAILED,
    ],
    CaseStatus.ASSESSED: [CaseStatus.APPROVED, CaseStatus.NEEDS_REVIEW, CaseStatus.ESCALATED],
    CaseStatus.NEEDS_REVIEW: [CaseStatus.APPROVED, CaseStatus.ESCALATED, CaseStatus.ARCHIVED],
    CaseStatus.APPROVED: [CaseStatus.ARCHIVED],
    CaseStatus.ESCALATED: [CaseStatus.ARCHIVED],
    CaseStatus.FAILED: [CaseStatus.INGESTION_PENDING, CaseStatus.PARSING],
    CaseStatus.ARCHIVED: [],
}


def assert_transition(old_status, new_status):
    if new_status not in ALLOWED_TRANSITIONS.get(old_status, []):
        raise ValueError(f"Invalid case state transition: {old_status} -> {new_status}")
