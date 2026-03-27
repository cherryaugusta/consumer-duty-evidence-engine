import hashlib
import os
import sys
import uuid
from pathlib import Path

import django

BASE_DIR = Path(__file__).resolve().parents[2]
BACKEND_DIR = BASE_DIR / "backend"

sys.path.append(str(BACKEND_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
django.setup()

from django.conf import settings  # noqa: E402
from django.contrib.auth import get_user_model  # noqa: E402
from django.db import transaction  # noqa: E402

from apps.artifacts.models import SourceArtifact, SourceChannel  # noqa: E402
from apps.assessments.services import assess_case_support, detect_case_contradictions  # noqa: E402
from apps.cases.models import ReviewCase  # noqa: E402
from apps.core.constants import CaseStatus, CaseType, Priority  # noqa: E402
from apps.extraction.services import extract_claims_for_case  # noqa: E402
from apps.obligations.models import ConsumerDutyOutcome  # noqa: E402
from apps.obligations.services import map_case_outcomes  # noqa: E402
from apps.parsing.services import parse_artifact_to_sections  # noqa: E402
from apps.recommendations.models import PromptPurpose, PromptVersion  # noqa: E402
from apps.recommendations.services import generate_case_recommendation  # noqa: E402

User = get_user_model()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def write_media_file(storage_path: str, text: str) -> None:
    media_root = Path(settings.MEDIA_ROOT)
    file_path = media_root / storage_path
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(text, encoding="utf-8")


def create_users():
    users_to_create = [
        {
            "username": "admin",
            "email": "admin@example.com",
            "password": "admin123!",
            "is_staff": True,
            "is_superuser": True,
            "first_name": "Admin",
            "last_name": "User",
        },
        {
            "username": "analyst_1",
            "email": "analyst1@example.com",
            "password": "analyst123!",
            "is_staff": False,
            "is_superuser": False,
            "first_name": "Analyst",
            "last_name": "One",
        },
        {
            "username": "analyst_2",
            "email": "analyst2@example.com",
            "password": "analyst123!",
            "is_staff": False,
            "is_superuser": False,
            "first_name": "Analyst",
            "last_name": "Two",
        },
    ]

    created_users = {}

    for user_data in users_to_create:
        user, _ = User.objects.update_or_create(
            username=user_data["username"],
            defaults={
                "email": user_data["email"],
                "is_staff": user_data["is_staff"],
                "is_superuser": user_data["is_superuser"],
                "first_name": user_data["first_name"],
                "last_name": user_data["last_name"],
            },
        )
        user.set_password(user_data["password"])
        user.save()
        created_users[user.username] = user

    return created_users


def create_outcomes():
    outcomes = [
        {
            "code": "products_services",
            "name": "Products and services",
            "description": "Product and service suitability.",
        },
        {
            "code": "price_value",
            "name": "Price and value",
            "description": "Fair price and value considerations.",
        },
        {
            "code": "fair_value",
            "name": "Fair value",
            "description": "Legacy fair value code used by current mapping rules.",
        },
        {
            "code": "consumer_understanding",
            "name": "Consumer understanding",
            "description": "Consumer understanding and clarity.",
        },
        {
            "code": "consumer_support",
            "name": "Consumer support",
            "description": "Consumer support responsiveness and accessibility.",
        },
    ]

    for outcome in outcomes:
        ConsumerDutyOutcome.objects.update_or_create(
            code=outcome["code"],
            defaults={
                "name": outcome["name"],
                "description": outcome["description"],
                "active": True,
            },
        )


def create_prompt_versions():
    prompt_versions = [
        {
            "name": "Rules Recommendation Prompt",
            "version_label": "v1",
            "purpose": PromptPurpose.RECOMMENDATION,
            "template_text": "Rule-based recommendation template for seeded demo cases.",
            "schema_version": "1.0",
            "is_active": True,
        },
        {
            "name": "Rules Extraction Prompt",
            "version_label": "v1",
            "purpose": PromptPurpose.EXTRACTION,
            "template_text": "Rule-based extraction template for seeded demo cases.",
            "schema_version": "1.0",
            "is_active": True,
        },
    ]

    for prompt in prompt_versions:
        PromptVersion.objects.update_or_create(
            name=prompt["name"],
            version_label=prompt["version_label"],
            purpose=prompt["purpose"],
            defaults={
                "template_text": prompt["template_text"],
                "schema_version": prompt["schema_version"],
                "is_active": prompt["is_active"],
            },
        )


def build_seed_cases(users: dict):
    return [
        {
            "reference_code": "DEMO-001",
            "title": "Seeded demo: unclear fee disclosure",
            "case_type": CaseType.COMPLAINT_REVIEW,
            "priority": Priority.HIGH,
            "submitted_by": users["admin"],
            "artifacts": [
                {
                    "artifact_type": "complaint",
                    "filename": "demo_001_complaint.txt",
                    "text": (
                        "Customer states they were charged a monthly fee that was not "
                        "clearly explained during onboarding."
                    ),
                },
                {
                    "artifact_type": "disclosure",
                    "filename": "demo_001_disclosure.txt",
                    "text": (
                        "Fees may apply depending on account usage. "
                        "Details available in full terms."
                    ),
                },
            ],
        },
        {
            "reference_code": "DEMO-002",
            "title": "Seeded demo: contradictory support script",
            "case_type": CaseType.SUPPORT_REVIEW,
            "priority": Priority.HIGH,
            "submitted_by": users["analyst_1"],
            "artifacts": [
                {
                    "artifact_type": "complaint",
                    "filename": "demo_002_complaint.txt",
                    "text": (
                        "Customer says they were told support was available seven days a week."
                    ),
                },
                {
                    "artifact_type": "script",
                    "filename": "demo_002_script.txt",
                    "text": "Sales script says support is available 24/7.",
                },
                {
                    "artifact_type": "policy_excerpt",
                    "filename": "demo_002_policy.txt",
                    "text": (
                        "Current service policy states support hours are "
                        "Monday to Friday, 9am to 5pm."
                    ),
                },
            ],
        },
        {
            "reference_code": "DEMO-003",
            "title": "Seeded demo: strong consumer support case",
            "case_type": CaseType.SUPPORT_REVIEW,
            "priority": Priority.MEDIUM,
            "submitted_by": users["analyst_2"],
            "artifacts": [
                {
                    "artifact_type": "complaint",
                    "filename": "demo_003_complaint.txt",
                    "text": (
                        "Customer reported a service issue but confirmed the "
                        "support team resolved it quickly and clearly."
                    ),
                },
                {
                    "artifact_type": "support_transcript",
                    "filename": "demo_003_transcript.txt",
                    "text": (
                        "Support transcript shows the issue was acknowledged "
                        "immediately, resolved the same day, and explained in "
                        "plain language."
                    ),
                },
            ],
        },
    ]


def create_case(case_data: dict) -> ReviewCase:
    ReviewCase.objects.filter(reference_code=case_data["reference_code"]).delete()

    return ReviewCase.objects.create(
        reference_code=case_data["reference_code"],
        title=case_data["title"],
        case_type=case_data["case_type"],
        priority=case_data["priority"],
        submitted_by=case_data["submitted_by"],
        correlation_id=str(uuid.uuid4()),
        status=CaseStatus.INGESTION_PENDING,
        dedupe_key=f"seed::{case_data['reference_code']}",
    )


def create_artifacts(case: ReviewCase, case_data: dict):
    created_artifacts = []

    for index, artifact_data in enumerate(case_data["artifacts"], start=1):
        storage_path = f"seeded_demo/{case.reference_code}/{index:02d}_{artifact_data['filename']}"
        write_media_file(storage_path, artifact_data["text"])

        artifact = SourceArtifact.objects.create(
            case=case,
            artifact_type=artifact_data["artifact_type"],
            filename=artifact_data["filename"],
            mime_type="text/plain",
            source_channel=SourceChannel.SEEDED_DEMO,
            storage_path=storage_path,
            sha256_checksum=sha256_text(artifact_data["text"]),
        )
        created_artifacts.append(artifact)

    return created_artifacts


def run_pipeline(case: ReviewCase, artifacts: list[SourceArtifact]) -> None:
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


@transaction.atomic
def main():
    print("\n=== Seeding Demo Data ===")

    users = create_users()
    print("Created/updated users: admin, analyst_1, analyst_2")

    create_outcomes()
    print("Created/updated outcomes")

    create_prompt_versions()
    print("Created/updated prompt versions")

    seed_cases = build_seed_cases(users)

    created_cases = []

    for case_data in seed_cases:
        case = create_case(case_data)
        artifacts = create_artifacts(case, case_data)
        run_pipeline(case, artifacts)
        created_cases.append(case)

        print(
            f"Seeded {case.reference_code} | "
            f"status={case.status} | "
            f"review_status={case.review_status} | "
            f"claims={case.claims.count()} | "
            f"assessments={case.assessments.count()} | "
            f"recommendation={getattr(case.recommendation, 'recommended_action', None)}"
        )

    print(f"\nSeeded {len(created_cases)} demo cases successfully.")


if __name__ == "__main__":
    main()
