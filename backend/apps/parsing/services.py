from pathlib import Path

from django.conf import settings

from apps.artifacts.models import DocumentSection, ParseStatus


def parse_artifact_to_sections(artifact):
    full_path = Path(settings.MEDIA_ROOT) / artifact.storage_path
    if not full_path.exists():
        artifact.parse_status = ParseStatus.FAILED
        artifact.parse_error_code = "missing_file"
        artifact.save(update_fields=["parse_status", "parse_error_code"])
        return []

    artifact.parse_status = ParseStatus.RUNNING
    artifact.save(update_fields=["parse_status"])

    text = full_path.read_text(encoding="utf-8", errors="ignore")
    artifact.text_length = len(text)
    artifact.parse_status = ParseStatus.PARSED
    artifact.parse_error_code = None
    artifact.save(update_fields=["text_length", "parse_status", "parse_error_code"])

    DocumentSection.objects.filter(artifact=artifact).delete()

    if not text.strip():
        return []

    sections = []
    chunk_size = 1200
    for index, start in enumerate(range(0, len(text), chunk_size)):
        end = min(start + chunk_size, len(text))
        section = DocumentSection.objects.create(
            artifact=artifact,
            section_index=index,
            heading=None,
            text=text[start:end],
            char_start=start,
            char_end=end,
            page_number=None,
            parser_confidence=0.8,
        )
        sections.append(section)

    return sections
