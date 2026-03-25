import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[3]
load_dotenv(BASE_DIR / ".env", override=True)

SECRET_KEY = os.getenv("SECRET_KEY", "change-me")
DEBUG = os.getenv("DEBUG", "True").lower() == "true"
ALLOWED_HOSTS = [
    h.strip() for h in os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if h.strip()
]

INSTALLED_APPS = [
    "daphne",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "rest_framework_simplejwt",
    "drf_spectacular",
    "channels",
    "django_filters",
    "pgvector.django",
    "apps.core",
    "apps.accounts",
    "apps.cases",
    "apps.artifacts",
    "apps.parsing",
    "apps.extraction",
    "apps.obligations",
    "apps.assessments",
    "apps.recommendations",
    "apps.reviews",
    "apps.audits",
    "apps.evals",
    "apps.observability",
    "apps.health",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "apps.observability.middleware.CorrelationIdMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("POSTGRES_DB", "cdee"),
        "USER": os.getenv("POSTGRES_USER", "cdee"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD", "cdee"),
        "HOST": os.getenv("POSTGRES_HOST", "localhost"),
        "PORT": os.getenv("POSTGRES_PORT", "5432"),
    }
}

AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = "en-gb"
TIME_ZONE = "Europe/London"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "backend" / "staticfiles"
MEDIA_URL = os.getenv("MEDIA_URL", "/media/")
MEDIA_ROOT = BASE_DIR / os.getenv("MEDIA_ROOT", "backend/media")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "accounts.User"

CORS_ALLOWED_ORIGINS = [
    o.strip()
    for o in os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:5173").split(",")
    if o.strip()
]

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.OrderingFilter",
        "rest_framework.filters.SearchFilter",
    ),
    "DEFAULT_PAGINATION_CLASS": "apps.core.pagination.StandardPagination",
    "PAGE_SIZE": 20,
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=int(os.getenv("JWT_ACCESS_MINUTES", "30"))),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=int(os.getenv("JWT_REFRESH_DAYS", "7"))),
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Consumer Duty Evidence Engine API",
    "DESCRIPTION": (
        "Portfolio-grade simulation of an AI-assisted evidence review workflow "
        "inspired by Consumer Duty expectations."
    ),
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/2")
CHANNEL_LAYER_REDIS_URL = os.getenv("CHANNEL_LAYER_REDIS_URL", "redis://localhost:6379/3")

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {"hosts": [CHANNEL_LAYER_REDIS_URL]},
    }
}

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL,
        "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
    }
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {"()": "apps.observability.logging.JsonFormatter"},
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
        }
    },
    "root": {"handlers": ["console"], "level": "INFO"},
}

MODEL_PROVIDER = os.getenv("LLM_PROVIDER", "mock")
MODEL_NAME = os.getenv("LLM_MODEL", "mock-structured-v1")
SIMULATE_PROVIDER_FAILURE = os.getenv("SIMULATE_PROVIDER_FAILURE", "False").lower() == "true"
SIMULATE_SCHEMA_FAILURE = os.getenv("SIMULATE_SCHEMA_FAILURE", "False").lower() == "true"
DEGRADED_MODE_DEFAULT = os.getenv("DEGRADED_MODE_DEFAULT", "False").lower() == "true"
