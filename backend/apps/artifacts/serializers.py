from rest_framework import serializers

from .models import DocumentSection, SourceArtifact


class SourceArtifactSerializer(serializers.ModelSerializer):
    class Meta:
        model = SourceArtifact
        fields = "__all__"


class DocumentSectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentSection
        fields = "__all__"


class SourceArtifactCreateSerializer(serializers.Serializer):
    artifact_type = serializers.ChoiceField(
        choices=SourceArtifact._meta.get_field("artifact_type").choices
    )
    file = serializers.FileField()
