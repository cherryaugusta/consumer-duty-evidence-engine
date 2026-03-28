# ADR 0007: Retry and Backoff Strategy

## Status

Accepted

---

## Context

The system relies on asynchronous processing with Celery.

Failures can occur due to:

- temporary network issues
- external API timeouts
- database locks
- transient service outages

Without a retry strategy:

- tasks fail permanently on temporary issues
- manual intervention is required
- pipeline reliability decreases

---

## Decision

The system implements a **standard retry and exponential backoff strategy** for all Celery tasks.

This ensures:

- transient failures are retried automatically
- retries are spaced to reduce system load
- repeated failures eventually stop

---

## Implementation

### Default Retry Configuration

All tasks must use:

- automatic retries
- exponential backoff
- limited retry attempts

---

### Example Task Configuration

Path:
`backend/apps/extraction/tasks.py`

```python
from celery import shared_task


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=60,
    retry_jitter=True,
    max_retries=5,
)
def extract_case_task(self, case_id):
    # task logic here
    pass
````

---

### Manual Retry (if needed)

```python id="y6t6xg"
try:
    # logic
except ExternalServiceError as e:
    raise self.retry(exc=e, countdown=10)
```

---

### Retry Behavior

* first retry: short delay
* subsequent retries: exponentially longer delays
* jitter: randomizes delay to avoid spikes

---

### When to Retry

Retry only for:

* network failures
* timeouts
* temporary external service errors

Do NOT retry for:

* validation errors
* invalid state transitions
* corrupted input data

---

### Failure Handling After Retries

If max retries exceeded:

* task fails permanently
* case transitions to FAILED
* audit event emitted

Example:

```python id="z3v3lq"
emit_audit_event(
    case,
    "case.extraction.failed",
    case.correlation_id,
    metadata={"reason": "max_retries_exceeded"},
)
```

---

### Logging Retries

```python id="2h0r9q"
logger.warning(
    "Retrying task",
    extra={
        "case_id": case.id,
        "correlation_id": case.correlation_id,
        "stage": "extraction",
        "retry_count": self.request.retries,
    },
)
```

---

## Benefits

* improved resilience to transient failures
* reduced manual intervention
* smoother system recovery
* better reliability under load

---

## Trade-offs

* increased execution time for failing tasks
* potential duplicate processing (handled via idempotency)
* more complex debugging for repeated failures

---

## Consequences

The system:

* automatically retries recoverable errors
* avoids immediate task failure
* limits retry attempts to prevent infinite loops
* integrates with idempotent task design

---

## Future Evolution

* dynamic retry policies per stage
* circuit breaker integration
* retry metrics and monitoring
* priority-based retry queues

---

## Summary

A consistent retry and backoff strategy ensures the system remains robust under transient failure conditions while preventing overload and infinite retries.

---