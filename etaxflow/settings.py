"""
Django settings for etaxflow project.
"""

import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent


def _env_bool(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).lower() in {"1", "true", "yes", "on"}


def _env_csv(name: str, default: str = "") -> list[str]:
    return [part.strip() for part in os.getenv(name, default).split(",") if part.strip()]


DEBUG = _env_bool("DEBUG", "True")

_raw_secret = os.getenv("SECRET_KEY", "").strip()
if not DEBUG:
    if not _raw_secret or _raw_secret in {
        "django-insecure-dev-key",
        "replace-me-with-secure-key",
    }:
        raise ImproperlyConfigured(
            "SECRET_KEY must be set to a non-default value when DEBUG=false."
        )
    SECRET_KEY = _raw_secret
else:
    SECRET_KEY = _raw_secret or "django-insecure-dev-key"

ALLOWED_HOSTS = _env_csv("ALLOWED_HOSTS", "localhost,127.0.0.1")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "core",
    "organizations",
    "contacts",
    "documents",
    "invoicing",
    "fiscal",
    "ecf",
    "audit",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "etaxflow.urls"

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
            ],
        },
    },
]

WSGI_APPLICATION = "etaxflow.wsgi.application"

# Database: PostgreSQL exclusively via DATABASE_URL when DEBUG=false.
# Local DEBUG=true may use SQLite; staging/production must not fall back silently.
_database_url = os.getenv("DATABASE_URL", "").strip()
if _database_url:
    import dj_database_url

    DATABASES = {
        "default": dj_database_url.parse(
            _database_url,
            conn_max_age=600,
            ssl_require=_env_bool("DATABASE_SSL_REQUIRE", "false" if DEBUG else "true"),
        )
    }
elif not DEBUG:
    raise ImproperlyConfigured(
        "DATABASE_URL is required when DEBUG=false. SQLite fallback is disabled in staging."
    )
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}

MEDIA_URL = "/media/"
MEDIA_ROOT = os.getenv("MEDIA_ROOT", str(BASE_DIR / "media"))

# HTTPS / proxy settings appropriate for Render (terminates TLS at the edge).
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
CSRF_TRUSTED_ORIGINS = _env_csv("CSRF_TRUSTED_ORIGINS")
SECURE_SSL_REDIRECT = _env_bool("SECURE_SSL_REDIRECT", "false")
SESSION_COOKIE_SECURE = _env_bool("SESSION_COOKIE_SECURE", "false" if DEBUG else "true")
CSRF_COOKIE_SECURE = _env_bool("CSRF_COOKIE_SECURE", "false" if DEBUG else "true")
SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "0"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = _env_bool("SECURE_HSTS_INCLUDE_SUBDOMAINS", "false")
SECURE_HSTS_PRELOAD = _env_bool("SECURE_HSTS_PRELOAD", "false")
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

# XML/DGII signing architecture placeholders. All defaults are disabled and
# test-safe. Phase 015 does not implement XMLDSig or load certificate/key material.
# IMPORTANT: do not assign Django's SIGNING_BACKEND (cookie/HMAC signer path).
# Env var SIGNING_BACKEND remains the documented placeholder and maps here.
SIGNING_MODE = os.getenv("SIGNING_MODE", "DISABLED")
ETAXFLOW_SIGNING_BACKEND = os.getenv("SIGNING_BACKEND", "NONE")
SIGNING_ENABLED = _env_bool("SIGNING_ENABLED", "false")
SIGNING_ALLOW_TEST_ONLY = _env_bool("SIGNING_ALLOW_TEST_ONLY", "false")
SIGNING_CERT_PATH = os.getenv("SIGNING_CERT_PATH", "")
SIGNING_KEY_PATH = os.getenv("SIGNING_KEY_PATH", "")
SIGNING_PASS_ENV_VAR = os.getenv("SIGNING_PASS_ENV_VAR", "")

# DGII service-contract placeholders. Defaults are mock/offline only and contain
# no live endpoint or credential. Phase 019 adds no HTTP transport.
DGII_ENVIRONMENT = os.getenv("DGII_ENVIRONMENT", "MOCK")
DGII_SOFTWARE_NAME = os.getenv("DGII_SOFTWARE_NAME", "eTaxFlow")
DGII_SOFTWARE_VERSION = os.getenv("DGII_SOFTWARE_VERSION", "MVP")
DGII_SOFTWARE_TYPE = os.getenv("DGII_SOFTWARE_TYPE", "INTERNAL")
DGII_URL_RECEPCION = os.getenv("DGII_URL_RECEPCION", "")
DGII_URL_APROBACION_COMERCIAL = os.getenv("DGII_URL_APROBACION_COMERCIAL", "")
DGII_URL_AUTENTICACION = os.getenv("DGII_URL_AUTENTICACION", "")
DGII_LIVE_TRANSPORT_ENABLED = _env_bool("DGII_LIVE_TRANSPORT_ENABLED", "false")

# Phase 025 — pre-certification endpoint design placeholders (disabled by default).
# These are for DGII portal registration metadata composition only; not live endpoints.
ETAXFLOW_SOFTWARE_NAME = os.getenv("ETAXFLOW_SOFTWARE_NAME", "eTaxFlow")
ETAXFLOW_SOFTWARE_VERSION = os.getenv("ETAXFLOW_SOFTWARE_VERSION", "0.1.0")
ETAXFLOW_SOFTWARE_TYPE = os.getenv("ETAXFLOW_SOFTWARE_TYPE", "PROPIO")
ETAXFLOW_PUBLIC_BASE_URL = os.getenv("ETAXFLOW_PUBLIC_BASE_URL", "")
ETAXFLOW_DGII_RECEPCION_PATH = os.getenv(
    "ETAXFLOW_DGII_RECEPCION_PATH", "/fe/recepcion/api/ecf"
)
ETAXFLOW_DGII_APROBACION_COMERCIAL_PATH = os.getenv(
    "ETAXFLOW_DGII_APROBACION_COMERCIAL_PATH", "/fe/aprobacioncomercial/api/ecf"
)
ETAXFLOW_DGII_AUTENTICACION_PATH_TEMPLATE = os.getenv(
    "ETAXFLOW_DGII_AUTENTICACION_PATH_TEMPLATE",
    "/fe/autenticacion/api/[semilla]validacioncertificado",
)
ETAXFLOW_ENABLE_PUBLIC_DGII_ENDPOINTS = _env_bool(
    "ETAXFLOW_ENABLE_PUBLIC_DGII_ENDPOINTS", "false"
)

# Phase 034 — inbound security policy placeholders (CONFIGURED_PLACEHOLDER ≠ ENFORCED).
# Public views do not enforce these yet; security policy lab reports them honestly.
ETAXFLOW_DGII_INBOUND_MAX_BODY_BYTES = int(
    os.getenv("ETAXFLOW_DGII_INBOUND_MAX_BODY_BYTES", "1048576")
)
ETAXFLOW_DGII_INBOUND_ALLOWED_CONTENT_TYPES = os.getenv(
    "ETAXFLOW_DGII_INBOUND_ALLOWED_CONTENT_TYPES",
    "application/xml,text/xml",
)
ETAXFLOW_DGII_INBOUND_RATE_LIMIT_POLICY = os.getenv(
    "ETAXFLOW_DGII_INBOUND_RATE_LIMIT_POLICY", "NOT_IMPLEMENTED"
)
ETAXFLOW_DGII_LOG_RAW_XML = _env_bool("ETAXFLOW_DGII_LOG_RAW_XML", "false")
ETAXFLOW_DGII_STORE_RAW_XML_DEFAULT = _env_bool(
    "ETAXFLOW_DGII_STORE_RAW_XML_DEFAULT", "false"
)

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
