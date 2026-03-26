from celery import shared_task

from apps.cases.models import ReviewCase
from apps.extraction.services import extract_claims_for_case
from apps.obligations.tasks import map_case_task


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=5, max_retries=2)
def extract_case_task(self, case_id: str):
    case = ReviewCase.objects.get(pk=case_id)

    claims = extract_claims_for_case(case)

    map_case_task.delay(str(case.id))

    return {
        "case_id": str(case.id),
        "created_claims": len(claims),
    }
