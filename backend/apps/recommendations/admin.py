from django.contrib import admin

from .models import PromptVersion, Recommendation


@admin.register(PromptVersion)
class PromptVersionAdmin(admin.ModelAdmin):
    list_display = ("name", "version_label", "purpose", "schema_version", "is_active", "created_at")
    list_filter = ("purpose", "is_active")


@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    list_display = (
        "case",
        "recommended_action",
        "recommended_priority",
        "confidence",
        "citation_count",
        "created_at",
    )
    list_filter = ("recommended_action",)
