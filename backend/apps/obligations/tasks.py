from celery import shared_task

from apps.assessments.tasks import assess_case_task
from apps.cases.models import ReviewCase
from apps.obligations.services import map_case_outcomes


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=5, max_retries=2)
def map_case_task(self, case_id: str):
    case = ReviewCase.objects.get(pk=case_id)

    links = map_case_outcomes(case)

    assess_case_task.delay(str(case.id))

    return {
        "case_id": str(case.id),
        "created_links": len(links),
    }
