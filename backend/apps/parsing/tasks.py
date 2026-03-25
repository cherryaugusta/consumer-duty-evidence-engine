from celery import shared_task

from apps.artifacts.models import SourceArtifact
from apps.parsing.services import parse_artifact_to_sections


@shared_task(bind=True, max_retries=3)
def parse_artifact_task(self, artifact_id: str):
    artifact = SourceArtifact.objects.get(pk=artifact_id)
    sections = parse_artifact_to_sections(artifact)
    return {"artifact_id": str(artifact.id), "sections_created": len(sections)}
