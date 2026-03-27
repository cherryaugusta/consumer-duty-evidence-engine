import os
import sys
from pathlib import Path

import django

BASE_DIR = Path(__file__).resolve().parents[2]
BACKEND_DIR = BASE_DIR / "backend"

sys.path.append(str(BACKEND_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
django.setup()

from django.core.exceptions import ObjectDoesNotExist  # noqa: E402
from django.db import transaction  # noqa: E402

from apps.artifacts.models import SourceArtifact  # noqa: E402
from apps.assessments.services import assess_case_support, detect_case_contradictions  # noqa: E402
from apps.cases.models import ReviewCase  # noqa: E402
from apps.core.constants import CaseStatus  # noqa: E402
from apps.extraction.services import extract_claims_for_case  # noqa: E402
from apps.obligations.services import map_case_outcomes  # noqa: E402
from apps.parsing.services import parse_artifact_to_sections  # noqa: E402
from apps.recommendations.services import generate_case_recommendation  # noqa: E402


def get_recommendation_action(case: ReviewCase) -> str | None:
    try:
        return case.recommendation.recommended_action
    except ObjectDoesNotExist:
        return None


def snapshot(case: ReviewCase) -> dict:
    return {
        "status": case.status,
        "review_status": case.review_status,
        "claims": case.claims.count(),
        "assessments": case.assessments.count(),
        "recommendation": get_recommendation_action(case),
    }


def print_snapshot(label: str, snap: dict) -> None:
    print(
        f"{label} | "
        f"status={snap['status']} | "
        f"review_status={snap['review_status']} | "
        f"claims={snap['claims']} | "
        f"assessments={snap['assessments']} | "
        f"recommendation={snap['recommendation']}"
    )


@transaction.atomic
def replay_case(reference_code: str) -> None:
    print(f"\n=== Replaying Case: {reference_code} ===")

    case = ReviewCase.objects.get(reference_code=reference_code)

    before = snapshot(case)
    print_snapshot("BEFORE", before)

    artifacts = list(SourceArtifact.objects.filter(case=case).order_by("id"))

    case.claims.all().delete()
    case.assessments.all().delete()

    try:
        case.recommendation.delete()
    except ObjectDoesNotExist:
        pass

    case.status = CaseStatus.PARSING
    case.save(update_fields=["status", "updated_at"])

    for artifact in artifacts:
        parse_artifact_to_sections(artifact)

    case.status = CaseStatus.PARSED
    case.save(update_fields=["status", "updated_at"])

    extract_claims_for_case(case)

    case.status = CaseStatus.EXTRACTED
    case.save(update_fields=["status", "updated_at"])

    map_case_outcomes(case)

    case.status = CaseStatus.MAPPED
    case.save(update_fields=["status", "updated_at"])

    assess_case_support(case)
    detect_case_contradictions(case)

    case.status = CaseStatus.ASSESSED
    case.save(update_fields=["status", "updated_at"])

    generate_case_recommendation(case=case)
    case.refresh_from_db()

    after = snapshot(case)
    print_snapshot("AFTER ", after)

    print("\n=== Determinism Check ===")
    for key in before:
        if before[key] != after[key]:
            print(f"CHANGED: {key} | before={before[key]} | after={after[key]}")
        else:
            print(f"UNCHANGED: {key}")


def main():
    if len(sys.argv) != 2:
        print("Usage: python .\\infra\\scripts\\replay_case.py <REFERENCE_CODE>")
        sys.exit(1)

    reference_code = sys.argv[1]
    replay_case(reference_code)


if __name__ == "__main__":
    main()
