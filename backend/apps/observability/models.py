import uuid

from django.db import models


class ExecutionStatus(models.TextChoices):
    SUCCESS = "success", "Success"
    TIMEOUT = "timeout", "Timeout"
    SCHEMA_FAIL = "schema_fail", "Schema fail"
    PROVIDER_ERROR = "provider_error", "Provider error"
    FALLBACK_USED = "fallback_used", "Fallback used"


class ModelExecutionLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey(
        "cases.ReviewCase", on_delete=models.CASCADE, related_name="model_execution_logs"
    )
    task_name = models.CharField(max_length=64)
    provider_name = models.CharField(max_length=64)
    model_name = models.CharField(max_length=128)
    prompt_version = models.ForeignKey(
        "recommendations.PromptVersion",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="execution_logs",
    )
    latency_ms = models.IntegerField()
    input_token_estimate = models.IntegerField(default=0)
    output_token_estimate = models.IntegerField(default=0)
    status = models.CharField(max_length=32, choices=ExecutionStatus.choices)
    cost_estimate = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["case", "task_name", "created_at"]),
        ]
