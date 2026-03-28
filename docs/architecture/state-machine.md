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