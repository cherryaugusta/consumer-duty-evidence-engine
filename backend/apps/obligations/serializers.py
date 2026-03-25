from rest_framework import serializers

from .models import EvidenceLink


class EvidenceLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = EvidenceLink
        fields = "__all__"
