from django.urls import re_path

from apps.cases.consumers import CaseStatusConsumer

websocket_urlpatterns = [
    re_path(r"ws/cases/(?P<case_id>[0-9a-f-]+)/$", CaseStatusConsumer.as_asgi()),
]
