from django.urls import path

from .views import (
    CaseAssessmentsView,
    CaseAuditEventsView,
    CaseClaimsView,
    CaseDetailView,
    CaseEvidenceLinksView,
    CaseListCreateView,
    CaseRecommendationView,
    CaseReplayView,
    CaseRetryView,
    CaseTimelineView,
)

urlpatterns = [
    path("cases/", CaseListCreateView.as_view()),
    path("cases/<uuid:pk>/", CaseDetailView.as_view()),
    path("cases/<uuid:pk>/retry/", CaseRetryView.as_view()),
    path("cases/<uuid:pk>/replay/", CaseReplayView.as_view()),
    path("cases/<uuid:pk>/claims/", CaseClaimsView.as_view()),
    path("cases/<uuid:pk>/evidence-links/", CaseEvidenceLinksView.as_view()),
    path("cases/<uuid:pk>/assessments/", CaseAssessmentsView.as_view()),
    path("cases/<uuid:pk>/recommendation/", CaseRecommendationView.as_view()),
    path("cases/<uuid:pk>/audit-events/", CaseAuditEventsView.as_view()),
    path("cases/<uuid:pk>/timeline/", CaseTimelineView.as_view()),
]
