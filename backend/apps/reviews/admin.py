from django.contrib import admin

from .models import ReviewerAction, ReviewTask


@admin.register(ReviewTask)
class ReviewTaskAdmin(admin.ModelAdmin):
    list_display = (
        "case",
        "queue_name",
        "assigned_to",
        "status",
        "reason_code",
        "sla_due_at",
        "created_at",
    )
    list_filter = ("status", "reason_code", "queue_name")


@admin.register(ReviewerAction)
class ReviewerActionAdmin(admin.ModelAdmin):
    list_display = ("review_task", "reviewer", "action_type", "created_at")
    list_filter = ("action_type",)
