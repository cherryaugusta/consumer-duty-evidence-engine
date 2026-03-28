# ADR 0002: Structured Output First

## Status

Accepted

---

## Context

The Consumer Duty Evidence Engine processes unstructured artifacts (documents, transcripts, policies) and converts them into structured data used for:

- obligation mapping
- support assessment
- recommendation generation
- audit export

A key design decision is how to handle extraction:

- free-text summaries (loose, flexible)
- structured outputs (strict schema, validated)

The system must support:

- deterministic downstream processing
- auditability
- replay and regression testing
- failure visibility
- safe handling of ambiguity

---

## Decision

The system adopts a **structured output first** approach.

This means:

- extraction produces schema-validated structured data
- downstream stages depend on structured fields, not free text
- invalid outputs are rejected rather than tolerated
- ambiguity is handled through routing (review), not hidden in prose

---

## Implementation

### Extraction Layer

Path:
`backend/apps/extraction/`

Responsibilities:

- convert parsed text into structured claims
- validate against schema
- attach metadata such as confidence and source references

---

### Schema Definition

Path:
`backend/apps/extraction/schema.py`

Defines:

- claim structure
- required fields
- allowed values

All extracted outputs must conform to this schema.

---

### Validation

Validation occurs during extraction:

- invalid structure → failure or review routing
- missing required fields → rejection
- malformed data → not passed downstream

---

### Downstream Dependency

All downstream components rely on structured data:

- mapping → uses structured claims
- assessment → uses structured support signals
- recommendation → uses structured outcomes and support status
- audit → stores structured payloads

No stage depends on raw free-text interpretation alone.

---

## Why Not Free-Text First

Free-text-first systems were not chosen because:

- outputs are inconsistent
- difficult to validate automatically
- hard to compare in evals
- ambiguous for audit purposes
- prone to hallucination-like behavior
- difficult to map deterministically to outcome codes

---

## Benefits

- deterministic processing
- schema validation enforces discipline
- easier regression testing
- measurable evaluation (precision, recall, mapping accuracy)
- clearer audit trail
- easier replay and comparison
- safer handling of ambiguous cases

---

## Trade-offs

- higher implementation effort
- schema design requires iteration
- strict validation can increase review routing
- less flexibility than free-text generation

---

## Consequences

The system:

- treats extraction failure as a workflow event
- routes uncertainty to `needs_review`
- avoids silent acceptance of malformed data
- prioritizes correctness over fluency
- enables eval-driven development

---

## Example Flow

1. artifact parsed into text
2. extraction produces structured claims
3. schema validation applied
4. if valid → continue pipeline
5. if invalid → route to review or fail

---

## Relationship to Evaluation

The eval system depends on structured output:

- claim precision and recall
- mapping accuracy
- support status accuracy
- citation validation

Without structured outputs, these metrics would not be reliable.

---

## Future Evolution

Possible improvements:

- richer schema (additional claim attributes)
- confidence calibration
- hybrid structured + explanation outputs
- improved validation rules

---

## Summary

Structured output first is a foundational decision that enables:

- auditability
- deterministic workflows
- safe failure handling
- measurable system performance

It is central to the system’s design as a workflow engine rather than a text-generation demo.