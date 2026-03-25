from django.contrib import admin

from .models import ContradictionFlag, SupportAssessment


@admin.register(SupportAssessment)
class SupportAssessmentAdmin(admin.ModelAdmin):
    list_display = (
        "case",
        "claim",
        "outcome",
        "status",
        "confidence",
        "requires_review",
        "created_at",
    )
    list_filter = ("status", "requires_review")


@admin.register(ContradictionFlag)
class ContradictionFlagAdmin(admin.ModelAdmin):
    list_display = ("case", "contradiction_type", "severity", "created_at")
    list_filter = ("contradiction_type", "severity")
