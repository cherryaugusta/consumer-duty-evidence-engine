from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.artifacts.models import SourceArtifact
from apps.cases.models import ReviewCase
from apps.cases.serializers import ReviewCaseSerializer
from apps.parsing.tasks import parse_artifact_task
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
        serializer = ReviewCaseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=201)


class CaseDetailView(APIView):
    def get(self, request, pk):
        case = get_object_or_404(ReviewCase, pk=pk)
        return Response(ReviewCaseSerializer(case).data)


# -------------------------
# PIPELINE CONTROL
# -------------------------


class CaseRetryView(APIView):
    def post(self, request, pk):
        case = get_object_or_404(ReviewCase, pk=pk)

        case.status = "ingestion_pending"
        case.save()

        artifacts = SourceArtifact.objects.filter(case=case)

        for artifact in artifacts:
            parse_artifact_task.delay(str(artifact.id))

        return Response({"message": "Retry triggered", "artifacts": artifacts.count()})


class CaseReplayView(APIView):
    def post(self, request, pk):
        return Response({"message": "Replay not implemented"})


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
                {"detail": "Recommendation not ready"}, status=status.HTTP_404_NOT_FOUND
            )

        return Response(RecommendationSerializer(rec).data)


class CaseAuditEventsView(APIView):
    def get(self, request, pk):
        return Response([])


class CaseTimelineView(APIView):
    def get(self, request, pk):
        return Response([])
