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