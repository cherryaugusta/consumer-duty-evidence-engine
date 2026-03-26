from rest_framework import serializers

from apps.artifacts.models import ArtifactType, SourceArtifact


class SourceArtifactSerializer(serializers.ModelSerializer):
    class Meta:
        model = SourceArtifact
        fields = [
            "id",
            "case",
            "artifact_type",
            "filename",
            "mime_type",
            "source_channel",
            "storage_path",
            "sha256_checksum",
            "parse_status",
            "parse_error_code",
            "text_length",
            "uploaded_at",
        ]
        read_only_fields = [
            "id",
            "case",
            "filename",
            "mime_type",
            "source_channel",
            "storage_path",
            "sha256_checksum",
            "parse_status",
            "parse_error_code",
            "text_length",
            "uploaded_at",
        ]


class ArtifactUploadSerializer(serializers.Serializer):
    artifact_type = serializers.ChoiceField(choices=ArtifactType.choices)
    file = serializers.FileField()
