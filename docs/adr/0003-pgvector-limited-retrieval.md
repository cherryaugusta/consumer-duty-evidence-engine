# ADR 0003: pgvector for Limited Retrieval

## Status

Accepted

## Context

The Consumer Duty Evidence Engine needs lightweight retrieval over parsed document sections to support:

- evidence linking
- policy/script lookup
- citation assistance
- future evaluation scenarios involving retrieval-backed matching

The project does not need a full standalone vector database or a large-scale retrieval platform.

It does need:

- local developer simplicity
- PostgreSQL compatibility
- support for document-section embeddings
- a credible retrieval story for portfolio purposes

## Decision

The project uses `pgvector` inside PostgreSQL for limited retrieval over `DocumentSection.embedding_vector`.

This keeps retrieval close to the source-of-truth database and avoids unnecessary infrastructure sprawl.

## Why pgvector

`pgvector` was chosen because it provides:

- direct integration with PostgreSQL
- Django compatibility through `pgvector.django`
- support for vector similarity search
- simple local setup with Docker
- a believable retrieval layer without adding a separate vector store

This is a good fit for a workflow product where retrieval is helpful but not the main product.

## Scope of Retrieval

Retrieval is intentionally limited.

It is used for:

- section-level evidence lookup
- supporting citation linkage
- policy/script similarity lookup
- future retrieval-assisted rule paths

It is not intended to be:

- a general semantic search platform
- a high-scale vector serving system
- a replacement for workflow state in PostgreSQL

## Model Location

The vector field is stored on:

- `backend/apps/artifacts/models.py`

Model:

- `DocumentSection`

Field:

- `embedding_vector`

This keeps retrieval attached directly to canonical parsed document sections.

## Database Support

The project enables the PostgreSQL `vector` extension.

Local Docker init path:

- `infra/db-init/001-enable-pgvector.sql`

The project also uses a vector index migration for document sections.

## Why Not a Separate Vector Database

A separate vector database was not chosen because:

- it would add unnecessary operational complexity
- the retrieval scope is narrow
- the project already relies on PostgreSQL as the primary store
- keeping retrieval close to document sections improves simplicity
- portfolio value comes more from workflow design than infrastructure sprawl

## Why Not No Retrieval At All

Pure rules-only operation remains an important baseline, but limited retrieval is still useful because it:

- improves evidence linking
- strengthens provenance demonstrations
- supports future retrieval-assisted evaluation scenarios
- gives a more credible AI workflow story

## Consequences

This decision means:

- PostgreSQL remains the single operational data platform
- embeddings are optional but structurally supported
- retrieval can be introduced incrementally without redesigning storage
- test environments must support the `vector` extension

## Operational Notes

The project already encountered the PostgreSQL test database issue for `VectorField`.

The working fix was to enable the extension in `template1`:

```powershell
docker compose exec db psql -U cdee -d template1 -c "CREATE EXTENSION IF NOT EXISTS vector;"
````

This is important for integration tests that create test databases.

## Limitations

This approach is intentionally limited:

* retrieval quality depends on embedding generation quality
* scale is bounded by PostgreSQL usage patterns
* this is not intended as a production-grade standalone vector search platform

These limitations are acceptable because the project is a workflow product first.

## Summary

`pgvector` is the right choice for this project because it adds credible, lightweight retrieval to document sections while keeping the architecture simple, local-friendly, and tightly aligned with PostgreSQL as the primary store.