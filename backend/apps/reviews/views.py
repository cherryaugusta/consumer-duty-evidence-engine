from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.constants import ReviewStatus

from .models import ReviewTask
from .serializers import ReviewActionSerializer, ReviewTaskSerializer


class ReviewTaskListView(generics.ListAPIView):
    queryset = ReviewTask.objects.all().order_by("sla_due_at", "-created_at")
    serializer_class = ReviewTaskSerializer


class ReviewTaskAssignView(APIView):
    def post(self, request, pk):
        task = ReviewTask.objects.get(pk=pk)
        task.assigned_to = request.user
        task.status = ReviewStatus.ASSIGNED
        task.save(update_fields=["assigned_to", "status", "updated_at"])
        return Response(ReviewTaskSerializer(task).data)


class ReviewTaskApproveView(APIView):
    def post(self, request, pk):
        serializer = ReviewActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        task = ReviewTask.objects.get(pk=pk)
        task.status = ReviewStatus.APPROVED
        task.save(update_fields=["status", "updated_at"])
        return Response(ReviewTaskSerializer(task).data, status=status.HTTP_200_OK)


class ReviewTaskOverrideView(APIView):
    def post(self, request, pk):
        serializer = ReviewActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        task = ReviewTask.objects.get(pk=pk)
        task.status = ReviewStatus.OVERRIDDEN
        task.save(update_fields=["status", "updated_at"])
        return Response(ReviewTaskSerializer(task).data, status=status.HTTP_200_OK)


class ReviewTaskEscalateView(APIView):
    def post(self, request, pk):
        serializer = ReviewActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        task = ReviewTask.objects.get(pk=pk)
        task.status = ReviewStatus.ESCALATED
        task.save(update_fields=["status", "updated_at"])
        return Response(ReviewTaskSerializer(task).data, status=status.HTTP_200_OK)
