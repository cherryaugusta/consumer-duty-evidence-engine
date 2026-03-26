from __future__ import annotations

from typing import Any

from apps.audits.models import ActorType, AuditEvent
from apps.cases.models import ReviewCase


def create_audit_event(
    *,
    case: ReviewCase,
    event_type: str,
    actor_type: str = ActorType.SYSTEM,
    actor_id: str | None = None,
    correlation_id: str | None = None,
    payload: dict[str, Any] | None = None,
) -> AuditEvent:
    """
    Central helper for writing audit events.

    This keeps event creation consistent across workflow stages and review actions.
    """
    return AuditEvent.objects.create(
        case=case,
        event_type=event_type,
        actor_type=actor_type,
        actor_id=actor_id,
        correlation_id=correlation_id or case.correlation_id,
        payload=payload or {},
    )
