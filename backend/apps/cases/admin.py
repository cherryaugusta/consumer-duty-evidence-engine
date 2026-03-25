from django.contrib import admin

from .models import ReviewCase


@admin.register(ReviewCase)
class ReviewCaseAdmin(admin.ModelAdmin):
    list_display = (
        "reference_code",
        "title",
        "status",
        "review_status",
        "priority",
        "case_type",
        "created_at",
    )
    search_fields = ("reference_code", "title", "correlation_id")
    list_filter = ("status", "review_status", "priority", "case_type", "degraded_mode_active")
