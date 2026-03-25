from django.contrib import admin

from .models import AuditEvent


@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    list_display = ("case", "event_type", "actor_type", "actor_id", "created_at")
    list_filter = ("actor_type", "event_type")
    search_fields = ("correlation_id", "actor_id")
