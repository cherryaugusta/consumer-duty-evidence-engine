# Evaluation Design

## Purpose

The evaluation framework exists to measure system behavior across the full evidence review workflow.

It is designed to answer practical questions:

- Does the system extract the right claims?
- Does it map those claims to the right outcome areas?
- Does it assign the right support status?
- Does it route uncertain cases safely?
- Does degraded mode behave correctly when provider-backed steps fail?
- Are citations linked to the right underlying evidence?

This project treats evaluation as a system capability, not as a one-off notebook exercise.

---

## Evaluation Scope

The eval harness measures the behavior of the pipeline across these stages:

1. parsing input artifacts into text-backed sections
2. extracting structured claims
3. mapping claims to canonical Consumer Duty outcome codes
4. assessing evidence sufficiency
5. routing cases to approve, review, escalate, or request more evidence
6. validating citation coverage and degraded-mode behavior

The eval suite does not only assess a single model output. It evaluates the workflow end to end.

---

## Evaluation Execution Model

The eval runner is implemented at:

- `infra/scripts/run_eval_suite.py`

The runner:

- initializes Django
- loads eval case JSON files from `evals/datasets/`
- validates each file against the eval case schema
- writes artifact text files into `MEDIA_ROOT`
- executes the real backend services synchronously
- compares actual outputs against expected outputs
- writes a regression report to `evals/reports/latest-report.json`

Important implementation property:

- the eval runner executes real backend logic directly
- it does not require Celery to be running
- it does require PostgreSQL and Redis to be available under the configured environment

This makes the eval harness suitable for both local regression checks and CI runs.

---

## Dataset Structure

Eval datasets live under:

- `evals/datasets/golden_cases/`
- `evals/datasets/adversarial_cases/`
- `evals/datasets/routing_cases/`
- `evals/datasets/citation_cases/`

Schemas live under:

- `evals/schemas/eval_case.schema.json`
- `evals/schemas/eval_report.schema.json`

Reports are written under:

- `evals/reports/`

Runs can be stored under:

- `evals/runs/`

---

## Eval Case Shape

Each eval case defines:

- scenario identity
- one or more input artifacts
- expected extracted claims
- expected mapped outcomes
- expected support status
- expected review-routing behavior
- expected recommendation action
- expected citation targets

This allows the same dataset to test multiple workflow stages in one pass.

---

## Scenario Categories

The dataset is intentionally mixed to represent both straightforward and failure-prone conditions.

### 1. Golden Cases

These represent normal, understandable inputs where the system should behave well.

Examples:

- clear fee-disclosure issue
- strong consumer-support evidence
- well-supported disclosure case

These cases are useful for checking:

- claim recall
- mapping consistency
- correct approvals when evidence is sufficient

---

### 2. Adversarial Cases

These are deliberately messy or difficult.

Examples:

- unusual formatting
- ambiguous wording
- weakly signalled customer harm
- schema-failure simulation

These cases are useful for checking:

- extraction robustness
- review routing under uncertainty
- resistance to overconfident auto-approval

---

### 3. Routing Cases

These focus on the routing decision rather than only extraction quality.

Examples:

- contradictory evidence
- outdated script version
- missing support
- provider failure simulation

These cases are useful for checking:

- `needs_review`
- `escalated`
- `request_more_evidence`
- degraded mode behavior

---

### 4. Citation Cases

These verify that the system links output claims and recommendations to the correct evidence sources.

These cases are useful for checking:

- citation validity rate
- provenance integrity
- evidence-link correctness

---

## Metrics

The current evaluation framework tracks these metrics.

### Claim Precision

Definition:

- among extracted claims, how many were correct

Why it matters:

- low precision means noisy extraction and analyst burden

---

### Claim Recall

Definition:

- among expected claims, how many were found

Why it matters:

- low recall means important issues may be missed

---

### Mapping Accuracy

Definition:

- how often extracted claims are mapped to the correct canonical outcome code

Why it matters:

- outcome mapping is central to the Consumer Duty-style workflow story

---

### Citation Validity Rate

Definition:

- proportion of expected citation targets correctly linked to evidence

Why it matters:

- unsupported recommendations reduce trust in the system

---

### Routing Accuracy

Definition:

- how often the system chooses the expected workflow route

Examples:

- approve
- review
- escalate
- request more evidence

Why it matters:

- safe routing is more important than polished text generation

---

### Support Status Accuracy

Definition:

- how often the system classifies support correctly

Allowed statuses:

- `supported`
- `weak_support`
- `missing_support`
- `contradictory_support`
- `stale_support`

Why it matters:

- support assessment drives downstream recommendation and review load

---

### Degraded Mode Success Rate

Definition:

- how often the system behaves correctly when provider-backed paths fail

Why it matters:

- failure handling is a core portfolio claim of this project

---

### Pass Rate

Definition:

- proportion of eval cases that met the expected combined outcome criteria

Why it matters:

- gives a compact top-line signal for regression tracking

---

## Current Verified Baseline

The most recent verified eval checkpoint produced:

- `claim_precision: 0.6333`
- `claim_recall: 1.0`
- `mapping_accuracy: 0.95`
- `citation_validity_rate: 1.0`
- `routing_accuracy: 0.85`
- `support_status_accuracy: 1.0`
- `degraded_mode_success_rate: 1.0`
- `pass_rate: 0.8`

Failure breakdown at that checkpoint:

- `claims: 0`
- `mapping: 1`
- `support: 0`
- `routing: 3`
- `citation: 0`

Interpretation:

- claim recall is strong
- mapping is strong enough for current portfolio purposes
- citation validity is strong
- support scoring is strong
- degraded mode behavior is strong
- the remaining misses are mostly routing-related and acceptable for the current milestone

This checkpoint is intentionally treated as good enough to move forward without more rule churn.

---

## Threshold Philosophy

This project does not pretend to be production regulatory software, so thresholds are used as portfolio discipline rather than regulatory sign-off.

Current threshold philosophy:

- prioritize safe routing over aggressive auto-approval
- prefer review routing when evidence is weak or contradictory
- treat citation validity as non-negotiable
- treat degraded mode correctness as essential

A strong benchmark report should show that:

- false confidence is limited
- contradictions are surfaced
- missing evidence forces review
- provider failures degrade safely

---

## Why the Eval Harness Uses Real Services

The eval runner uses the actual Django services instead of mock-only logic because that gives stronger signal on:

- orchestration correctness
- state progression behavior
- artifact handling
- assessment logic
- recommendation routing
- regression risk after code changes

This is more useful for portfolio credibility than isolated metric-only evaluation.

---

## What the Eval Harness Demonstrates

The eval framework shows that the project includes:

- measurable system behavior
- reproducible regression checks
- synthetic benchmark discipline
- explicit success and failure case design
- safety-oriented evaluation rather than demo-only behavior

That is a stronger engineering signal than a one-time happy-path demo.

---

## Limitations

The current eval harness still has limitations.

### 1. Synthetic Data

The datasets are synthetic and portfolio-oriented. They do not represent real regulated production data.

### 2. Narrow Taxonomy

The project uses four canonical outcome codes rather than a broader regulatory taxonomy.

### 3. Limited Document Complexity

The parsing layer is sufficient for the portfolio workflow but not designed as a full production document-ingestion system.

### 4. Metrics Reflect Current Rule/Workflow Design

The benchmark measures the current hybrid logic. It is not a general benchmark for arbitrary compliance reasoning.

These limitations are acceptable because the goal is to demonstrate disciplined system design, fallback handling, and measurable workflow behavior.

---

## Recommended Use in Demo and README

When presenting this project, the evaluation story should be framed as:

- a regression harness for workflow quality
- a measurable proof that the system does more than generate text
- evidence that routing, citation validity, and fallback behavior are tested

The strongest message is:

- this project evaluates system decisions, not just model outputs