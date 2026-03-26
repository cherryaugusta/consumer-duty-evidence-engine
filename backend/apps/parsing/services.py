from pathlib import Path

from django.conf import settings

from apps.artifacts.models import DocumentSection, SourceArtifact


def parse_artifact_to_sections(artifact: SourceArtifact) -> int:
    media_root = Path(settings.MEDIA_ROOT)
    file_path = media_root / artifact.storage_path

    raw_text = file_path.read_text(encoding="utf-8", errors="ignore").strip()

    DocumentSection.objects.filter(artifact=artifact).delete()

    DocumentSection.objects.create(
        artifact=artifact,
        section_index=0,
        heading=None,
        text=raw_text,
        char_start=0,
        char_end=len(raw_text),
        page_number=None,
        parser_confidence=1.0,
    )

    artifact.text_length = len(raw_text)
    artifact.save(update_fields=["text_length"])

    return 1
