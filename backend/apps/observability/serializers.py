from rest_framework import serializers


class MetricsOverviewSerializer(serializers.Serializer):
    total_cases = serializers.IntegerField()
    needs_review_cases = serializers.IntegerField()
    approved_cases = serializers.IntegerField()
    escalated_cases = serializers.IntegerField()
    degraded_mode_cases = serializers.IntegerField()
    total_review_tasks = serializers.IntegerField()
    unassigned_review_tasks = serializers.IntegerField()
    assigned_review_tasks = serializers.IntegerField()
    approved_review_tasks = serializers.IntegerField()
    escalated_review_tasks = serializers.IntegerField()
    overridden_review_tasks = serializers.IntegerField()
