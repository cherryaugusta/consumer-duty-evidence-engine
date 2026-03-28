# ADR 0002: PostgreSQL as Primary Store

## Status

Accepted

## Context

The Consumer Duty Evidence Engine needs a durable primary data store for:

- cases
- uploaded artifacts
- parsed document sections
- extracted claims
- evidence links
- support assessments
- contradiction flags
- recommendations
- review tasks
- reviewer actions
- audit events
- eval runs

The system requires:

- strong relational integrity
- transaction support
- queryable audit history
- support for JSON fields
- compatibility with Django ORM
- support for pgvector-based retrieval experiments

## Decision

PostgreSQL is the primary system of record.

It stores all workflow-critical entities and remains the authoritative source of truth for case lifecycle data.

Redis is used only for infrastructure concerns such as:

- Celery broker/backend
- caching
- Channels layer

Redis is not used as the source of truth for workflow state.

## Why PostgreSQL

PostgreSQL was chosen because it provides:

- mature relational modeling
- reliable transactions
- strong indexing support
- JSON field support
- compatibility with Django
- compatibility with pgvector
- clear local development story with Docker

This project is workflow-heavy and entity-rich. A relational database is the correct fit.

## What PostgreSQL Stores

PostgreSQL stores the durable operational records for:

- `cases.ReviewCase`
- `artifacts.SourceArtifact`
- `artifacts.DocumentSection`
- `extraction.Claim`
- `obligations.ConsumerDutyOutcome`
- `obligations.EvidenceLink`
- `assessments.SupportAssessment`
- `assessments.ContradictionFlag`
- `recommendations.PromptVersion`
- `recommendations.Recommendation`
- `reviews.ReviewTask`
- `reviews.ReviewerAction`
- `audits.AuditEvent`
- `observability.ModelExecutionLog`
- `evals.EvalCase`
- `evals.EvalRun`

## Why Not Redis as Primary Store

Redis was not chosen as the primary store because:

- workflow history must be durable
- relational joins matter across the domain
- auditability requires durable persistence
- retries and replay require stable source-of-truth records
- Redis is better suited to transient infrastructure roles

## Why Not a Document Store

A document database was not chosen because:

- the project has rich relational links across cases, artifacts, sections, claims, assessments, reviews, and audits
- integrity constraints matter
- unique constraints matter
- indexed querying across entities matters more than document flexibility

## Consequences

This decision means:

- PostgreSQL is required for local development and CI
- migrations are part of normal development
- workflow debugging can rely on durable DB state
- replay, export, and audit features can query a consistent source of truth

## Operational Notes

Local project defaults use:

- host: `localhost`
- port: `55432`
- database: `cdee`
- user: `cdee`

For fresh PowerShell windows, the project has already used:

```powershell
$env:POSTGRES_HOST="localhost"
$env:POSTGRES_PORT="55432"
$env:POSTGRES_DB="cdee"
$env:POSTGRES_USER="cdee"
$env:POSTGRES_PASSWORD="cdee"
$env:DJANGO_SETTINGS_MODULE="config.settings.local"
````

## Future Evolution

This decision still allows future additions such as:

* read replicas
* partitioning
* additional indexes
* more advanced pgvector usage

But PostgreSQL remains the core system of record.

## Summary

PostgreSQL is the right primary store for this project because it supports durable workflow state, relational integrity, auditability, and Django-native development while still allowing pgvector-backed retrieval where useful.