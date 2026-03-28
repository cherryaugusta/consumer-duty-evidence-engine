from django.urls import path

from apps.observability.views import MetricsOverviewView

urlpatterns = [
    path("overview/", MetricsOverviewView.as_view(), name="metrics-overview"),
]
