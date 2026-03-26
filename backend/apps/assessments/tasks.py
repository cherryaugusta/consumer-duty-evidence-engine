from celery import shared_task

from apps.assessments.services import assess_case_support, detect_case_contradictions
from apps.cases.models import ReviewCase


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=5, max_retries=2)
def assess_case_task(self, case_id: str):
    case = ReviewCase.objects.get(pk=case_id)

    assessments = assess_case_support(case)
    contradictions = detect_case_contradictions(case)

    return {
        "case_id": str(case.id),
        "created_assessments": len(assessments),
        "created_contradictions": len(contradictions),
    }
