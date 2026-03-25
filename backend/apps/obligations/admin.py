from django.contrib import admin

from .models import ConsumerDutyOutcome, EvidenceLink


@admin.register(ConsumerDutyOutcome)
class ConsumerDutyOutcomeAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "active")
    list_filter = ("active",)


@admin.register(EvidenceLink)
class EvidenceLinkAdmin(admin.ModelAdmin):
    list_display = ("case", "claim", "outcome", "link_type", "score")
    list_filter = ("link_type", "outcome")
