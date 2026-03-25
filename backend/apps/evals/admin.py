from django.contrib import admin

from .models import EvalCase, EvalRun


@admin.register(EvalCase)
class EvalCaseAdmin(admin.ModelAdmin):
    list_display = ("dataset_name", "scenario_type", "is_adversarial", "created_at")
    list_filter = ("dataset_name", "scenario_type", "is_adversarial")


@admin.register(EvalRun)
class EvalRunAdmin(admin.ModelAdmin):
    list_display = ("run_label", "status", "started_at", "finished_at")
    list_filter = ("status",)
