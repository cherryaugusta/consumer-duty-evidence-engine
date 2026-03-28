# State Machine Design

## Purpose

The case state machine enforces controlled progression through the evidence review workflow.

It ensures:
- no invalid transitions
- consistent lifecycle behavior
- predictable routing under failure or uncertainty
- auditability of all state changes

---

## Case Status Lifecycle

```mermaid
stateDiagram-v2
    [*] --> NEW

    NEW --> INGESTION_PENDING
    NEW --> FAILED

    INGESTION_PENDING --> PARSING
    INGESTION_PENDING --> FAILED

    PARSING --> PARSED
    PARSING --> FAILED

    PARSED --> EXTRACTION_PENDING
    PARSED --> FAILED

    EXTRACTION_PENDING --> EXTRACTED
    EXTRACTION_PENDING --> NEEDS_REVIEW
    EXTRACTION_PENDING --> FAILED

    EXTRACTED --> MAPPING_PENDING
    EXTRACTED --> FAILED

    MAPPING_PENDING --> MAPPED
    MAPPING_PENDING --> FAILED

    MAPPED --> ASSESSMENT_PENDING
    MAPPED --> FAILED

    ASSESSMENT_PENDING --> ASSESSED
    ASSESSMENT_PENDING --> NEEDS_REVIEW
    ASSESSMENT_PENDING --> FAILED

    ASSESSED --> APPROVED
    ASSESSED --> NEEDS_REVIEW
    ASSESSED --> ESCALATED

    NEEDS_REVIEW --> APPROVED
    NEEDS_REVIEW --> ESCALATED
    NEEDS_REVIEW --> ARCHIVED

    APPROVED --> ARCHIVED
    ESCALATED --> ARCHIVED

    FAILED --> INGESTION_PENDING
    FAILED --> PARSING

    ARCHIVED --> [*]
````

---

## Review Status Lifecycle

Separate from case status, review tasks follow their own lifecycle.

```mermaid
stateDiagram-v2
    [*] --> UNASSIGNED

    UNASSIGNED --> ASSIGNED
    ASSIGNED --> IN_REVIEW

    IN_REVIEW --> APPROVED
    IN_REVIEW --> OVERRIDDEN
    IN_REVIEW --> ESCALATED

    APPROVED --> CLOSED
    OVERRIDDEN --> CLOSED
    ESCALATED --> CLOSED
```

---

## Transition Enforcement

All transitions are validated using:

* `apps.cases.state_machine.assert_transition`

Invalid transitions raise an exception and are not persisted.

This guarantees:

* no skipping stages
* no illegal recovery paths
* consistent workflow behavior across API, tasks, and scripts

---

## Key Transition Rules

### 1. Linear Processing Stages

Core pipeline must follow strict order:

```
INGESTION_PENDING → PARSING → PARSED → EXTRACTION → MAPPING → ASSESSMENT → RECOMMENDATION
```

No stage can be skipped.

---

### 2. Failure Handling

Any stage may transition to:

* `FAILED`

Recovery paths:

* `FAILED → INGESTION_PENDING`
* `FAILED → PARSING`

This allows controlled retries without corrupting downstream state.

---

### 3. Review Routing

A case enters `NEEDS_REVIEW` when:

* schema validation fails
* confidence is low
* contradictions are detected
* required evidence is missing
* degraded mode is active

From `NEEDS_REVIEW`, only:

* APPROVED
* ESCALATED
* ARCHIVED

are allowed.

---

### 4. Final States

Terminal states:

* `ARCHIVED`

Once archived:

* no further transitions are allowed

---

## State vs Review Status

Two independent axes:

| Dimension     | Purpose              |
| ------------- | -------------------- |
| Case Status   | pipeline progression |
| Review Status | human workflow state |

Examples:

* Case can be `NEEDS_REVIEW` with review status `UNASSIGNED`
* Case can be `APPROVED` while review task is `CLOSED`

---

## Audit Integration

Every transition generates an audit event:

* event type: `case.status_changed`
* includes:

  * previous status
  * new status
  * correlation_id
  * timestamp

This enables:

* full timeline reconstruction
* debugging of workflow behavior
* replay traceability

---

## WebSocket Integration

Each transition triggers a WebSocket event:

```json
{
  "case_id": "<uuid>",
  "status": "assessment_pending",
  "review_status": "unassigned",
  "timestamp": "<iso8601>",
  "degraded_mode_active": false
}
```

This supports:

* real-time UI updates
* operational observability

---

## Why This Matters

The state machine is critical because it:

* prevents silent workflow corruption
* enforces disciplined AI usage
* guarantees safe fallback behavior
* enables deterministic replay
* provides strong portfolio signal of system design maturity

---