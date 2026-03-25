from django.contrib import admin

from .models import ModelExecutionLog


@admin.register(ModelExecutionLog)
class ModelExecutionLogAdmin(admin.ModelAdmin):
    list_display = (
        "case",
        "task_name",
        "provider_name",
        "model_name",
        "status",
        "latency_ms",
        "created_at",
    )
    list_filter = ("status", "provider_name", "task_name")
