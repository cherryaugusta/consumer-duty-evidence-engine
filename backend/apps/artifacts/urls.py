from django.urls import path

from apps.artifacts.views import (
    ArtifactDetailView,
    ArtifactSectionsView,
    CaseArtifactListCreateView,
)

urlpatterns = [
    path("cases/<uuid:id>/artifacts/", CaseArtifactListCreateView.as_view()),
    path("artifacts/<uuid:pk>/", ArtifactDetailView.as_view()),
    path("artifacts/<uuid:pk>/sections/", ArtifactSectionsView.as_view()),
]
