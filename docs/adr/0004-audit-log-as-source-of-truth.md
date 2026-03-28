# ADR 0004: Audit Log as Source of Truth

## Status

Accepted

---

## Context

The system processes cases asynchronously across multiple stages.

Challenges:

- debugging failures across distributed workers
- reconstructing execution history
- ensuring regulatory traceability
- understanding partial or failed processing

Logs alone are insufficient because:

- they are not queryable in a structured way
- they are not guaranteed to be complete
- they are not tied strongly to domain entities

---

## Decision

The system adopts **Audit Events as the source of truth for execution history**.

This means:

- every significant action emits an audit event
- audit events are stored in the database
- audit events are queryable per case
- audit events are immutable

---

## Implementation

### Model

Path:
`backend/apps/audit/models.py`

```python
from django.db import models


class AuditEvent(models.Model):
    event_type = models.CharField(max_length=255)
    case = models.ForeignKey("cases.Case", on_delete=models.CASCADE)
    correlation_id = models.UUIDField()
    timestamp = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(default=dict)

    def __str__(self):
        return f"{self.event_type} - {self.case_id}"
````

---

### Migration

Run:

```powershell
cd backend
python manage.py makemigrations audit
python manage.py migrate
```

---

### Event Types

Convention:

```
case.<stage>.<status>
```

Examples:

* case.parsing.started
* case.parsing.completed
* case.parsing.failed
* case.extraction.completed
* case.assessment.failed

---

### Emit Audit Event

Path:
`backend/apps/audit/services.py`

```python
from apps.audit.models import AuditEvent


def emit_audit_event(case, event_type, correlation_id, metadata=None):
    AuditEvent.objects.create(
        case=case,
        event_type=event_type,
        correlation_id=correlation_id,
        metadata=metadata or {},
    )
```

---

### Usage in Tasks

Example:

Path:
`backend/apps/parsing/tasks.py`

```python
from apps.audit.services import emit_audit_event

emit_audit_event(
    case=case,
    event_type="case.parsing.started",
    correlation_id=case.correlation_id,
)
```

---

### Failure Example

```python
try:
    # parsing logic
    emit_audit_event(case, "case.parsing.completed", case.correlation_id)
except Exception as e:
    emit_audit_event(
        case,
        "case.parsing.failed",
        case.correlation_id,
        metadata={"error": str(e)},
    )
    raise
```

---

## Why Not Logs Only

Logs were rejected as a primary source because:

* not queryable per case
* can be lost or rotated
* lack strict structure
* difficult to aggregate

---

## Benefits

* complete execution trace per case
* queryable for debugging and analytics
* supports regulatory audit requirements
* enables replay and diagnostics
* aligns with state machine transitions

---

## Trade-offs

* additional database writes
* storage growth over time
* requires discipline in emitting events

---

## Consequences

The system:

* records every stage transition
* allows full reconstruction of case history
* decouples observability from logs
* enables future analytics and monitoring

---

## Future Evolution

* add indexing on event_type and case
* introduce retention policies
* stream events to external systems
* integrate with monitoring tools

---

## Summary

Audit events provide a reliable, structured, and queryable history of system behavior.

They are the foundation for observability, debugging, and compliance.

---