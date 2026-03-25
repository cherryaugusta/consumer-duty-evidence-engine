from celery import shared_task


@shared_task(bind=True, max_retries=1)
def recommend_case_task(self, case_id: str):
    return {"case_id": case_id, "stage": "recommendation", "status": "placeholder"}
