# ADR 0004: Structured Output First

## Status

Accepted

## Context

The Consumer Duty Evidence Engine relies on multiple AI-assisted stages:

- parsing (future OCR/LLM augmentation)
- extraction (claims)
- obligation mapping
- assessment
- recommendation generation

Unstructured outputs from language models introduce risks:

- inconsistent formats
- difficult validation
- brittle downstream processing
- lack of auditability
- reduced determinism

Given regulatory alignment requirements, outputs must be:

- auditable
- reproducible
- schema-valid
- machine-consumable

## Decision

All AI-assisted components must produce **structured outputs first**, using explicit schemas.

Free-form text is treated as a secondary artifact, not the primary output.

## Principles

### 1. Schema Before Prompting

Every AI task must define a strict schema:

- JSON structure
- required fields
- field types
- validation rules

The schema is the contract.

### 2. Deterministic Consumption

Downstream services must:

- consume structured data only
- avoid parsing raw text
- rely on validated fields

This ensures stable pipelines across all workflow stages.

### 3. Validation Layer

All structured outputs must be validated:

- schema validation (Pydantic or equivalent)
- field constraints
- type enforcement

Invalid outputs must be rejected or retried.

### 4. Text as Supporting Evidence

Natural language output is allowed, but:

- stored as metadata or explanation
- never used as the primary input to downstream tasks

### 5. Audit Compatibility

Structured outputs enable:

- precise audit logs
- replayability
- deterministic debugging
- regulatory traceability

## Implementation Approach

Structured outputs will be introduced progressively:

- current deterministic services already produce structured data
- future LLM integrations will use strict output schemas
- services will return typed objects instead of raw text blobs

## Example

Instead of:

```text
"The claim appears misleading because fees are not clearly disclosed."
````

The system produces:

```json
{
  "claim_id": "uuid",
  "issue_type": "misleading_information",
  "confidence": 0.87,
  "explanation": "Fees are mentioned but not clearly disclosed upfront"
}
```

## Why This Matters

This decision is critical for:

* regulatory defensibility
* system reliability
* engineering scalability
* testability of AI-assisted components

Without structured outputs, the system becomes:

* fragile
* opaque
* difficult to validate

## Alternatives Considered

### Free-form LLM Output

Rejected because:

* inconsistent
* hard to validate
* unsuitable for regulated workflows

### Post-hoc Parsing

Rejected because:

* brittle
* error-prone
* increases system complexity

## Consequences

* additional upfront schema design effort
* stricter service contracts
* improved long-term reliability
* easier debugging and audit tracing

## Summary

Structured output is mandatory across all AI-assisted stages to ensure the system remains deterministic, auditable, and suitable for regulatory-aligned workflows.