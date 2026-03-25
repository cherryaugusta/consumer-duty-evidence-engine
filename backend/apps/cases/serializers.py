from rest_framework import serializers

from .models import ReviewCase


class ReviewCaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewCase
        fields = "__all__"


class ReviewCaseCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewCase
        fields = ("title", "case_type", "priority")


class CaseRetrySerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True)


class CaseReplaySerializer(serializers.Serializer):
    from_stage = serializers.CharField()
    reason = serializers.CharField(required=False, allow_blank=True)
