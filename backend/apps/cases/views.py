import uuid

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, status
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.assessments.serializers import SupportAssessmentSerializer
from apps.audits.serializers import AuditEventSerializer
from apps.core.constants import CaseStatus, ReviewStatus
from apps.extraction.serializers import ClaimSerializer
from apps.obligations.serializers import EvidenceLinkSerializer
from apps.recommendations.serializers import RecommendationSerializer

from .models import ReviewCase
from .serializers import (
    CaseReplaySerializer,
    CaseRetrySerializer,
    ReviewCaseCreateSerializer,
    ReviewCaseSerializer,
)


class CaseListCreateView(generics.ListCreateAPIView):
    queryset = ReviewCase.objects.all().order_by("-created_at")
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_fields = [
        "status",
        "priority",
        "review_status",
        "case_type",
        "degraded_mode_active",
    ]
    ordering_fields = ["created_at", "updated_at", "priority"]
    search_fields = ["reference_code", "title", "correlation_id"]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ReviewCaseCreateSerializer
        return ReviewCaseSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        case = serializer.save(
            reference_code=f"CDEE-{uuid.uuid4().hex[:12].upper()}",
            status=CaseStatus.INGESTION_PENDING,
            review_status=ReviewStatus.UNASSIGNED,
            correlation_id=uuid.uuid4().hex,
        )

        output = ReviewCaseSerializer(case, context={"request": request})
        headers = self.get_success_headers(output.data)
        return Response(output.data, status=status.HTTP_201_CREATED, headers=headers)


class CaseDetailView(generics.RetrieveUpdateAPIView):
    queryset = ReviewCase.objects.all()
    serializer_class = ReviewCaseSerializer


class CaseRetryView(APIView):
    def post(self, request, pk):
        serializer = CaseRetrySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        case = ReviewCase.objects.get(pk=pk)
        case.status = CaseStatus.INGESTION_PENDING
        case.save(update_fields=["status", "updated_at"])
        return Response(ReviewCaseSerializer(case).data, status=status.HTTP_200_OK)


class CaseReplayView(APIView):
    def post(self, request, pk):
        serializer = CaseReplaySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        case = ReviewCase.objects.get(pk=pk)
        case.status = CaseStatus.INGESTION_PENDING
        case.save(update_fields=["status", "updated_at"])
        return Response(
            {
                "case_id": str(case.id),
                "status": case.status,
                "from_stage": serializer.validated_data["from_stage"],
            },
            status=status.HTTP_200_OK,
        )


class CaseClaimsView(APIView):
    def get(self, request, pk):
        queryset = ReviewCase.objects.get(pk=pk).claims.all().order_by("-created_at")
        return Response(ClaimSerializer(queryset, many=True).data)


class CaseEvidenceLinksView(APIView):
    def get(self, request, pk):
        queryset = ReviewCase.objects.get(pk=pk).evidence_links.all()
        return Response(EvidenceLinkSerializer(queryset, many=True).data)


class CaseAssessmentsView(APIView):
    def get(self, request, pk):
        queryset = ReviewCase.objects.get(pk=pk).assessments.all().order_by("-created_at")
        return Response(SupportAssessmentSerializer(queryset, many=True).data)


class CaseRecommendationView(APIView):
    def get(self, request, pk):
        case = ReviewCase.objects.get(pk=pk)
        recommendation = getattr(case, "recommendation", None)
        if recommendation is None:
            return Response({})
        return Response(RecommendationSerializer(recommendation).data)


class CaseAuditEventsView(APIView):
    def get(self, request, pk):
        queryset = ReviewCase.objects.get(pk=pk).audit_events.all().order_by("-created_at")
        return Response(AuditEventSerializer(queryset, many=True).data)


class CaseTimelineView(APIView):
    def get(self, request, pk):
        queryset = ReviewCase.objects.get(pk=pk).audit_events.all().order_by("created_at")
        return Response(AuditEventSerializer(queryset, many=True).data)
