from celery import shared_task


@shared_task(bind=True, max_retries=2)
def extract_case_task(self, case_id: str):
    return {"case_id": case_id, "stage": "extraction", "status": "placeholder"}
