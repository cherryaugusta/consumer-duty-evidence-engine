from __future__ import annotations

from django.shortcuts import get_object_or_404
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import IsAuthenticated

from apps.cases.models import ReviewCase
from apps.recommendations.models import Recommendation
from apps.recommendations.serializers import RecommendationSerializer


class CaseRecommendationView(RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = RecommendationSerializer
    lookup_field = "case_id"

    def get_object(self):
        case_id = self.kwargs["case_id"]
        case = get_object_or_404(ReviewCase, id=case_id)
        return get_object_or_404(Recommendation, case=case)
