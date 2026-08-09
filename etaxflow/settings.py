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

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
