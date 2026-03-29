import json
from pathlib import Path

from django.conf import settings
from django.http import Http404
from rest_framework import status
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.cases.models import ReviewCase
from apps.evals.models import EvalRun
from apps.evals.serializers import EvalLatestReportSerializer, EvalRunSerializer


class EvalRunListView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = EvalRunSerializer
    queryset = EvalRun.objects.order_by("-started_at", "-id")


class EvalRunDetailView(RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = EvalRunSerializer
    queryset = EvalRun.objects.all()
    lookup_field = "id"
    lookup_url_kwarg = "pk"


class EvalLatestReportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        backend_dir = Path(settings.BASE_DIR) / "backend"
        project_root = backend_dir.parent
        report_path = project_root / "evals" / "reports" / "latest-report.json"

        if not report_path.exists():
            return Response(
                {"detail": "Latest eval report not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        with report_path.open(encoding="utf-8") as file_handle:
            payload = json.load(file_handle)

        serializer = EvalLatestReportSerializer(payload)
        return Response(serializer.data)


class EvalCaseLookupView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, eval_case_id: str):
        case = (
            ReviewCase.objects.filter(eval_case_id=eval_case_id)
            .order_by("-created_at", "-id")
            .first()
        )

        if case is None:
            raise Http404("No ReviewCase matches the given query.")

        return Response({"case_id": str(case.id)})
