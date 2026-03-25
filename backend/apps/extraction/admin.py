from django.contrib import admin

from .models import Claim


@admin.register(Claim)
class ClaimAdmin(admin.ModelAdmin):
    list_display = ("claim_type", "case", "extraction_confidence", "schema_valid", "created_at")
    search_fields = ("claim_text", "normalized_claim_text")
    list_filter = ("claim_type", "schema_valid")
