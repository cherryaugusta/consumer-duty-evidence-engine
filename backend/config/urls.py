from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("apps.accounts.urls")),
    path("api/", include("apps.cases.urls")),
    path("api/", include("apps.artifacts.urls")),
    path("api/", include("apps.extraction.urls")),
    path("api/", include("apps.obligations.urls")),
    path("api/", include("apps.assessments.urls")),
    path("api/", include("apps.recommendations.urls")),
    path("api/", include("apps.reviews.urls")),
    path("api/", include("apps.audits.urls")),
    path("api/", include("apps.evals.urls")),
    path("api/metrics/", include("apps.observability.urls")),
    path("health/", include("apps.health.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
