from django.core.cache import cache
from django.db import connection
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


class LiveView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"status": "ok"})


class ReadyView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        cache.set("healthcheck", "ok", 5)
        return Response({"status": "ready"})


class DepsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        db_ok = False
        redis_ok = False
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            db_ok = True
        except Exception:
            pass
        try:
            cache.set("depscheck", "ok", 5)
            redis_ok = cache.get("depscheck") == "ok"
        except Exception:
            pass
        status = "ok" if db_ok and redis_ok else "degraded"
        return Response({"status": status, "database": db_ok, "redis": redis_ok})
