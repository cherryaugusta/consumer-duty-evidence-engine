# ADR 0001: Monolith with Async Workers

## Status

Accepted

---

## Context

The Consumer Duty Evidence Engine is designed as a workflow-oriented system that processes uploaded artifacts through multiple stages:

- parsing
- extraction
- mapping
- assessment
- recommendation

These stages are:

- stateful
- sequential
- auditable
- occasionally long-running

The system must also support:

- deterministic state transitions
- replay and retry
- auditability
- degraded mode handling
- local development on Windows

---

## Decision

The system is implemented as:

- a Django monolith for core application logic
- Celery workers for asynchronous task execution
- Redis as broker and result backend

This results in a **monolith + async worker architecture**.

---

## Architecture Components

### Web Application

Path:
`backend/`

Responsibilities:

- API endpoints
- data models
- state machine
- orchestration logic
- audit event creation
- WebSocket handling (via ASGI)

---

### Async Workers

Command used:

```powershell
python -m celery -A config worker -l info -P solo
````

Responsibilities:

* parsing tasks
* extraction tasks
* mapping tasks
* assessment tasks
* recommendation tasks

Windows constraint:

* uses `-P solo` pool (no prefork)

---

### Broker and Backend

Started via:

```powershell
docker compose up -d db redis
```

Configuration:

* broker: `redis://localhost:6379/1`
* result backend: `redis://localhost:6379/2`

---

## Why Not Microservices

A microservices architecture was not chosen because:

* the domain model is tightly coupled (case, artifacts, assessments)
* orchestration logic depends on shared state
* debugging distributed workflows adds complexity
* this project prioritizes clarity and traceability over horizontal scaling
* local development would become significantly more complex

---

## Why Async Workers Are Used

Celery is used because:

* parsing and extraction can be slow
* tasks should not block API requests
* retry and failure handling must be controlled
* pipeline stages can be decoupled but still coordinated

---

## Benefits

* simple deployment model
* shared data model across all stages
* easier debugging
* strong alignment with state machine design
* supports replay and audit workflows
* works reliably on Windows with `solo` pool

---

## Trade-offs

* limited horizontal scalability compared to microservices
* single codebase requires discipline to maintain modularity
* Celery on Windows requires non-default configuration (`-P solo`)
* not designed for high-throughput distributed workloads

---

## Consequences

The system:

* prioritizes correctness and traceability over raw scale
* keeps orchestration logic close to the data model
* uses Celery as an execution layer rather than a separate service boundary
* remains easy to run locally for demonstration and evaluation

---

## Future Evolution

If needed, this architecture could evolve toward:

* containerized deployment (separate web + worker containers)
* multiple worker queues
* external monitoring (Prometheus, Grafana)
* eventual service decomposition

However, this is intentionally deferred.

---

## Summary

The monolith + async worker approach is the best fit for:

* a workflow-driven system
* strong auditability requirements
* replayable processing
* controlled failure handling
* local-first development

It keeps the system understandable while still supporting asynchronous execution.

---


