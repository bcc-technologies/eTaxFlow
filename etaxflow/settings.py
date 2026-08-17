"""
Django settings for etaxflow project.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-dev-key")
DEBUG = os.getenv("DEBUG", "True").lower() in {"1", "true", "yes", "on"}
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

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

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

if os.getenv("DATABASE_URL"):
    import dj_database_url

    DATABASES["default"] = dj_database_url.config(default=os.getenv("DATABASE_URL"))

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
MEDIA_URL = "/media/"
MEDIA_ROOT = os.getenv("MEDIA_ROOT", str(BASE_DIR / "media"))

# Signing architecture placeholders. All defaults are disabled and test-safe;
# Phase 015 does not implement XMLDSig or load any certificate/key material.
SIGNING_MODE = os.getenv("SIGNING_MODE", "DISABLED")
SIGNING_BACKEND = os.getenv("SIGNING_BACKEND", "NONE")
SIGNING_ENABLED = os.getenv("SIGNING_ENABLED", "false").lower() in {
    "1",
    "true",
    "yes",
    "on",
}
SIGNING_ALLOW_TEST_ONLY = os.getenv("SIGNING_ALLOW_TEST_ONLY", "false").lower() in {
    "1",
    "true",
    "yes",
    "on",
}
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
DGII_LIVE_TRANSPORT_ENABLED = os.getenv(
    "DGII_LIVE_TRANSPORT_ENABLED", "false"
).lower() in {"1", "true", "yes", "on"}

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
ETAXFLOW_ENABLE_PUBLIC_DGII_ENDPOINTS = os.getenv(
    "ETAXFLOW_ENABLE_PUBLIC_DGII_ENDPOINTS", "false"
).lower() in {"1", "true", "yes", "on"}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
