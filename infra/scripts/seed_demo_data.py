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
                        "clearly explained during onboarding and that they only noticed "
                        "the charge after the first statement arrived."
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
            "title": "Seeded demo: product suitability concern",
            "case_type": CaseType.COMPLAINT_REVIEW,
            "priority": Priority.HIGH,
            "submitted_by": users["analyst_2"],
            "artifacts": [
                {
                    "artifact_type": "complaint",
                    "filename": "demo_003_complaint.txt",
                    "text": (
                        "Customer says the product was presented as suitable for "
                        "short-term savings needs even though they needed easy "
                        "access and no risk to capital."
                    ),
                },
                {
                    "artifact_type": "disclosure",
                    "filename": "demo_003_disclosure.txt",
                    "text": (
                        "The product may involve fluctuations in value and may not "
                        "be suitable for customers needing immediate access to all "
                        "funds."
                    ),
                },
                {
                    "artifact_type": "policy_excerpt",
                    "filename": "demo_003_policy.txt",
                    "text": (
                        "Advisers should clearly explain risk, liquidity "
                        "restrictions, and customer suitability considerations "
                        "before sale."
                    ),
                },
            ],
        },
        {
            "reference_code": "DEMO-004",
            "title": "Seeded demo: well-supported disclosure case",
            "case_type": CaseType.DISCLOSURE_REVIEW,
            "priority": Priority.MEDIUM,
            "submitted_by": users["admin"],
            "artifacts": [
                {
                    "artifact_type": "complaint",
                    "filename": "demo_004_complaint.txt",
                    "text": (
                        "Customer queried whether the annual charge had been "
                        "disclosed, but later accepted that the fee explanation "
                        "was presented clearly before purchase."
                    ),
                },
                {
                    "artifact_type": "disclosure",
                    "filename": "demo_004_disclosure.txt",
                    "text": (
                        "Annual charge: 0.75% of invested balance. "
                        "This fee is charged monthly in arrears and is shown in "
                        "the worked example."
                    ),
                },
                {
                    "artifact_type": "support_transcript",
                    "filename": "demo_004_transcript.txt",
                    "text": (
                        "Agent walked through the annual charge, the monthly "
                        "application method, and where the fee would appear on "
                        "statements. Customer confirmed understanding."
                    ),
                },
            ],
        },
        {
            "reference_code": "DEMO-005",
            "title": "Seeded demo: delayed complaint handling",
            "case_type": CaseType.SUPPORT_REVIEW,
            "priority": Priority.HIGH,
            "submitted_by": users["analyst_1"],
            "artifacts": [
                {
                    "artifact_type": "complaint",
                    "filename": "demo_005_complaint.txt",
                    "text": (
                        "Customer says their complaint was not acknowledged for "
                        "three weeks and they had to chase several times for an "
                        "update."
                    ),
                },
                {
                    "artifact_type": "support_transcript",
                    "filename": "demo_005_transcript.txt",
                    "text": (
                        "Internal note shows the complaint inbox was backlogged "
                        "and no response was sent for 19 days after receipt."
                    ),
                },
                {
                    "artifact_type": "policy_excerpt",
                    "filename": "demo_005_policy.txt",
                    "text": (
                        "Complaint handling policy requires prompt "
                        "acknowledgement and regular customer updates "
                        "throughout the investigation period."
                    ),
                },
            ],
        },
        {
            "reference_code": "DEMO-006",
            "title": "Seeded demo: outdated script version",
            "case_type": CaseType.DISCLOSURE_REVIEW,
            "priority": Priority.HIGH,
            "submitted_by": users["analyst_2"],
            "artifacts": [
                {
                    "artifact_type": "complaint",
                    "filename": "demo_006_complaint.txt",
                    "text": (
                        "Customer says the adviser used an old script that "
                        "described charges that no longer matched the current "
                        "product literature."
                    ),
                },
                {
                    "artifact_type": "script",
                    "filename": "demo_006_script.txt",
                    "text": (
                        "Script version effective 2022 says there is no platform "
                        "fee and describes a promotional rate that ended in 2023."
                    ),
                },
                {
                    "artifact_type": "disclosure",
                    "filename": "demo_006_disclosure.txt",
                    "text": (
                        "Current 2025 disclosure states a platform fee applies "
                        "and that the promotional rate is no longer available."
                    ),
                },
            ],
        },
        {
            "reference_code": "DEMO-007",
            "title": "Seeded demo: ambiguous customer harm statement",
            "case_type": CaseType.COMPLAINT_REVIEW,
            "priority": Priority.MEDIUM,
            "submitted_by": users["admin"],
            "artifacts": [
                {
                    "artifact_type": "complaint",
                    "filename": "demo_007_complaint.txt",
                    "text": (
                        "Customer says the explanation left them worse off, "
                        "confused, and under pressure, but does not clearly "
                        "state whether a fee, delay, or product issue caused "
                        "the harm."
                    ),
                },
                {
                    "artifact_type": "support_transcript",
                    "filename": "demo_007_transcript.txt",
                    "text": (
                        "Call notes mention confusion and frustration but do not "
                        "clearly identify the specific product term or service "
                        "failure at issue."
                    ),
                },
            ],
        },
        {
            "reference_code": "DEMO-008",
            "title": "Seeded demo: duplicate artifact upload",
            "case_type": CaseType.DISCLOSURE_REVIEW,
            "priority": Priority.MEDIUM,
            "submitted_by": users["analyst_1"],
            "artifacts": [
                {
                    "artifact_type": "complaint",
                    "filename": "demo_008_complaint.txt",
                    "text": (
                        "Customer says they received the same disclosure twice "
                        "and remained unsure which version applied to their "
                        "account."
                    ),
                },
                {
                    "artifact_type": "disclosure",
                    "filename": "demo_008_disclosure_v1.txt",
                    "text": (
                        "Monthly account fee is £12. This copy appears to have "
                        "been uploaded twice during account setup."
                    ),
                },
                {
                    "artifact_type": "disclosure",
                    "filename": "demo_008_disclosure_v2.txt",
                    "text": (
                        "Monthly account fee is £12. This copy appears to have "
                        "been uploaded twice during account setup, with a "
                        "duplicate delivery notice attached."
                    ),
                },
            ],
        },
        {
            "reference_code": "DEMO-009",
            "title": "Seeded demo: schema-failure simulation",
            "case_type": CaseType.COMPLAINT_REVIEW,
            "priority": Priority.HIGH,
            "submitted_by": users["analyst_2"],
            "artifacts": [
                {
                    "artifact_type": "complaint",
                    "filename": "demo_009_complaint.txt",
                    "text": (
                        "Customer says the fee explanation was broken and "
                        "inconsistent. SIMULATE_SCHEMA_FAILURE seed scenario for "
                        "extraction review routing."
                    ),
                },
                {
                    "artifact_type": "internal_note",
                    "filename": "demo_009_note.txt",
                    "text": (
                        "This seeded case is intended to exercise "
                        "schema-failure handling paths and should route safely "
                        "to review if structured extraction is invalid."
                    ),
                },
            ],
        },
        {
            "reference_code": "DEMO-010",
            "title": "Seeded demo: provider failure simulation",
            "case_type": CaseType.SUPPORT_REVIEW,
            "priority": Priority.HIGH,
            "submitted_by": users["admin"],
            "artifacts": [
                {
                    "artifact_type": "complaint",
                    "filename": "demo_010_complaint.txt",
                    "text": (
                        "Customer says support communications were confusing and "
                        "incomplete. SIMULATE_PROVIDER_FAILURE seed scenario "
                        "for degraded-mode routing."
                    ),
                },
                {
                    "artifact_type": "policy_excerpt",
                    "filename": "demo_010_policy.txt",
                    "text": (
                        "When automated reasoning is unavailable, the case "
                        "should fall back to rules-based assessment and be "
                        "routed for analyst review."
                    ),
                },
            ],
        },
        {
            "reference_code": "DEMO-011",
            "title": "Seeded demo: strong contradiction across dates",
            "case_type": CaseType.DISCLOSURE_REVIEW,
            "priority": Priority.HIGH,
            "submitted_by": users["analyst_1"],
            "artifacts": [
                {
                    "artifact_type": "complaint",
                    "filename": "demo_011_complaint.txt",
                    "text": (
                        "Customer says they were told the fee change took "
                        "effect in January 2025, but their documents show "
                        "different dates."
                    ),
                },
                {
                    "artifact_type": "script",
                    "filename": "demo_011_script.txt",
                    "text": (
                        "Adviser script says the revised fee structure took "
                        "effect on 1 January 2025."
                    ),
                },
                {
                    "artifact_type": "disclosure",
                    "filename": "demo_011_disclosure.txt",
                    "text": (
                        "Formal disclosure states the revised fee structure "
                        "takes effect on 1 March 2025."
                    ),
                },
                {
                    "artifact_type": "policy_excerpt",
                    "filename": "demo_011_policy.txt",
                    "text": (
                        "Change-management note states customer communications "
                        "should reference the operative date of 15 February "
                        "2025."
                    ),
                },
            ],
        },
        {
            "reference_code": "DEMO-012",
            "title": "Seeded demo: strong consumer-support case with clear evidence",
            "case_type": CaseType.SUPPORT_REVIEW,
            "priority": Priority.MEDIUM,
            "submitted_by": users["analyst_2"],
            "artifacts": [
                {
                    "artifact_type": "complaint",
                    "filename": "demo_012_complaint.txt",
                    "text": (
                        "Customer initially reported difficulty accessing help, "
                        "but later confirmed the support team resolved the issue "
                        "quickly, clearly, and without repeat chasing."
                    ),
                },
                {
                    "artifact_type": "support_transcript",
                    "filename": "demo_012_transcript.txt",
                    "text": (
                        "Support transcript shows the issue was acknowledged "
                        "immediately, a clear explanation was given in plain "
                        "language, and the matter was resolved the same day."
                    ),
                },
                {
                    "artifact_type": "policy_excerpt",
                    "filename": "demo_012_policy.txt",
                    "text": (
                        "Support policy requires timely acknowledgement, "
                        "plain-language explanations, and same-day resolution "
                        "wherever feasible for routine servicing issues."
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
