# System Overview

## Purpose

The Consumer Duty Evidence Engine is a portfolio-grade simulation of an AI-assisted evidence review workflow inspired by FCA Consumer Duty expectations.

The system is designed to demonstrate how AI can be integrated into a governed, auditable workflow where outputs must be structured, reviewable, and safe under uncertainty.

It is not a chatbot. It is a workflow system.

---

## High-Level Architecture

```mermaid
flowchart LR
    UI[React UI] --> API[Django DRF API]
    API --> DB[(PostgreSQL)]
    API --> REDIS[(Redis)]
    API --> WS[Channels / WebSockets]
    API --> CELERY[Celery Worker]

    CELERY --> DB
    CELERY --> REDIS

    API --> AUDIT[Audit Events]
    API --> EVALS[Eval Runner]
````

---

## Core Components

### 1. Django + DRF (Backend API)

Responsible for:

* case lifecycle management
* artifact upload and persistence
* orchestration of async workflows
* state machine enforcement
* audit event recording
* API exposure for frontend and eval runner

Key properties:

* monolith architecture for simplicity and traceability
* strict state transitions
* observable and auditable actions

---

### 2. PostgreSQL (Primary Data Store)

Stores:

* cases
* artifacts and document sections
* extracted claims
* evidence links
* support assessments
* contradiction flags
* recommendations
* review tasks and actions
* audit events
* eval runs and metrics

Key properties:

* single source of truth
* relational integrity across workflow stages
* pgvector enabled for limited retrieval use

---

### 3. Redis (Infrastructure Layer)

Used for:

* Celery broker and result backend
* Django cache
* Channels WebSocket layer

Key properties:

* low-latency messaging between services
* lightweight coordination for async tasks

---

### 4. Celery Worker (Async Processing)

Responsible for:

* parsing artifacts into document sections
* extracting structured claims
* mapping claims to outcome areas
* assessing support sufficiency
* generating recommendations

Task chain:

1. parse_artifact_task
2. extract_case_task
3. map_case_task
4. assess_case_task
5. recommend_case_task

Key properties:

* retry-aware
* failure-aware
* deterministic fallback paths

---

### 5. Channels / WebSockets

Provides:

* real-time case status updates
* live workflow progression visibility

Example events:

* parsing started
* extraction completed
* assessment flagged for review
* recommendation generated

---

### 6. React Frontend (Operator UI)

Provides:

* cases dashboard
* case detail with evidence and assessments
* review queue and analyst actions
* metrics and eval dashboards

Key properties:

* operator-focused, not chat-based
* structured presentation of evidence and outcomes
* designed for screenshot credibility

---

### 7. Eval Harness

Located under:

* `infra/scripts/run_eval_suite.py`
* `evals/`

Responsibilities:

* load synthetic eval datasets
* execute real backend pipeline
* compare outputs against ground truth
* generate regression report

Key properties:

* measures system behavior, not just model output
* supports iteration without manual inspection

---

### 8. Audit System

Every significant action generates an audit event:

* case state transitions
* task execution stages
* review actions
* replay and retry operations

Key properties:

* full traceability
* correlation ID propagation
* timeline reconstruction

---

## End-to-End Workflow

1. Case is created → `INGESTION_PENDING`
2. Artifacts are uploaded and stored
3. Parsing tasks generate document sections
4. Extraction produces structured claims
5. Mapping links claims to outcome areas
6. Assessment evaluates evidence sufficiency
7. Recommendation generates structured decision
8. Case is routed to:

   * APPROVED
   * NEEDS_REVIEW
   * ESCALATED

All transitions are:

* state-machine validated
* audited
* broadcast via WebSocket

---

## Design Principles

### 1. Structured Outputs First

All AI-like steps produce schema-validated outputs. Invalid schema routes to review.

### 2. Deterministic Fallback

Rules-based paths ensure system behavior remains safe under:

* model failure
* schema failure
* low confidence

### 3. Human-in-the-Loop

Uncertain cases are routed to analysts with:

* clear reason codes
* full evidence context
* override capabilities

### 4. Auditability

Every decision is:

* recorded
* attributable
* replayable

### 5. Evaluation-Driven Development

System behavior is measured through:

* synthetic datasets
* regression reports
* scenario-based testing

---

## Why This Architecture

This project uses a Django monolith with async workers because:

* simplifies coordination across workflow stages
* keeps data model and orchestration tightly aligned
* avoids premature microservice complexity
* enables strong transactional guarantees
* supports rapid iteration for portfolio delivery

Async workers are added to:

* handle long-running tasks
* simulate real production workflows
* decouple ingestion from processing

---

## What This System Demonstrates

* AI integrated into a governed workflow, not a wrapper
* stateful, observable, auditable processing pipelines
* safe handling of uncertainty through fallback and review
* evidence-linked reasoning instead of free-form output
* measurable system performance via eval harness

---