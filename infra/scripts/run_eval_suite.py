import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import jsonschema

BASE_DIR = Path(__file__).resolve().parents[2]
EVALS_DIR = BASE_DIR / "evals"
DATASETS_DIR = EVALS_DIR / "datasets"
SCHEMAS_DIR = EVALS_DIR / "schemas"
REPORTS_DIR = EVALS_DIR / "reports"

EVAL_CASE_SCHEMA_PATH = SCHEMAS_DIR / "eval_case.schema.json"
EVAL_REPORT_SCHEMA_PATH = SCHEMAS_DIR / "eval_report.schema.json"

REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def load_json(path: Path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_schema(path: Path):
    return load_json(path)


def validate_json(data, schema, source_path: Path):
    try:
        jsonschema.validate(instance=data, schema=schema)
    except jsonschema.ValidationError as e:
        print(f"\n❌ Schema validation failed for: {source_path}")
        print(f"Error: {e.message}")
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
        if not dataset_dir.exists():
            continue
        files.extend(dataset_dir.glob("*.json"))
    return files


def run_placeholder_evaluation(eval_cases):
    """
    Placeholder evaluator.

    For now:
    - assumes all expectations are met
    - returns perfect metrics

    This will be replaced later with real pipeline calls.
    """

    total = len(eval_cases)

    if total == 0:
        return {
            "claim_precision": 0.0,
            "claim_recall": 0.0,
            "mapping_accuracy": 0.0,
            "citation_validity_rate": 0.0,
            "routing_accuracy": 0.0,
            "support_status_accuracy": 0.0,
            "degraded_mode_success_rate": 0.0,
        }

    return {
        "claim_precision": 1.0,
        "claim_recall": 1.0,
        "mapping_accuracy": 1.0,
        "citation_validity_rate": 1.0,
        "routing_accuracy": 1.0,
        "support_status_accuracy": 1.0,
        "degraded_mode_success_rate": 1.0,
    }


def build_report(metrics):
    report = {
        "run_label": f"local-run-{datetime.now(UTC).isoformat()}",
        "summary_metrics": metrics,
        "thresholds": {
            "mapping_accuracy_min": 0.8,
            "false_negative_rate_max": 0.2,
            "citation_validity_min": 0.85,
            "support_status_accuracy_min": 0.8,
            "degraded_mode_success_min": 0.9,
        },
    }
    return report


def main():
    print("\n=== Running Eval Suite ===")

    eval_case_schema = load_schema(EVAL_CASE_SCHEMA_PATH)
    eval_report_schema = load_schema(EVAL_REPORT_SCHEMA_PATH)

    eval_files = collect_eval_files()

    print(f"Found {len(eval_files)} eval files")

    eval_cases = []

    for file_path in eval_files:
        data = load_json(file_path)
        validate_json(data, eval_case_schema, file_path)
        eval_cases.append(data)

    print("✅ All eval cases passed schema validation")

    metrics = run_placeholder_evaluation(eval_cases)
    report = build_report(metrics)

    validate_json(report, eval_report_schema, Path("generated-report"))

    output_path = REPORTS_DIR / "latest-report.json"

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"\n✅ Eval report generated at: {output_path}")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
