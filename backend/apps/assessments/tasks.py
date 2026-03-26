from celery import shared_task

from apps.assessments.services import assess_case_support, detect_case_contradictions
from apps.cases.models import ReviewCase
from apps.core.constants import CaseStatus
from apps.recommendations.tasks import recommend_case_task


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=5, max_retries=2)
def assess_case_task(self, case_id: str):
    case = ReviewCase.objects.get(pk=case_id)

    assessments = assess_case_support(case)
    contradictions = detect_case_contradictions(case)

    # Normalize workflow state before recommendation.
    # Recommendation routing expects the case to already be in ASSESSED.
    case.status = CaseStatus.ASSESSED
    case.save(update_fields=["status", "updated_at"])

    recommend_case_task.delay(str(case.id))

    return {
        "case_id": str(case.id),
        "created_assessments": len(assessments),
        "created_contradictions": len(contradictions),
        "queued_recommendation": True,
        "case_status": case.status,
    }
