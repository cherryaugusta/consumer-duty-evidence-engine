# Ingestion Pipeline Architecture

## Purpose

The ingestion pipeline is responsible for taking uploaded artifacts and transforming them into structured, assessable cases.

It guarantees:

- deterministic processing flow
- safe failure handling
- async scalability via Celery
- traceability via audit + correlation IDs

---

## High-Level Flow

```mermaid
flowchart LR
    A[Upload Artifact] --> B[Create Case]
    B --> C[Queue Parsing Task]
    C --> D[Parse Artifact]
    D --> E[Store Parsed Output]

    E --> F[Queue Extraction]
    F --> G[Extract Structured Data]

    G --> H[Queue Mapping]
    H --> I[Map to Obligations]

    I --> J[Queue Assessment]
    J --> K[Run Assessment]

    K --> L[Queue Recommendation]
    L --> M[Generate Recommendations]

    M --> N[Finalize Case]
````

---

## Pipeline Stages (Mapped to Code)

### 1. Artifact Upload

**Entry point:**

* API endpoint (Django view)

**Responsibilities:**

* store raw file
* create `Case` record
* assign `correlation_id`

**Next step:**

* enqueue parsing

```python
parse_artifact_task.delay(case_id)
```

---

### 2. Parsing

**Task:**

* `apps.parsing.tasks.parse_artifact_task`

**Responsibilities:**

* read artifact (PDF, DOCX, etc.)
* extract raw text
* normalize content

**State transition:**

* `INGESTION_PENDING → PARSING → PARSED`

**Failure:**

* `→ FAILED`

---

### 3. Extraction

**Task:**

* `apps.extraction.tasks.extract_case_task`

**Responsibilities:**

* convert raw text → structured schema
* apply validation
* attach confidence scores

**Outputs:**

* entities
* fields
* metadata

**State transition:**

* `PARSED → EXTRACTION_PENDING → EXTRACTED`

**Edge cases:**

* low confidence → `NEEDS_REVIEW`

---

### 4. Mapping

**Task:**

* `apps.obligations.tasks.map_case_task`

**Responsibilities:**

* map extracted data → regulatory obligations
* link evidence to rules

**State transition:**

* `EXTRACTED → MAPPING_PENDING → MAPPED`

---

### 5. Assessment

**Task:**

* `apps.assessments.tasks.assess_case_task`

**Responsibilities:**

* evaluate compliance
* compute risk signals
* determine pass/fail/uncertain

**State transition:**

* `MAPPED → ASSESSMENT_PENDING → ASSESSED`

**Edge cases:**

* ambiguity → `NEEDS_REVIEW`

---

### 6. Recommendation

**Task:**

* `apps.recommendations.tasks.recommend_case_task`

**Responsibilities:**

* generate remediation suggestions
* prioritise issues

---

### 7. Finalization

**Task:**

* `apps.artifacts.tasks.finalize_case_parsing`

**Responsibilities:**

* mark pipeline complete
* ensure consistency
* emit final audit event

**Final states:**

* `APPROVED`
* `NEEDS_REVIEW`
* `ESCALATED`

---

## Task Orchestration Pattern

Pipeline uses **task chaining via explicit enqueueing**, not Celery chains.

Pattern:

```python
def parse_artifact_task(case_id):
    # process
    extract_case_task.delay(case_id)
```

Advantages:

* simpler debugging
* better retry control
* explicit state transitions

---

## Queue + Broker

**Broker:**

* Redis (`redis://localhost:6379/1`)

**Result backend:**

* Redis (`redis://localhost:6379/2`)

**Worker:**

* Celery

Windows-compatible mode:

```bash
celery -A config worker -l info -P solo
```

---

## Failure Handling Strategy

Each stage:

* wrapped in try/except
* updates case status on failure
* logs structured error

```python
try:
    ...
except Exception:
    case.status = FAILED
    case.save()
```

Retry strategy:

* manual or controlled retry via state machine
* no blind automatic retries

---

## Idempotency

All tasks must be idempotent:

* safe to re-run
* no duplicate side effects
* check existing outputs before writing

Example:

```python
if case.parsed_output_exists:
    return
```

---

## Observability

### Logging

* structured logs (JSON)
* include:

  * `case_id`
  * `correlation_id`
  * `stage`

### Audit Events

Each stage emits:

* `case.stage.started`
* `case.stage.completed`
* `case.stage.failed`

---

## WebSocket Updates

After each transition:

```json
{
  "case_id": "<uuid>",
  "status": "parsing",
  "timestamp": "<iso8601>"
}
```

Supports real-time UI updates.

---

## Degraded Mode

If external services fail:

* pipeline continues with reduced capability
* flags case as:

  * `degraded_mode_active = true`

Triggers:

* `NEEDS_REVIEW` routing

---

## Why This Matters

This pipeline design ensures:

* scalability via async workers
* strict control via state machine
* resilience to partial failure
* clear separation of responsibilities
* strong auditability for compliance use cases

---