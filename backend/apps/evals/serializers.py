from rest_framework import serializers

from apps.evals.models import EvalRun


class EvalRunSerializer(serializers.ModelSerializer):
    class Meta:
        model = EvalRun
        fields = [
            "id",
            "run_label",
            "config_snapshot",
            "started_at",
            "finished_at",
            "status",
            "summary_metrics",
        ]


class EvalLatestReportSerializer(serializers.Serializer):
    run_label = serializers.CharField()
    summary_metrics = serializers.JSONField()
    thresholds = serializers.JSONField()
    total_cases = serializers.IntegerField()
    failure_breakdown = serializers.JSONField()
    scenario_breakdown = serializers.JSONField()
    top_failures = serializers.JSONField()
    top_successes = serializers.JSONField()
    results = serializers.JSONField()
