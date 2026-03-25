from django.contrib import admin

from .models import DocumentSection, SourceArtifact


@admin.register(SourceArtifact)
class SourceArtifactAdmin(admin.ModelAdmin):
    list_display = ("filename", "artifact_type", "source_channel", "parse_status", "uploaded_at")
    search_fields = ("filename", "sha256_checksum", "storage_path")
    list_filter = ("artifact_type", "source_channel", "parse_status")


@admin.register(DocumentSection)
class DocumentSectionAdmin(admin.ModelAdmin):
    list_display = ("artifact", "section_index", "heading", "page_number")
    search_fields = ("heading", "text")
