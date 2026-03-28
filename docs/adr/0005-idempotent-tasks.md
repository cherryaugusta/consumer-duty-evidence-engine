# ADR 0005: Idempotent Tasks

## Status

Accepted

---

## Context

The system relies on asynchronous task execution using Celery.

Risks:

- tasks may run more than once
- retries may occur after partial completion
- workers may crash mid-execution
- duplicate messages may be delivered

Without safeguards, this leads to:

- duplicated database writes
- inconsistent case state
- corrupted outputs
- non-deterministic behavior

---

## Decision

All Celery tasks must be **idempotent**.

This means:

- running the same task multiple times produces the same result
- no duplicate side effects occur
- tasks can safely retry

---

## Implementation

### Rule 1: Check Current State Before Execution

Path:
`backend/apps/parsing/tasks.py`

```python
from apps.cases.models import CaseStatus

if case.status != CaseStatus.PARSED:
    return
````

---

### Rule 2: Use State Machine as Gatekeeper

Path:
`backend/apps/cases/state_machine.py`

```python
transition_case(case, CaseStatus.EXTRACTION)
```

If invalid → task stops.

---

### Rule 3: Avoid Duplicate Writes

Use `update_or_create` or `get_or_create`

Example:

Path:
`backend/apps/extraction/services.py`

```python
obj, _ = ExtractedData.objects.update_or_create(
    case=case,
    defaults={"data": extracted_payload},
)
```

---

### Rule 4: Use Unique Constraints

Path:
`backend/apps/extraction/models.py`

```python
class ExtractedData(models.Model):
    case = models.OneToOneField("cases.Case", on_delete=models.CASCADE)
    data = models.JSONField()
```

---

### Rule 5: Idempotent Audit Events

Avoid duplicate events:

```python
if not AuditEvent.objects.filter(
    case=case,
    event_type="case.extraction.completed"
).exists():
    emit_audit_event(...)
```

---

### Rule 6: Safe Retry Pattern

```python
try:
    # work
except Exception:
    raise self.retry(countdown=5)
```

---

### Rule 7: No External Side Effects Without Guard

Example:

```python
if not case.notification_sent:
    send_notification()
    case.notification_sent = True
    case.save(update_fields=["notification_sent"])
```

---

## Example Task (Fully Idempotent)

Path:
`backend/apps/extraction/tasks.py`

```python
from celery import shared_task
from apps.cases.models import Case, CaseStatus
from apps.cases.state_machine import transition_case
from apps.audit.services import emit_audit_event


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def extract_case_task(self, case_id):
    case = Case.objects.get(id=case_id)

    if case.status != CaseStatus.PARSED:
        return

    transition_case(case, CaseStatus.EXTRACTION)

    emit_audit_event(case, "case.extraction.started", case.correlation_id)

    try:
        # extraction logic here

        transition_case(case, CaseStatus.EXTRACTED)

        emit_audit_event(
            case,
            "case.extraction.completed",
            case.correlation_id,
        )

    except Exception as e:
        emit_audit_event(
            case,
            "case.extraction.failed",
            case.correlation_id,
            metadata={"error": str(e)},
        )
        transition_case(case, CaseStatus.FAILED)
        raise
```

---

## Why Not Assume Single Execution

Rejected because:

* Celery guarantees **at least once delivery**, not exactly once
* network failures can cause retries
* workers can crash mid-task
* distributed systems are inherently unreliable

---

## Benefits

* safe retries
* consistent system state
* no duplicate data
* predictable execution
* easier debugging

---

## Trade-offs

* additional checks in every task
* more defensive coding
* slight performance overhead

---

## Consequences

The system:

* tolerates duplicate execution
* ensures correctness under failure
* avoids data corruption
* supports robust async processing

---

## Future Evolution

* introduce task deduplication keys
* add idempotency middleware
* track execution hashes
* implement distributed locks if needed

---

## Summary

Idempotency is mandatory for reliable async systems.

All tasks must be safe to execute multiple times without side effects.

---