from django.urls import path

from .views import DepsView, LiveView, ReadyView

urlpatterns = [
    path("live", LiveView.as_view()),
    path("ready", ReadyView.as_view()),
    path("deps", DepsView.as_view()),
]
