from django.urls import path

from apps.artifacts.views import CaseArtifactListCreateView

urlpatterns = [
    path("cases/<uuid:id>/artifacts/", CaseArtifactListCreateView.as_view()),
]
