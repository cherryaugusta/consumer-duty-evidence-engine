# ADR 0005: State Machine Enforced Workflow

## Status

Accepted

## Context

The Consumer Duty Evidence Engine processes cases through a multi-stage pipeline:

- artifact ingestion
- parsing
- extraction
- obligation mapping
- assessment
- recommendation
- review

Without strict control, workflow systems risk:

- invalid state transitions
- skipped stages
- inconsistent data
- difficult debugging
- non-reproducible outcomes

Given regulatory alignment requirements, the system must ensure:

- deterministic progression
- controlled transitions
- clear lifecycle visibility
- auditability of state changes

## Decision

The workflow is enforced using an explicit **state machine** defined on the `ReviewCase` model.

All state transitions must:

- be explicit
- follow allowed paths
- be validated before execution

## Case Lifecycle States

The system uses defined states (via `CaseStatus`):

- CREATED
- PARSING
- PARSED
- EXTRACTED
- MAPPED
- ASSESSED
- NEEDS_REVIEW
- ESCALATED
- APPROVED

These states represent the canonical lifecycle of a case.

## Transition Rules

Transitions must follow a valid sequence:

- CREATED → PARSING
- PARSING → PARSED
- PARSED → EXTRACTED
- EXTRACTED → MAPPED
- MAPPED → ASSESSED
- ASSESSED → NEEDS_REVIEW / APPROVED / ESCALATED

Invalid transitions are not allowed.

## Enforcement Strategy

### 1. Application-Level Enforcement

State changes are controlled in services and tasks:

- tasks update state only when their stage completes
- services ensure correct ordering
- invalid transitions raise errors

### 2. Task-Oriented Progression

Each Celery task corresponds to a stage:

- `parse_artifact_task`
- `extract_case_task`
- `map_case_task`
- `assess_case_task`
- `recommend_case_task`

Each task:

- assumes a valid prior state
- moves the case forward

### 3. No Implicit State Changes

State must never change implicitly:

- no hidden transitions
- no side effects from unrelated operations

### 4. Audit Integration

Every transition is recorded via audit events:

- state change events
- stage start/completion
- failures

This ensures full traceability.

## Why a State Machine

A state machine provides:

- deterministic workflows
- easier debugging
- clearer system behavior
- enforceable invariants
- regulatory audit alignment

## Alternatives Considered

### Implicit Workflow

Rejected because:

- transitions become unpredictable
- harder to trace and debug
- weak auditability

### Event-Only Workflow (No State)

Rejected because:

- difficult to determine current system state
- requires reconstructing from event streams
- increases operational complexity

## Consequences

- stricter workflow control
- additional validation logic
- clearer system boundaries
- improved reliability and traceability

## Future Enhancements

- explicit transition validation helpers
- state transition guards
- admin tooling for inspecting state flows

## Summary

The system enforces a state machine on case processing to ensure deterministic, auditable, and controlled workflow execution across all stages.