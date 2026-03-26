import hashlib
import mimetypes
import os
import uuid
from pathlib import Path

from django.conf import settings
from django.core.files.uploadedfile import UploadedFile
from django.db import IntegrityError, transaction

from apps.artifacts.models import ParseStatus, SourceArtifact, SourceChannel
from apps.audits.models import ActorType, AuditEvent


def _sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _artifact_upload_dir(case_id) -> Path:
    return Path(settings.MEDIA_ROOT) / "cases" / str(case_id) / "artifacts"


def _safe_filename(filename: str) -> str:
    original = Path(filename).name
    stem = Path(original).stem
    suffix = Path(original).suffix
    normalized_stem = "".join(ch for ch in stem if ch.isalnum() or ch in {"-", "_"}).strip("._-")
    if not normalized_stem:
        normalized_stem = "artifact"
    return f"{normalized_stem}{suffix.lower()}"


def _build_storage_name(filename: str) -> str:
    safe_name = _safe_filename(filename)
    unique_prefix = uuid.uuid4().hex
    return f"{unique_prefix}_{safe_name}"


def _guess_mime_type(uploaded_file: UploadedFile) -> str:
    if getattr(uploaded_file, "content_type", None):
        return uploaded_file.content_type
    guessed, _ = mimetypes.guess_type(uploaded_file.name)
    return guessed or "application/octet-stream"


def create_artifact_from_upload(
    *,
    case,
    uploaded_file: UploadedFile,
    artifact_type: str,
    uploaded_by=None,
    correlation_id: str | None = None,
) -> SourceArtifact:
    file_bytes = uploaded_file.read()
    uploaded_file.seek(0)

    checksum = _sha256_bytes(file_bytes)
    existing = SourceArtifact.objects.filter(case=case, sha256_checksum=checksum).first()
    if existing:
        return existing

    upload_dir = _artifact_upload_dir(case.id)
    upload_dir.mkdir(parents=True, exist_ok=True)

    storage_name = _build_storage_name(uploaded_file.name)
    absolute_path = upload_dir / storage_name

    with open(absolute_path, "wb") as destination:
        destination.write(file_bytes)

    relative_storage_path = os.path.relpath(absolute_path, settings.MEDIA_ROOT).replace("\\", "/")

    try:
        with transaction.atomic():
            artifact = SourceArtifact.objects.create(
                case=case,
                artifact_type=artifact_type,
                filename=_safe_filename(uploaded_file.name),
                mime_type=_guess_mime_type(uploaded_file),
                source_channel=SourceChannel.UPLOAD,
                storage_path=relative_storage_path,
                sha256_checksum=checksum,
                parse_status=ParseStatus.PENDING,
                text_length=0,
            )

            AuditEvent.objects.create(
                case=case,
                event_type="artifact.uploaded",
                actor_type=ActorType.USER if uploaded_by else ActorType.SYSTEM,
                actor_id=str(uploaded_by.id) if uploaded_by else None,
                correlation_id=correlation_id or getattr(case, "correlation_id", "") or "",
                payload={
                    "artifact_id": str(artifact.id),
                    "artifact_type": artifact.artifact_type,
                    "filename": artifact.filename,
                    "mime_type": artifact.mime_type,
                    "storage_path": artifact.storage_path,
                    "sha256_checksum": artifact.sha256_checksum,
                },
            )

            return artifact
    except IntegrityError:
        duplicate = SourceArtifact.objects.filter(case=case, sha256_checksum=checksum).first()
        if duplicate:
            if absolute_path.exists():
                absolute_path.unlink(missing_ok=True)
            return duplicate
        raise
