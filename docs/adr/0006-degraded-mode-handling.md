# ADR 0006: Degraded Mode Handling

## Status

Accepted

---

## Context

The system depends on external services such as:

- LLM providers
- document parsing tools
- third-party APIs

These dependencies may:

- fail temporarily
- return partial responses
- timeout under load
- become unavailable

Without a strategy, failures would:

- block the entire pipeline
- cause cascading failures
- reduce system reliability

---

## Decision

The system implements a **degraded mode** strategy.

This means:

- the pipeline continues operating when dependencies fail
- partial results are allowed
- degraded executions are explicitly marked
- audit and logs capture degraded context

---

## Implementation

### Case Field

Path:
`backend/apps/cases/models.py`

```python
degraded_mode_active = models.BooleanField(default=False)
````

---

### Migration

Run:

```powershell
cd backend
python manage.py makemigrations cases
python manage.py migrate
```

---

### Helper Function

Path:
`backend/apps/core/degraded.py`

```python
def activate_degraded_mode(case):
    case.degraded_mode_active = True
    case.save(update_fields=["degraded_mode_active"])
```

---

### Example Usage in Task

Path:
`backend/apps/extraction/tasks.py`

```python
from apps.core.degraded import activate_degraded_mode

try:
    # normal extraction logic
except ExternalServiceError:
    activate_degraded_mode(case)

    # fallback logic (minimal extraction)
```

---

### Logging

```python
logger.warning(
    "Degraded mode activated",
    extra={
        "case_id": case.id,
        "correlation_id": case.correlation_id,
        "stage": "extraction",
        "degraded_mode": True,
    },
)
```

---

### Audit Event

```python
emit_audit_event(
    case,
    "case.extraction.completed",
    case.correlation_id,
    metadata={"degraded_mode": True},
)
```

---

### WebSocket Payload

```json
{
  "case_id": "uuid",
  "status": "extracted",
  "degraded_mode": true
}
```

---

## Fallback Strategies

Examples:

* use cached responses
* reduce model complexity
* skip optional enrichment
* return partial structured output

---

## Failure vs Degraded Mode

| Condition             | Behavior      |
| --------------------- | ------------- |
| recoverable failure   | degraded mode |
| unrecoverable failure | FAILED state  |

---

## Benefits

* pipeline continues operating
* improved system resilience
* better user experience
* avoids full pipeline blockage

---

## Trade-offs

* reduced output quality
* additional implementation complexity
* requires clear signaling to users

---

## Consequences

The system:

* tolerates external instability
* produces best-effort outputs
* explicitly marks degraded results
* maintains observability

---

## Future Evolution

* graded degradation levels
* automatic retry after degraded runs
* smarter fallback selection
* dependency health monitoring

---

## Summary

Degraded mode ensures the system remains functional under partial failure conditions while maintaining transparency and traceability.

---