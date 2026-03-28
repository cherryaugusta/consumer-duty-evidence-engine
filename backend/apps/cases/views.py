from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.artifacts.tasks import queue_case_parsing_if_ready
from apps.cases.models import ReviewCase
from apps.cases.serializers import (
    CaseReplaySerializer,
    CaseRetrySerializer,
    ReviewCaseCreateSerializer,
    ReviewCaseSerializer,
)
from apps.cases.services import transition_case
from apps.core.constants import CaseStatus
from apps.recommendations.models import Recommendation
from apps.recommendations.serializers import RecommendationSerializer

# -------------------------
# CORE CASE VIEWS
# -------------------------


class CaseListCreateView(APIView):
    def get(self, request):
        cases = ReviewCase.objects.all().order_by("-created_at")
        return Response(ReviewCaseSerializer(cases, many=True).data)

    def post(self, request):
        serializer = ReviewCaseCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        case = serializer.save()
        return Response(ReviewCaseSerializer(case).data, status=status.HTTP_201_CREATED)


class CaseDetailView(APIView):
    def get(self, request, pk):
        case = get_object_or_404(ReviewCase, pk=pk)
        return Response(ReviewCaseSerializer(case).data)


# -------------------------
# PIPELINE CONTROL
# -------------------------


class CaseRetryView(APIView):
    RETRYABLE_STATUSES = {
        CaseStatus.FAILED,
    }

    def post(self, request, pk):
        case = get_object_or_404(ReviewCase, pk=pk)
        serializer = CaseRetrySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if case.status not in self.RETRYABLE_STATUSES:
            return Response(
                {
                    "detail": (
                        f"Case retry is only allowed from {CaseStatus.FAILED}. "
                        f"Current status is {case.status}."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        transition_case(
            case=case,
            new_status=CaseStatus.INGESTION_PENDING,
            correlation_id=case.correlation_id,
            actor_type="user",
            actor_id=(
                str(request.user.id)
                if getattr(request, "user", None) and request.user.is_authenticated
                else None
            ),
            message="Case retry requested",
            payload={
                "reason": serializer.validated_data.get("reason", ""),
            },
        )

        case.refresh_from_db(fields=["status"])

        transition_case(
            case=case,
            new_status=CaseStatus.PARSING,
            correlation_id=case.correlation_id,
            actor_type="user",
            actor_id=(
                str(request.user.id)
                if getattr(request, "user", None) and request.user.is_authenticated
                else None
            ),
            message="Retry queued parsing",
            payload={
                "reason": serializer.validated_data.get("reason", ""),
            },
        )

        queue_case_parsing_if_ready.delay(str(case.id))

        return Response(
            {
                "message": "Retry triggered",
                "case_id": str(case.id),
                "status": case.status,
            },
            status=status.HTTP_202_ACCEPTED,
        )


class CaseReplayView(APIView):
    def post(self, request, pk):
        serializer = CaseReplaySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(
            {"detail": "Replay not implemented"},
            status=status.HTTP_501_NOT_IMPLEMENTED,
        )


# -------------------------
# DATA VIEWS (SAFE)
# -------------------------


class CaseClaimsView(APIView):
    def get(self, request, pk):
        return Response([])


class CaseEvidenceLinksView(APIView):
    def get(self, request, pk):
        return Response([])


class CaseAssessmentsView(APIView):
    def get(self, request, pk):
        return Response([])


class CaseRecommendationView(APIView):
    def get(self, request, pk):
        case = get_object_or_404(ReviewCase, pk=pk)

        rec = Recommendation.objects.filter(case=case).first()

        if not rec:
            return Response(
                {"detail": "Recommendation not ready"},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(RecommendationSerializer(rec).data)


class CaseAuditEventsView(APIView):
    def get(self, request, pk):
        return Response([])


class CaseTimelineView(APIView):
    def get(self, request, pk):
        return Response([])
