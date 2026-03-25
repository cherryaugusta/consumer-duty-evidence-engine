from rest_framework import serializers

from .models import ReviewerAction, ReviewTask


class ReviewTaskSerializer(serializers.ModelSerializer):
    assigned_to_label = serializers.CharField(source="assigned_to.username", read_only=True)

    class Meta:
        model = ReviewTask
        fields = "__all__"


class ReviewActionSerializer(serializers.Serializer):
    comment = serializers.CharField(required=False, allow_blank=True)
    override_reason_code = serializers.CharField(required=False, allow_blank=True)


class ReviewerActionSerializer(serializers.ModelSerializer):
    reviewer_label = serializers.CharField(source="reviewer.username", read_only=True)

    class Meta:
        model = ReviewerAction
        fields = "__all__"
