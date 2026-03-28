from apps.audits.models import AuditEvent


def emit_audit_event(
    *,
    case,
    event_type: str,
    correlation_id: str,
    actor_type: str = "system",
    actor_id: str | None = None,
    payload: dict | None = None,
) -> AuditEvent:
    return AuditEvent.objects.create(
        case=case,
        event_type=event_type,
        actor_type=actor_type,
        actor_id=actor_id,
        correlation_id=correlation_id,
        payload=payload or {},
    )


def create_audit_event(
    case,
    event_type: str,
    correlation_id: str,
    actor_type: str = "system",
    actor_id: str | None = None,
    payload: dict | None = None,
) -> AuditEvent:
    return emit_audit_event(
        case=case,
        event_type=event_type,
        correlation_id=correlation_id,
        actor_type=actor_type,
        actor_id=actor_id,
        payload=payload,
    )
