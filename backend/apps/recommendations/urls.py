from django.urls import path

from apps.recommendations.views import CaseRecommendationView

urlpatterns = [
    path("cases/<uuid:case_id>/recommendation/", CaseRecommendationView.as_view()),
]
