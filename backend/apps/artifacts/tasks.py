from celery import shared_task

from apps.artifacts.models import ParseStatus, SourceArtifact
from apps.cases.models import ReviewCase
from apps.cases.services import transition_case
from apps.core.constants import CaseStatus


@shared_task
def queue_case_parsing_if_ready(case_id: str):
    from apps.parsing.tasks import parse_artifact_task

    case = ReviewCase.objects.get(pk=case_id)
    artifacts = SourceArtifact.objects.filter(case=case).order_by("uploaded_at")

    queued = 0
    for artifact in artifacts:
        if artifact.parse_status == ParseStatus.PENDING:
            parse_artifact_task.delay(str(artifact.id))
            queued += 1

    return {"case_id": case_id, "queued_artifacts": queued}


@shared_task
def finalize_case_parsing(case_id: str):
    case = ReviewCase.objects.get(pk=case_id)
    artifacts = SourceArtifact.objects.filter(case=case)

    if not artifacts.exists():
        return {"case_id": case_id, "status": "no_artifacts"}

    if artifacts.filter(parse_status=ParseStatus.FAILED).exists():
        transition_case(
            case=case,
            new_status=CaseStatus.FAILED,
            correlation_id=case.correlation_id,
            message="One or more artifacts failed to parse",
        )
        return {"case_id": case_id, "status": "failed"}

    if artifacts.filter(parse_status__in=[ParseStatus.PENDING, ParseStatus.RUNNING]).exists():
        return {"case_id": case_id, "status": "waiting"}

    transition_case(
        case=case,
        new_status=CaseStatus.PARSED,
        correlation_id=case.correlation_id,
        message="All artifacts parsed",
    )
    return {"case_id": case_id, "status": "parsed"}
