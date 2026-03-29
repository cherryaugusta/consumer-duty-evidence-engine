import hashlib
import json
import os
import sys
import uuid
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

import django
import jsonschema

BASE_DIR = Path(__file__).resolve().parents[2]
BACKEND_DIR = BASE_DIR / "backend"

sys.path.append(str(BACKEND_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
django.setup()

from django.conf import settings  # noqa: E402

from apps.artifacts.models import SourceArtifact, SourceChannel  # noqa: E402
from apps.assessments.models import SupportAssessment  # noqa: E402
from apps.assessments.services import assess_case_support, detect_case_contradictions  # noqa: E402
from apps.cases.models import ReviewCase  # noqa: E402
from apps.core.constants import CaseStatus  # noqa: E402
from apps.extraction.models import Claim  # noqa: E402
from apps.extraction.services import extract_claims_for_case  # noqa: E402
from apps.obligations.models import ConsumerDutyOutcome, EvidenceLink  # noqa: E402
from apps.obligations.services import map_case_outcomes  # noqa: E402
from apps.parsing.services import parse_artifact_to_sections  # noqa: E402
from apps.recommendations.models import RecommendedAction  # noqa: E402
from apps.recommendations.services import generate_case_recommendation  # noqa: E402

EVALS_DIR = BASE_DIR / "evals"
DATASETS_DIR = EVALS_DIR / "datasets"
SCHEMAS_DIR = EVALS_DIR / "schemas"
REPORTS_DIR = EVALS_DIR / "reports"

EVAL_CASE_SCHEMA_PATH = SCHEMAS_DIR / "eval_case.schema.json"
EVAL_REPORT_SCHEMA_PATH = SCHEMAS_DIR / "eval_report.schema.json"

REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def load_json(path: Path):
    with open(path, encoding="utf-8") as file_handle:
        return json.load(file_handle)


def validate_json(data, schema, source_path: Path):
    try:
        jsonschema.validate(instance=data, schema=schema)
    except jsonschema.ValidationError as exc:
        print(f"\nSchema validation failed for: {source_path}")
        print(f"Error: {exc.message}")
        sys.exit(1)


def collect_eval_files():
    files = []
    for dataset_type in [
        "golden_cases",
        "adversarial_cases",
        "routing_cases",
        "citation_cases",
    ]:
        dataset_dir = DATASETS_DIR / dataset_type
        if dataset_dir.exists():
            files.extend(sorted(dataset_dir.glob("*.json")))
    return files


def normalize_outcome_code(code: str) -> str:
    if code == "fair_value":
        return "price_value"
    return code


def ensure_outcomes_exist():
    required_outcomes = [
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
            "description": "Legacy fair value code used by existing mapping logic.",
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

    for outcome in required_outcomes:
        ConsumerDutyOutcome.objects.update_or_create(
            code=outcome["code"],
            defaults={
                "name": outcome["name"],
                "description": outcome["description"],
                "active": True,
            },
        )


def build_eval_storage_path(case_id: str, artifact_index: int) -> str:
    return f"eval_inputs/{case_id}/{artifact_index:02d}.txt"


def write_eval_artifact(storage_path: str, text: str) -> None:
    media_root = Path(settings.MEDIA_ROOT)
    file_path = media_root / storage_path
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(text, encoding="utf-8")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def infer_case_type(eval_case: dict) -> str:
    return "complaint_review"


def create_case(eval_case: dict) -> ReviewCase:
    return ReviewCase.objects.create(
        reference_code=f"EVAL-{uuid.uuid4().hex[:8].upper()}",
        title=f"Eval: {eval_case['case_id']}",
        case_type=infer_case_type(eval_case),
        correlation_id=str(uuid.uuid4()),
        status=CaseStatus.INGESTION_PENDING,
        dedupe_key=f"eval::{eval_case['case_id']}",
        eval_case_id=eval_case["case_id"],
    )


def create_artifacts(case: ReviewCase, eval_case: dict) -> list[SourceArtifact]:
    artifacts = []

    for index, artifact_data in enumerate(eval_case["artifacts"], start=1):
        storage_path = build_eval_storage_path(eval_case["case_id"], index)
        artifact_text = artifact_data["text"]
        write_eval_artifact(storage_path, artifact_text)

        artifact = SourceArtifact.objects.create(
            case=case,
            artifact_type=artifact_data["artifact_type"],
            filename=f"{eval_case['case_id']}_{index:02d}.txt",
            mime_type="text/plain",
            source_channel=SourceChannel.API,
            storage_path=storage_path,
            sha256_checksum=sha256_text(artifact_text),
        )
        artifacts.append(artifact)

    return artifacts


def run_case(eval_case: dict) -> ReviewCase:
    case = create_case(eval_case)
    artifacts = create_artifacts(case, eval_case)

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
    return case


def evaluate_claims(case: ReviewCase, expected: dict) -> dict:
    actual_claims = list(Claim.objects.filter(case=case).values_list("claim_type", "claim_text"))
    expected_claims = expected["expected_claims"]

    matched_expected = 0
    matched_actual_indexes = set()

    for expected_claim in expected_claims:
        expected_type = expected_claim["claim_type"]
        expected_substring = expected_claim["claim_text_contains"].lower()

        for actual_index, (actual_type, actual_text) in enumerate(actual_claims):
            actual_text_lower = (actual_text or "").lower()
            if actual_type == expected_type and expected_substring in actual_text_lower:
                matched_expected += 1
                matched_actual_indexes.add(actual_index)
                break

    actual_count = len(actual_claims)
    expected_count = len(expected_claims)

    precision = matched_expected / actual_count if actual_count else 0.0
    recall = matched_expected / expected_count if expected_count else 0.0

    return {
        "matched_expected": matched_expected,
        "actual_count": actual_count,
        "expected_count": expected_count,
        "precision": precision,
        "recall": recall,
        "all_expected_matched": matched_expected == expected_count,
        "any_claims_found": actual_count > 0,
    }


def evaluate_outcomes(case: ReviewCase, expected: dict) -> dict:
    actual_codes = {
        normalize_outcome_code(code)
        for code in EvidenceLink.objects.filter(case=case).values_list(
            "outcome__code",
            flat=True,
        )
    }
    expected_codes = {normalize_outcome_code(code) for code in expected["expected_outcomes"]}

    matches = actual_codes == expected_codes

    return {
        "actual_codes": sorted(actual_codes),
        "expected_codes": sorted(expected_codes),
        "exact_match": matches,
    }


def evaluate_support_status(case: ReviewCase, expected: dict) -> dict:
    expected_status = expected["expected_support_status"]
    actual_statuses = list(
        SupportAssessment.objects.filter(case=case).values_list("status", flat=True)
    )
    match = expected_status in actual_statuses

    return {
        "expected_status": expected_status,
        "actual_statuses": actual_statuses,
        "match": match,
    }


def evaluate_routing(case: ReviewCase, expected: dict) -> dict:
    expected_requires_review = expected["expected_requires_review"]
    expected_action = expected["expected_recommended_action"]

    actual_requires_review = case.status == CaseStatus.NEEDS_REVIEW
    actual_action = None

    if hasattr(case, "recommendation"):
        actual_action = case.recommendation.recommended_action

    requires_review_match = actual_requires_review == expected_requires_review
    action_match = actual_action == expected_action

    return {
        "expected_requires_review": expected_requires_review,
        "actual_requires_review": actual_requires_review,
        "expected_action": expected_action,
        "actual_action": actual_action,
        "requires_review_match": requires_review_match,
        "action_match": action_match,
    }


def evaluate_citations(case: ReviewCase, expected: dict) -> dict:
    actual_artifact_types = {
        artifact_type
        for artifact_type in EvidenceLink.objects.filter(case=case).values_list(
            "section__artifact__artifact_type",
            flat=True,
        )
        if artifact_type
    }
    expected_artifact_types = {
        item["artifact_type"] for item in expected["expected_citation_targets"]
    }

    match = expected_artifact_types.issubset(actual_artifact_types)

    return {
        "actual_artifact_types": sorted(actual_artifact_types),
        "expected_artifact_types": sorted(expected_artifact_types),
        "match": match,
    }


def build_case_summary(result: dict) -> dict:
    checks = {
        "claims": result["claim_result"]["all_expected_matched"],
        "mapping": result["outcome_result"]["exact_match"],
        "support": result["support_result"]["match"],
        "routing": result["routing_result"]["requires_review_match"],
        "citation": result["citation_result"]["match"],
    }
    passed_checks = sum(1 for passed in checks.values() if passed)
    total_checks = len(checks)
    score = passed_checks / total_checks if total_checks else 0.0

    failed_checks = [name for name, passed in checks.items() if not passed]

    return {
        "case_id": result["case_id"],
        "score": round(score, 4),
        "passed_checks": passed_checks,
        "total_checks": total_checks,
        "all_passed": passed_checks == total_checks,
        "failed_checks": failed_checks,
    }


def evaluate_case(case: ReviewCase, expected: dict) -> dict:
    claim_result = evaluate_claims(case, expected)
    outcome_result = evaluate_outcomes(case, expected)
    support_result = evaluate_support_status(case, expected)
    routing_result = evaluate_routing(case, expected)
    citation_result = evaluate_citations(case, expected)

    result = {
        "case_id": expected["case_id"],
        "scenario_type": expected["scenario_type"],
        "claim_result": claim_result,
        "outcome_result": outcome_result,
        "support_result": support_result,
        "routing_result": routing_result,
        "citation_result": citation_result,
    }
    result["summary"] = build_case_summary(result)
    return result


def aggregate_metrics(results: list[dict]) -> dict:
    total = len(results)
    if total == 0:
        return {
            "claim_precision": 0.0,
            "claim_recall": 0.0,
            "mapping_accuracy": 0.0,
            "citation_validity_rate": 0.0,
            "routing_accuracy": 0.0,
            "support_status_accuracy": 0.0,
            "degraded_mode_success_rate": 0.0,
            "pass_rate": 0.0,
        }

    claim_precision = sum(r["claim_result"]["precision"] for r in results) / total
    claim_recall = sum(r["claim_result"]["recall"] for r in results) / total
    mapping_accuracy = sum(1 for r in results if r["outcome_result"]["exact_match"]) / total
    citation_validity_rate = sum(1 for r in results if r["citation_result"]["match"]) / total
    routing_accuracy = (
        sum(1 for r in results if r["routing_result"]["requires_review_match"]) / total
    )
    support_status_accuracy = sum(1 for r in results if r["support_result"]["match"]) / total

    degraded_cases = [
        r for r in results if r["routing_result"]["expected_action"] == RecommendedAction.REVIEW
    ]
    if degraded_cases:
        degraded_mode_success_rate = sum(
            1 for r in degraded_cases if r["routing_result"]["action_match"]
        ) / len(degraded_cases)
    else:
        degraded_mode_success_rate = 1.0

    pass_rate = sum(1 for r in results if r["summary"]["all_passed"]) / total

    return {
        "claim_precision": round(claim_precision, 4),
        "claim_recall": round(claim_recall, 4),
        "mapping_accuracy": round(mapping_accuracy, 4),
        "citation_validity_rate": round(citation_validity_rate, 4),
        "routing_accuracy": round(routing_accuracy, 4),
        "support_status_accuracy": round(support_status_accuracy, 4),
        "degraded_mode_success_rate": round(degraded_mode_success_rate, 4),
        "pass_rate": round(pass_rate, 4),
    }


def build_failure_breakdown(results: list[dict]) -> dict:
    counter = Counter()

    for result in results:
        for failed_check in result["summary"]["failed_checks"]:
            counter[failed_check] += 1

    return {
        "claims": counter.get("claims", 0),
        "mapping": counter.get("mapping", 0),
        "support": counter.get("support", 0),
        "routing": counter.get("routing", 0),
        "citation": counter.get("citation", 0),
    }


def build_scenario_breakdown(results: list[dict]) -> dict:
    scenario_map: dict[str, dict] = {}

    for result in results:
        scenario_type = result["scenario_type"]
        if scenario_type not in scenario_map:
            scenario_map[scenario_type] = {
                "total_cases": 0,
                "fully_passed_cases": 0,
                "average_score": 0.0,
            }

        scenario_map[scenario_type]["total_cases"] += 1
        if result["summary"]["all_passed"]:
            scenario_map[scenario_type]["fully_passed_cases"] += 1

    for scenario_type in scenario_map:
        scenario_results = [r for r in results if r["scenario_type"] == scenario_type]
        avg_score = sum(r["summary"]["score"] for r in scenario_results) / len(scenario_results)
        scenario_map[scenario_type]["average_score"] = round(avg_score, 4)

    return scenario_map


def build_ranked_case_lists(results: list[dict]) -> tuple[list[dict], list[dict]]:
    ranked = sorted(
        [
            {
                "case_id": r["case_id"],
                "scenario_type": r["scenario_type"],
                "score": r["summary"]["score"],
                "failed_checks": r["summary"]["failed_checks"],
            }
            for r in results
        ],
        key=lambda item: (item["score"], item["case_id"]),
    )

    top_failures = ranked[:5]
    top_successes = list(reversed(ranked[-5:]))

    return top_failures, top_successes


def build_report(results: list[dict], metrics: dict) -> dict:
    failure_breakdown = build_failure_breakdown(results)
    scenario_breakdown = build_scenario_breakdown(results)
    top_failures, top_successes = build_ranked_case_lists(results)

    return {
        "run_label": f"real-run-{datetime.now(UTC).isoformat()}",
        "summary_metrics": metrics,
        "thresholds": {
            "mapping_accuracy_min": 0.8,
            "false_negative_rate_max": 0.2,
            "citation_validity_min": 0.85,
            "support_status_accuracy_min": 0.8,
            "degraded_mode_success_min": 0.9,
        },
        "total_cases": len(results),
        "failure_breakdown": failure_breakdown,
        "scenario_breakdown": scenario_breakdown,
        "top_failures": top_failures,
        "top_successes": top_successes,
        "results": results,
    }


def main():
    print("\n=== Running REAL Eval Suite ===")

    eval_case_schema = load_json(EVAL_CASE_SCHEMA_PATH)
    eval_report_schema = load_json(EVAL_REPORT_SCHEMA_PATH)

    ensure_outcomes_exist()

    eval_files = collect_eval_files()
    print(f"Found {len(eval_files)} eval files")

    eval_cases = []
    for path in eval_files:
        data = load_json(path)
        validate_json(data, eval_case_schema, path)
        eval_cases.append(data)

    print("All eval cases passed schema validation")

    results = []

    for eval_case in eval_cases:
        print(f"\n--- Running {eval_case['case_id']} ---")
        case = run_case(eval_case)
        result = evaluate_case(case, eval_case)
        results.append(result)

        print(
            json.dumps(
                {
                    "case_id": result["case_id"],
                    "scenario_type": result["scenario_type"],
                    "score": result["summary"]["score"],
                    "failed_checks": result["summary"]["failed_checks"],
                },
                indent=2,
            )
        )

    metrics = aggregate_metrics(results)
    report = build_report(results, metrics)

    validate_json(report, eval_report_schema, Path("generated-report"))

    output_path = REPORTS_DIR / "latest-report.json"
    with open(output_path, "w", encoding="utf-8") as file_handle:
        json.dump(report, file_handle, indent=2)

    print(f"\nEval report generated at: {output_path}")
    print(json.dumps(report["summary_metrics"], indent=2))
    print(json.dumps(report["failure_breakdown"], indent=2))


if __name__ == "__main__":
    main()
