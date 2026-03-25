from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.utils.timezone import now

from apps.audits.services import create_audit_event
from apps.cases.state_machine import assert_transition


def broadcast_case_status(case, message: str):
    channel_layer = get_channel_layer()
    payload = {
        "case_id": str(case.id),
        "status": case.status,
        "review_status": case.review_status,
        "timestamp": now().isoformat(),
        "degraded_mode_active": case.degraded_mode_active,
        "message": message,
    }
    async_to_sync(channel_layer.group_send)(
        f"case_{case.id}",
        {
            "type": "case_status",
            "payload": payload,
        },
    )


def transition_case(
    *,
    case,
    new_status: str,
    correlation_id: str,
    actor_type: str = "system",
    actor_id: str | None = None,
    message: str = "",
    payload: dict | None = None,
):
    old_status = case.status
    assert_transition(old_status, new_status)
    case.status = new_status
    case.save(update_fields=["status", "updated_at"])

    create_audit_event(
        case=case,
        event_type="case.status_changed",
        actor_type=actor_type,
        actor_id=actor_id,
        correlation_id=correlation_id,
        payload={
            "old_status": old_status,
            "new_status": new_status,
            "message": message,
            **(payload or {}),
        },
    )

    broadcast_case_status(case, message or f"Case moved to {new_status}")
    return case
