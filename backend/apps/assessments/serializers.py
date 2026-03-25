from rest_framework import serializers

from .models import ContradictionFlag, SupportAssessment


class SupportAssessmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportAssessment
        fields = "__all__"


class ContradictionFlagSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContradictionFlag
        fields = "__all__"
