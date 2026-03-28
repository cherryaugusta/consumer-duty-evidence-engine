# Failure Modes

## Purpose

This document describes how the Consumer Duty Evidence Engine handles workflow failures, uncertainty, and degraded operating conditions.

The goal is not to hide failure. The goal is to surface failure safely, route it appropriately, and preserve auditability.

---

## Failure-Handling Principles

The system follows these rules:

- failures must be visible
- invalid structured output must not silently pass
- contradictory or weak evidence must route to review
- provider failures must activate degraded behavior rather than pretend success
- audit history must remain intact
- replay and retry must be controlled

---

## Primary Failure Categories

The main failure categories in this project are:

1. artifact parsing failure
2. extraction schema failure
3. provider failure
4. contradiction detection
5. missing required evidence
6. stale evidence
7. duplicate uploads
8. repeated task failure
9. invalid state transition

---

## 1. Artifact Parsing Failure

### Description

Parsing fails when an artifact cannot be read or transformed into canonical document sections.

### Examples

- unreadable file content
- unsupported format edge case
- filesystem read issue
- parser exception

### Expected behavior

- artifact parse status moves to `failed`
- case may move to `failed`
- failure is logged
- failure is auditable
- retry remains possible through controlled workflow paths

### Why it matters

Parsing is the first transformation stage. If parsing is wrong, downstream extraction and assessment become untrustworthy.

---

## 2. Extraction Schema Failure

### Description

Extraction fails when structured output does not satisfy the expected schema.

### Examples

- missing required fields
- invalid claim shape
- malformed structured output
- simulated schema failure case

### Expected behavior

- malformed output is rejected
- case routes to `needs_review`
- audit history captures the failure
- the system does not silently continue as if extraction succeeded

### Why it matters

This project is intentionally structured-output-first. Schema failure must be treated as a workflow event, not as a cosmetic issue.

---

## 3. Provider Failure

### Description

Provider failure means a provider-backed step cannot complete normally.

### Examples

- simulated provider outage
- model call failure
- timeout
- unavailable upstream dependency

### Expected behavior

- `degraded_mode_active` is set to `true`
- rules-only or fallback behavior is used where applicable
- case routes to review when safe completion is not possible
- recommendation output should remain conservative
- failure is visible in logs and audit history

### Why it matters

A workflow product must fail safely. It must not mask provider outages behind false certainty.

---

## 4. Contradictory Evidence

### Description

Contradictions occur when evidence sources conflict in a way that affects support assessment or recommendation confidence.

### Examples

- conflicting dates
- conflicting policy statements
- conflicting support-script language
- conflicting descriptions of customer impact

### Expected behavior

- contradiction flags are created
- support assessment can become `contradictory_support`
- case routes to `needs_review` or `escalated` depending on severity
- contradiction remains visible in exported audit material

### Why it matters

This is one of the strongest examples of why the project is a workflow system rather than a summarization tool.

---

## 5. Missing Required Evidence

### Description

The system may identify a claim but lack the required supporting source material.

### Examples

- fee complaint without disclosure support
- disclosure concern without matching disclosure artifact
- support issue without relevant supporting transcript
- incomplete case bundle

### Expected behavior

- support assessment becomes `missing_support`
- case routes to review
- recommendation may become `request_more_evidence`
- the system does not auto-approve based on incomplete support

### Why it matters

The correct response to insufficient evidence is controlled abstention or review, not overconfidence.

---

## 6. Stale Evidence

### Description

Evidence is stale when the available support is outdated relative to the claim or case timeline.

### Examples

- outdated script version
- old policy excerpt
- evidence date conflicts with current case period

### Expected behavior

- support assessment becomes `stale_support`
- case routes to review
- rationale should reflect the evidence-age concern

### Why it matters

Old evidence can look complete while still being inappropriate for the actual decision context.

---

## 7. Duplicate Uploads

### Description

Duplicate uploads occur when the same artifact is submitted more than once for the same case.

### Expected behavior

- duplicates are deduplicated by checksum
- storage should not multiply equivalent artifacts for the same case
- workflow should remain stable
- auditability should remain intact

### Why it matters

Duplicate documents are common in operational systems. Safe dedupe prevents noisy evidence graphs and misleading counts.

---

## 8. Repeated Task Failure

### Description

A task may continue failing even after retry attempts.

### Applies to

- parsing
- extraction
- mapping
- assessment
- recommendation

### Expected behavior

- retry policy is stage-specific
- after repeated failure, the case routes to either:
  - `failed`
  - `needs_review`
- behavior depends on stage and recoverability

### Why it matters

Repeated retries without clear failure handling create workflow ambiguity and poor operator trust.

---

## 9. Invalid State Transition

### Description

The state machine blocks illegal workflow jumps.

### Examples

- `new -> approved`
- `parsed -> assessed`
- `archived -> parsing`

### Expected behavior

- transition is rejected
- exception is raised
- invalid state is not persisted

### Why it matters

This prevents corruption of workflow history and keeps replay, retry, and review paths deterministic.

---

## Failure Routing Summary

The system should route failures like this:

| Failure type | Expected route |
| --- | --- |
| parsing failure | failed |
| extraction schema failure | needs_review |
| provider failure | degraded mode + needs_review |
| contradiction | needs_review or escalated |
| missing evidence | needs_review |
| stale evidence | needs_review |
| duplicate upload | dedupe, continue safely |
| repeated unrecoverable failure | failed or review |
| invalid transition | reject immediately |

---

## Degraded Mode Behavior

Degraded mode exists so the workflow can remain safe under provider problems.

### Expected degraded behavior

- continue using deterministic logic where possible
- do not present unsafe certainty
- surface degraded state explicitly
- preserve traceability
- route uncertain outputs to review

### Portfolio significance

Degraded mode is one of the most important credibility features in the project because it shows the system is designed for failure handling, not just happy-path demos.

---

## Visibility Requirements

Failures should be visible through multiple channels:

- JSON logs
- case status
- review status where relevant
- contradiction flags where relevant
- audit events
- exported audit packets
- demo cases and eval scenarios

A failure should never exist only as a hidden terminal exception.

---

## Replay and Retry

The project supports both retry and replay.

### Retry

Retry is used when rerunning the current failed stage is appropriate.

### Replay

Replay is used when rerunning the case from a chosen downstream point is appropriate while preserving audit history.

### Expected replay behavior

- preserve prior audit trail
- clear downstream derived objects from replay point onward
- rerun the relevant workflow stages
- keep final comparison observable

---

## Demo-Relevant Failure Cases

The seeded and eval data intentionally include failure-oriented scenarios such as:

- schema-failure simulation
- provider failure simulation
- contradictory evidence
- stale evidence
- duplicate upload
- strong date contradiction
- weak or missing support

These scenarios are important because they demonstrate the system’s safety behavior under uncertainty.

---

## Honest Scope

This project is a portfolio-grade simulation, not a production compliance platform.

Its failure-handling design is intended to demonstrate:

- explicit workflow control
- auditable fallback behavior
- review routing under uncertainty
- measurable degraded-mode handling
- replayable operational workflows

That is the correct scope claim for the repository.