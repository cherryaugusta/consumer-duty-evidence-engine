from __future__ import annotations

from rest_framework import serializers

from apps.recommendations.models import Recommendation


class RecommendationSerializer(serializers.ModelSerializer):
    prompt_version_name = serializers.SerializerMethodField()
    prompt_version_label = serializers.SerializerMethodField()

    class Meta:
        model = Recommendation
        fields = [
            "id",
            "case",
            "recommended_action",
            "recommended_priority",
            "executive_summary",
            "structured_rationale",
            "confidence",
            "citation_count",
            "model_version",
            "prompt_version",
            "prompt_version_name",
            "prompt_version_label",
            "created_at",
        ]

    def get_prompt_version_name(self, obj):
        if not obj.prompt_version:
            return None
        return obj.prompt_version.name

    def get_prompt_version_label(self, obj):
        if not obj.prompt_version:
            return None
        return obj.prompt_version.version_label
