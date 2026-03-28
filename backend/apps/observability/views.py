from django.db.models import Count
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.cases.models import ReviewCase
from apps.core.constants import CaseStatus, ReviewStatus
from apps.observability.serializers import MetricsOverviewSerializer
from apps.reviews.models import ReviewTask


class MetricsOverviewView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        case_counts = {
            row["status"]: row["count"]
            for row in ReviewCase.objects.values("status").annotate(count=Count("id"))
        }
        review_task_counts = {
            row["status"]: row["count"]
            for row in ReviewTask.objects.values("status").annotate(count=Count("id"))
        }

        payload = {
            "total_cases": ReviewCase.objects.count(),
            "needs_review_cases": case_counts.get(CaseStatus.NEEDS_REVIEW, 0),
            "approved_cases": case_counts.get(CaseStatus.APPROVED, 0),
            "escalated_cases": case_counts.get(CaseStatus.ESCALATED, 0),
            "degraded_mode_cases": ReviewCase.objects.filter(degraded_mode_active=True).count(),
            "total_review_tasks": ReviewTask.objects.count(),
            "unassigned_review_tasks": review_task_counts.get(ReviewStatus.UNASSIGNED, 0),
            "assigned_review_tasks": review_task_counts.get(ReviewStatus.ASSIGNED, 0),
            "approved_review_tasks": review_task_counts.get(ReviewStatus.APPROVED, 0),
            "escalated_review_tasks": review_task_counts.get(ReviewStatus.ESCALATED, 0),
            "overridden_review_tasks": review_task_counts.get(ReviewStatus.OVERRIDDEN, 0),
        }

        serializer = MetricsOverviewSerializer(payload)
        return Response(serializer.data)
