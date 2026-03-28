# ADR 0003: State Machine Enforced Workflow

## Status

Accepted

---

## Context

The system processes cases through multiple asynchronous stages:

- parsing
- extraction
- mapping
- assessment
- recommendation
- finalization

Without strict control, risks include:

- invalid transitions (e.g., assessment before extraction)
- duplicate processing
- race conditions from Celery workers
- inconsistent case states
- difficulty debugging failures

The system must guarantee:

- deterministic execution
- safe retries
- clear visibility of progress
- enforceable ordering of stages

---

## Decision

The system enforces a **state machine-driven workflow** for all case processing.

This means:

- each case has a single explicit state
- transitions are strictly defined and validated
- no stage executes unless the case is in the correct state
- invalid transitions are rejected

---

## Implementation

### State Definition

Path:
`backend/apps/cases/models.py`

Example:

```python
class CaseStatus(models.TextChoices):
    INGESTION_PENDING = "INGESTION_PENDING"
    PARSING = "PARSING"
    PARSED = "PARSED"
    EXTRACTION = "EXTRACTION"
    EXTRACTED = "EXTRACTED"
    MAPPING = "MAPPING"
    MAPPED = "MAPPED"
    ASSESSMENT = "ASSESSMENT"
    ASSESSED = "ASSESSED"
    RECOMMENDATION = "RECOMMENDATION"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
````

---

### Transition Logic

Path:
`backend/apps/cases/state_machine.py`

```python
from apps.cases.models import CaseStatus

VALID_TRANSITIONS = {
    CaseStatus.INGESTION_PENDING: [CaseStatus.PARSING],
    CaseStatus.PARSING: [CaseStatus.PARSED, CaseStatus.FAILED],
    CaseStatus.PARSED: [CaseStatus.EXTRACTION],
    CaseStatus.EXTRACTION: [CaseStatus.EXTRACTED, CaseStatus.FAILED],
    CaseStatus.EXTRACTED: [CaseStatus.MAPPING],
    CaseStatus.MAPPING: [CaseStatus.MAPPED, CaseStatus.FAILED],
    CaseStatus.MAPPED: [CaseStatus.ASSESSMENT],
    CaseStatus.ASSESSMENT: [CaseStatus.ASSESSED, CaseStatus.FAILED],
    CaseStatus.ASSESSED: [CaseStatus.RECOMMENDATION],
    CaseStatus.RECOMMENDATION: [CaseStatus.COMPLETED, CaseStatus.FAILED],
}
```

---

### Transition Function

Path:
`backend/apps/cases/state_machine.py`

```python
def transition_case(case, new_status):
    current = case.status

    if new_status not in VALID_TRANSITIONS.get(current, []):
        raise ValueError(f"Invalid transition: {current} -> {new_status}")

    case.status = new_status
    case.save(update_fields=["status"])
```

---

### Usage in Tasks

Each Celery task must:

1. validate current state
2. transition to "in-progress" state
3. execute logic
4. transition to "completed" state

Example:

Path:
`backend/apps/parsing/tasks.py`

```python
from apps.cases.state_machine import transition_case
from apps.cases.models import CaseStatus

@shared_task
def parse_artifact_task(case_id):
    case = Case.objects.get(id=case_id)

    transition_case(case, CaseStatus.PARSING)

    # parsing logic here

    transition_case(case, CaseStatus.PARSED)
```

---

## Failure Handling

On failure:

* case transitions to FAILED
* audit event emitted
* structured log recorded

Example:

```python
try:
    # stage logic
    transition_case(case, CaseStatus.EXTRACTED)
except Exception as e:
    transition_case(case, CaseStatus.FAILED)
    raise
```

---

## Why Not Implicit Workflow

Implicit workflows (no state machine) were rejected because:

* ordering is not enforced
* retries may corrupt state
* debugging becomes difficult
* concurrency issues increase
* system behavior becomes non-deterministic

---

## Benefits

* strict ordering guarantees
* safe retries (idempotent transitions)
* easier debugging (explicit state)
* UI can display progress reliably
* audit alignment with state transitions
* prevents invalid execution paths

---

## Trade-offs

* additional implementation complexity
* requires discipline in all tasks
* migration needed if states change

---

## Consequences

The system:

* rejects invalid transitions at runtime
* enforces stage boundaries
* treats state as the source of truth
* enables reliable orchestration with Celery

---

## Example Flow

1. INGESTION_PENDING
2. PARSING → PARSED
3. EXTRACTION → EXTRACTED
4. MAPPING → MAPPED
5. ASSESSMENT → ASSESSED
6. RECOMMENDATION → COMPLETED

Failures at any stage move the case to FAILED.

---

## Future Evolution

Possible improvements:

* transition audit hooks
* retry policies per state
* parallel branches (if needed)
* state transition metrics

---

## Summary

The state machine enforces correctness, determinism, and observability across the entire pipeline.

It is essential for operating a reliable asynchronous processing system.

---