from django.urls import path

from .views import ArtifactDetailView, ArtifactListCreateView, ArtifactSectionsView

urlpatterns = [
    path("cases/<uuid:pk>/artifacts/", ArtifactListCreateView.as_view()),
    path("artifacts/<uuid:pk>/", ArtifactDetailView.as_view()),
    path("artifacts/<uuid:pk>/sections/", ArtifactSectionsView.as_view()),
]
