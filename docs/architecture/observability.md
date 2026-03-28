# Observability Architecture

## Purpose

Observability ensures that every case moving through the system can be:

- traced end-to-end
- debugged at any stage
- audited for compliance decisions
- monitored for failures and degraded behavior

This system is designed to make pipeline behavior transparent, not opaque.

---

## Observability Pillars

The system implements three core pillars:

1. structured logging
2. audit events
3. state visibility

These work together to provide full traceability.

---

## Correlation ID

Every case is assigned a `correlation_id` at creation.

This ID is propagated through:

- API requests
- Celery tasks
- logs
- audit events

### Example

```json
{
  "correlation_id": "case-1234-uuid",
  "case_id": "uuid",
  "stage": "parsing"
}
````

### Why it matters

* enables tracing a single case across all services
* critical for debugging async pipelines

---

## Structured Logging

All logs are JSON formatted.

### Required fields

* `timestamp`
* `level`
* `logger`
* `message`
* `case_id`
* `correlation_id`
* `stage`

### Example

```json
{
  "timestamp": "2026-03-28T08:00:00Z",
  "level": "INFO",
  "logger": "apps.parsing",
  "message": "Parsing started",
  "case_id": "uuid",
  "correlation_id": "uuid",
  "stage": "parsing"
}
```

---

## Logging in Django

Configured via:

* `config/settings/base.py`

Example:

```python
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "format": "%(message)s"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json"
        }
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO"
    }
}
```

---

## Logging in Celery

Celery workers emit logs using the same structured format.

Key requirement:

* include `case_id` and `correlation_id` in every task log

Example:

```python
logger.info(
    "Extraction completed",
    extra={
        "case_id": case.id,
        "correlation_id": case.correlation_id,
        "stage": "extraction"
    }
)
```

---

## Audit Events

Audit events provide a permanent, queryable record of system actions.

### Event Types

Each pipeline stage emits:

* `case.stage.started`
* `case.stage.completed`
* `case.stage.failed`

### Example

```json
{
  "event_type": "case.parsing.completed",
  "case_id": "uuid",
  "correlation_id": "uuid",
  "timestamp": "2026-03-28T08:01:00Z",
  "metadata": {
    "duration_ms": 1200
  }
}
```

---

## Audit Storage

Audit events are stored in the database.

Suggested model:

```python
class AuditEvent(models.Model):
    event_type = models.CharField(max_length=255)
    case = models.ForeignKey("Case", on_delete=models.CASCADE)
    correlation_id = models.UUIDField()
    timestamp = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(default=dict)
```

---

## State Visibility

The system exposes case state explicitly.

### Case Status Examples

* `INGESTION_PENDING`
* `PARSING`
* `PARSED`
* `EXTRACTED`
* `MAPPED`
* `ASSESSED`
* `NEEDS_REVIEW`
* `APPROVED`
* `FAILED`

### Why it matters

* supports UI progress tracking
* enables safe retries
* allows debugging without logs

---

## WebSocket Updates

Frontend receives real-time updates.

### Payload

```json
{
  "case_id": "uuid",
  "status": "extraction",
  "timestamp": "2026-03-28T08:02:00Z"
}
```

### Trigger points

* after each state transition
* after failures
* after finalization

---

## Error Tracking

Errors are captured with:

* structured logs
* audit events
* case status updates

### Failure Example

```json
{
  "event_type": "case.extraction.failed",
  "case_id": "uuid",
  "correlation_id": "uuid",
  "metadata": {
    "error": "schema validation failed"
  }
}
```

---

## Degraded Mode Observability

When external dependencies fail:

* system sets `degraded_mode_active = true`
* logs include degraded flag
* audit events include degraded context

### Example

```json
{
  "event_type": "case.assessment.completed",
  "metadata": {
    "degraded_mode": true
  }
}
```

---

## Metrics (Future Extension)

The system can expose metrics such as:

* task duration per stage
* failure rate per stage
* queue latency
* review rate vs approval rate

These can later be integrated with:

* Prometheus
* Grafana

---

## Local Debugging Workflow

### Step 1: Run services

```powershell
docker compose up -d db redis
```

### Step 2: Start backend

```powershell
cd backend
python manage.py runserver
```

### Step 3: Start Celery (Windows-safe)

```powershell
python -m celery -A config worker -l info -P solo
```

### Step 4: Observe logs

* Django logs → terminal
* Celery logs → terminal
* verify correlation_id consistency

---

## Debugging a Case

1. find `case_id`
2. search logs using `correlation_id`
3. check audit events in DB
4. inspect final state
5. replay if needed

---

## Design Principles

The observability design follows these principles:

* no silent failures
* every state change is visible
* every task is traceable
* logs are structured, not free text
* audit events are durable

---

## Why This Matters

This system is not just generating outputs.

It is:

* traceable
* debuggable
* auditable
* safe under failure

That is essential for any system making compliance-related decisions.

---