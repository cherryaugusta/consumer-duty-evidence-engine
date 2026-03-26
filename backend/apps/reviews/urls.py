from django.urls import path

from apps.reviews.views import (
    ReviewTaskApproveView,
    ReviewTaskAssignView,
    ReviewTaskEscalateView,
    ReviewTaskListView,
    ReviewTaskOverrideView,
)

urlpatterns = [
    path("review-tasks/", ReviewTaskListView.as_view()),
    path("review-tasks/<uuid:pk>/assign/", ReviewTaskAssignView.as_view()),
    path("review-tasks/<uuid:pk>/approve/", ReviewTaskApproveView.as_view()),
    path("review-tasks/<uuid:pk>/override/", ReviewTaskOverrideView.as_view()),
    path("review-tasks/<uuid:pk>/escalate/", ReviewTaskEscalateView.as_view()),
]
