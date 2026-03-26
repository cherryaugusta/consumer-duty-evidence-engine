from __future__ import annotations

from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.cases.models import ReviewCase
from apps.recommendations.models import RecommendedAction
from apps.reviews.models import ReviewerAction, ReviewTask

User = get_user_model()


class SimpleUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name"]


class ReviewTaskCaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewCase
        fields = [
            "id",
            "reference_code",
            "title",
            "status",
            "review_status",
            "priority",
            "case_type",
            "degraded_mode_active",
            "created_at",
            "updated_at",
        ]


class ReviewerActionSerializer(serializers.ModelSerializer):
    reviewer = SimpleUserSerializer(read_only=True)

    class Meta:
        model = ReviewerAction
        fields = [
            "id",
            "review_task",
            "reviewer",
            "action_type",
            "old_value",
            "new_value",
            "comment",
            "override_reason_code",
            "created_at",
        ]


class ReviewTaskSerializer(serializers.ModelSerializer):
    case = ReviewTaskCaseSerializer(read_only=True)
    assigned_to = SimpleUserSerializer(read_only=True)
    actions = ReviewerActionSerializer(many=True, read_only=True)

    class Meta:
        model = ReviewTask
        fields = [
            "id",
            "case",
            "queue_name",
            "assigned_to",
            "status",
            "reason_code",
            "sla_due_at",
            "created_at",
            "updated_at",
            "actions",
        ]


class ReviewTaskAssignSerializer(serializers.Serializer):
    assignee_id = serializers.IntegerField(required=False)
    comment = serializers.CharField(required=False, allow_blank=True, default="")


class ReviewTaskApproveSerializer(serializers.Serializer):
    comment = serializers.CharField()


class ReviewTaskOverrideSerializer(serializers.Serializer):
    recommended_action = serializers.ChoiceField(
        choices=[
            RecommendedAction.APPROVE,
            RecommendedAction.REVIEW,
            RecommendedAction.ESCALATE,
            RecommendedAction.REQUEST_MORE_EVIDENCE,
        ]
    )
    recommended_priority = serializers.CharField(required=False, allow_blank=False)
    executive_summary = serializers.CharField(required=False, allow_blank=False)
    override_reason_code = serializers.CharField()
    comment = serializers.CharField()
    structured_rationale = serializers.JSONField(required=False)


class ReviewTaskEscalateSerializer(serializers.Serializer):
    comment = serializers.CharField()
