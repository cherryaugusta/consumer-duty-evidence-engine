from __future__ import annotations

from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status
from rest_framework.generics import GenericAPIView, ListAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.reviews.models import ReviewTask
from apps.reviews.serializers import (
    ReviewTaskApproveSerializer,
    ReviewTaskAssignSerializer,
    ReviewTaskEscalateSerializer,
    ReviewTaskOverrideSerializer,
    ReviewTaskSerializer,
)
from apps.reviews.services import (
    approve_review_task,
    assign_review_task,
    escalate_review_task,
    override_review_task,
)

User = get_user_model()


class ReviewTaskListView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ReviewTaskSerializer
    queryset = (
        ReviewTask.objects.select_related("case", "assigned_to")
        .prefetch_related("actions__reviewer")
        .order_by("sla_due_at", "-created_at")
    )
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_fields = ["reason_code", "status", "queue_name", "assigned_to"]
    ordering_fields = ["created_at", "updated_at", "sla_due_at"]
    search_fields = [
        "case__reference_code",
        "case__title",
        "case__correlation_id",
    ]


class ReviewTaskDetailView(RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ReviewTaskSerializer
    queryset = ReviewTask.objects.select_related("case", "assigned_to").prefetch_related(
        "actions__reviewer"
    )
    lookup_field = "id"
    lookup_url_kwarg = "pk"


class ReviewTaskAssignView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ReviewTaskAssignSerializer

    def post(self, request, pk):
        review_task = get_object_or_404(ReviewTask, id=pk)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        assignee = request.user
        assignee_id = serializer.validated_data.get("assignee_id")
        if assignee_id is not None:
            assignee = get_object_or_404(User, id=assignee_id)

        review_task = assign_review_task(
            review_task=review_task,
            reviewer=request.user,
            assignee=assignee,
            comment=serializer.validated_data.get("comment", ""),
        )

        return Response(ReviewTaskSerializer(review_task).data, status=status.HTTP_200_OK)


class ReviewTaskApproveView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ReviewTaskApproveSerializer

    def post(self, request, pk):
        review_task = get_object_or_404(ReviewTask, id=pk)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        review_task = approve_review_task(
            review_task=review_task,
            reviewer=request.user,
            comment=serializer.validated_data["comment"],
        )

        return Response(ReviewTaskSerializer(review_task).data, status=status.HTTP_200_OK)


class ReviewTaskOverrideView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ReviewTaskOverrideSerializer

    def post(self, request, pk):
        review_task = get_object_or_404(ReviewTask, id=pk)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        review_task = override_review_task(
            review_task=review_task,
            reviewer=request.user,
            recommended_action=serializer.validated_data["recommended_action"],
            recommended_priority=serializer.validated_data.get("recommended_priority"),
            executive_summary=serializer.validated_data.get("executive_summary"),
            structured_rationale=serializer.validated_data.get("structured_rationale"),
            override_reason_code=serializer.validated_data["override_reason_code"],
            comment=serializer.validated_data["comment"],
        )

        return Response(ReviewTaskSerializer(review_task).data, status=status.HTTP_200_OK)


class ReviewTaskEscalateView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ReviewTaskEscalateSerializer

    def post(self, request, pk):
        review_task = get_object_or_404(ReviewTask, id=pk)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        review_task = escalate_review_task(
            review_task=review_task,
            reviewer=request.user,
            comment=serializer.validated_data["comment"],
        )

        return Response(ReviewTaskSerializer(review_task).data, status=status.HTTP_200_OK)
