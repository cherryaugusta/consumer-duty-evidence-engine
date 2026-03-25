import uuid

from django.db import models


class EvalStatus(models.TextChoices):
    QUEUED = "queued", "Queued"
    RUNNING = "running", "Running"
    SUCCEEDED = "succeeded", "Succeeded"
    FAILED = "failed", "Failed"


class EvalCase(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dataset_name = models.CharField(max_length=64)
    scenario_type = models.CharField(max_length=64)
    input_bundle_path = models.CharField(max_length=500)
    ground_truth = models.JSONField(default=dict)
    is_adversarial = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


class EvalRun(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    run_label = models.CharField(max_length=128)
    config_snapshot = models.JSONField(default=dict)
    started_at = models.DateTimeField()
    finished_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=16, choices=EvalStatus.choices)
    summary_metrics = models.JSONField(default=dict, blank=True)
