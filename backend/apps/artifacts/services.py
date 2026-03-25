import hashlib
import uuid
from pathlib import Path

from django.conf import settings
from rest_framework import serializers

from .models import SourceArtifact


def create_artifact_from_upload(*, case, artifact_type: str, uploaded_file):
    content = uploaded_file.read()
    uploaded_file.seek(0)
    checksum = hashlib.sha256(content).hexdigest()

    existing = SourceArtifact.objects.filter(
        case=case,
        sha256_checksum=checksum,
    ).first()
    if existing:
        raise serializers.ValidationError({"detail": "Duplicate artifact upload for this case."})

    media_root = Path(settings.MEDIA_ROOT)
    media_root.mkdir(parents=True, exist_ok=True)

    filename = f"{uuid.uuid4()}_{uploaded_file.name}"
    relative_path = Path("artifacts") / filename
    full_path = media_root / relative_path
    full_path.parent.mkdir(parents=True, exist_ok=True)

    with open(full_path, "wb") as destination:
        for chunk in uploaded_file.chunks():
            destination.write(chunk)

    return SourceArtifact.objects.create(
        case=case,
        artifact_type=artifact_type,
        filename=uploaded_file.name,
        mime_type=uploaded_file.content_type or "application/octet-stream",
        source_channel="upload",
        storage_path=str(relative_path).replace("\\", "/"),
        sha256_checksum=checksum,
        text_length=0,
    )
