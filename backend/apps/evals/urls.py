from django.urls import path

from apps.evals.views import (
    EvalCaseLookupView,
    EvalLatestReportView,
    EvalRunDetailView,
    EvalRunListView,
)

urlpatterns = [
    path("evals/", EvalRunListView.as_view(), name="eval-run-list"),
    path("evals/<uuid:pk>/", EvalRunDetailView.as_view(), name="eval-run-detail"),
    path(
        "evals/reports/latest/",
        EvalLatestReportView.as_view(),
        name="eval-latest-report",
    ),
    path(
        "evals/lookup/<str:eval_case_id>/",
        EvalCaseLookupView.as_view(),
        name="eval-case-lookup",
    ),
]
