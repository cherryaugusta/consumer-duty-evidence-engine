import pytest

from apps.cases.state_machine import assert_transition
from apps.core.constants import CaseStatus


@pytest.mark.parametrize(
    ("old_status", "new_status"),
    [
        (CaseStatus.NEW, CaseStatus.INGESTION_PENDING),
        (CaseStatus.NEW, CaseStatus.FAILED),
        (CaseStatus.INGESTION_PENDING, CaseStatus.PARSING),
        (CaseStatus.INGESTION_PENDING, CaseStatus.FAILED),
        (CaseStatus.PARSING, CaseStatus.PARSED),
        (CaseStatus.PARSING, CaseStatus.FAILED),
        (CaseStatus.PARSED, CaseStatus.EXTRACTION_PENDING),
        (CaseStatus.PARSED, CaseStatus.FAILED),
        (CaseStatus.EXTRACTION_PENDING, CaseStatus.EXTRACTED),
        (CaseStatus.EXTRACTION_PENDING, CaseStatus.NEEDS_REVIEW),
        (CaseStatus.EXTRACTION_PENDING, CaseStatus.FAILED),
        (CaseStatus.EXTRACTED, CaseStatus.MAPPING_PENDING),
        (CaseStatus.EXTRACTED, CaseStatus.FAILED),
        (CaseStatus.MAPPING_PENDING, CaseStatus.MAPPED),
        (CaseStatus.MAPPING_PENDING, CaseStatus.FAILED),
        (CaseStatus.MAPPED, CaseStatus.ASSESSMENT_PENDING),
        (CaseStatus.MAPPED, CaseStatus.FAILED),
        (CaseStatus.ASSESSMENT_PENDING, CaseStatus.ASSESSED),
        (CaseStatus.ASSESSMENT_PENDING, CaseStatus.NEEDS_REVIEW),
        (CaseStatus.ASSESSMENT_PENDING, CaseStatus.FAILED),
        (CaseStatus.ASSESSED, CaseStatus.APPROVED),
        (CaseStatus.ASSESSED, CaseStatus.NEEDS_REVIEW),
        (CaseStatus.ASSESSED, CaseStatus.ESCALATED),
        (CaseStatus.NEEDS_REVIEW, CaseStatus.APPROVED),
        (CaseStatus.NEEDS_REVIEW, CaseStatus.ESCALATED),
        (CaseStatus.NEEDS_REVIEW, CaseStatus.ARCHIVED),
        (CaseStatus.APPROVED, CaseStatus.ARCHIVED),
        (CaseStatus.ESCALATED, CaseStatus.ARCHIVED),
        (CaseStatus.FAILED, CaseStatus.INGESTION_PENDING),
        (CaseStatus.FAILED, CaseStatus.PARSING),
    ],
)
def test_valid_case_transitions(old_status: str, new_status: str) -> None:
    assert_transition(old_status, new_status)


@pytest.mark.parametrize(
    ("old_status", "new_status"),
    [
        (CaseStatus.NEW, CaseStatus.APPROVED),
        (CaseStatus.NEW, CaseStatus.PARSED),
        (CaseStatus.INGESTION_PENDING, CaseStatus.EXTRACTED),
        (CaseStatus.PARSING, CaseStatus.ASSESSED),
        (CaseStatus.PARSED, CaseStatus.MAPPED),
        (CaseStatus.EXTRACTION_PENDING, CaseStatus.APPROVED),
        (CaseStatus.EXTRACTED, CaseStatus.ASSESSMENT_PENDING),
        (CaseStatus.MAPPING_PENDING, CaseStatus.APPROVED),
        (CaseStatus.MAPPED, CaseStatus.APPROVED),
        (CaseStatus.ASSESSMENT_PENDING, CaseStatus.ARCHIVED),
        (CaseStatus.ASSESSED, CaseStatus.PARSING),
        (CaseStatus.NEEDS_REVIEW, CaseStatus.PARSING),
        (CaseStatus.APPROVED, CaseStatus.NEEDS_REVIEW),
        (CaseStatus.ESCALATED, CaseStatus.APPROVED),
        (CaseStatus.ARCHIVED, CaseStatus.NEW),
        (CaseStatus.ARCHIVED, CaseStatus.PARSING),
        (CaseStatus.FAILED, CaseStatus.APPROVED),
    ],
)
def test_invalid_case_transitions_raise_value_error(
    old_status: str,
    new_status: str,
) -> None:
    with pytest.raises(
        ValueError,
        match=f"Invalid case state transition: {old_status} -> {new_status}",
    ):
        assert_transition(old_status, new_status)
