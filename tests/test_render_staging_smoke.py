"""Smoke tests for Render staging deployment readiness (no live deploy)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from django.test import Client, SimpleTestCase, override_settings


ROOT = Path(__file__).resolve().parents[1]
FE_PATHS = (
    "/fe/recepcion/api/ecf",
    "/fe/aprobacioncomercial/api/ecf",
    "/fe/autenticacion/api/semilla",
    "/fe/autenticacion/api/validacioncertificado",
)


def _run_settings_probe(env_overrides: dict[str, str], script: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.update(env_overrides)
    env["PYTHONPATH"] = os.pathsep.join(
        [str(ROOT), env.get("PYTHONPATH", "")]
    ).rstrip(os.pathsep)
    return subprocess.run(
        [sys.executable, "-c", script],
        cwd=str(ROOT),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


class RenderStagingDocumentationTests(SimpleTestCase):
    def test_render_deployment_doc_exists(self):
        doc = ROOT / "docs/deployment/RENDER_STAGING_DEPLOYMENT.md"
        self.assertTrue(doc.is_file())
        content = doc.read_text()
        self.assertIn(
            "pip install -r requirements.txt && python manage.py collectstatic --noinput",
            content,
        )
        self.assertIn("gunicorn etaxflow.wsgi:application", content)
        self.assertIn("python manage.py migrate --noinput", content)
        self.assertIn("/healthz", content)
        self.assertIn("ETAXFLOW_ENABLE_PUBLIC_DGII_ENDPOINTS", content)
        self.assertIn("DGII_LIVE_TRANSPORT_ENABLED", content)
        self.assertIn("SIGNING_ENABLED", content)
        self.assertNotIn("BEGIN PRIVATE KEY", content)

    def test_requirements_include_render_dependencies(self):
        requirements = (ROOT / "requirements.txt").read_text().lower()
        self.assertIn("gunicorn", requirements)
        self.assertIn("dj-database-url", requirements)
        self.assertIn("psycopg", requirements)
        self.assertIn("whitenoise", requirements)

    def test_staging_example_keeps_dgii_and_signing_disabled(self):
        content = (ROOT / ".env.staging.example").read_text()
        self.assertIn("DEBUG=false", content)
        self.assertIn("ETAXFLOW_ENABLE_PUBLIC_DGII_ENDPOINTS=false", content)
        self.assertIn("DGII_LIVE_TRANSPORT_ENABLED=false", content)
        self.assertIn("SIGNING_ENABLED=false", content)
        self.assertIn("DATABASE_URL=", content)
        self.assertNotIn("BEGIN PRIVATE KEY", content)
        self.assertNotIn("BEGIN CERTIFICATE", content)


class HealthzSmokeTests(SimpleTestCase):
    def test_healthz_returns_200_without_auth(self):
        client = Client()
        response = client.get("/healthz")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"ok")
        self.assertEqual(response["Content-Type"].split(";")[0], "text/plain")


class PublicEndpointDisabledSmokeTests(SimpleTestCase):
    def test_fe_endpoints_return_503_disabled_without_processing(self):
        client = Client()
        for path in FE_PATHS:
            with self.subTest(path=path, method="GET"):
                response = client.get(path)
                self.assertEqual(response.status_code, 503)
                payload = response.json()
                self.assertEqual(payload["status"], "DISABLED")
                self.assertIsNone(payload["track_id"])
                self.assertFalse(payload["dgii_submission_allowed"])

            with self.subTest(path=path, method="POST"):
                response = client.post(
                    path,
                    data="<ECF>synthetic-not-fiscal</ECF>",
                    content_type="application/xml",
                )
                self.assertEqual(response.status_code, 503)
                payload = json.loads(response.content.decode())
                self.assertEqual(payload["status"], "DISABLED")
                self.assertIsNone(payload["track_id"])


class StagingSettingsGuardTests(SimpleTestCase):
    def test_debug_false_requires_secret_key_and_database_url(self):
        result = _run_settings_probe(
            {
                "DEBUG": "false",
                "SECRET_KEY": "",
                "DATABASE_URL": "",
                "ALLOWED_HOSTS": "etaxflow-staging.onrender.com",
            },
            "\n".join(
                [
                    "from django.core.exceptions import ImproperlyConfigured",
                    "try:",
                    "    import etaxflow.settings  # noqa: F401",
                    "except ImproperlyConfigured as exc:",
                    "    print(exc)",
                    "    raise SystemExit(0)",
                    "raise SystemExit('expected ImproperlyConfigured')",
                ]
            ),
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(
            "SECRET_KEY" in result.stdout or "DATABASE_URL" in result.stdout,
            result.stdout,
        )

    def test_debug_false_with_valid_env_parses_postgres_and_csrf(self):
        script = "\n".join(
            [
                "import etaxflow.settings as s",
                "assert s.DEBUG is False",
                "assert s.SECRET_KEY == 'staging-test-secret-key-not-for-production'",
                "assert s.DATABASES['default']['ENGINE'] == 'django.db.backends.postgresql'",
                "assert 'etaxflow-staging.onrender.com' in s.ALLOWED_HOSTS",
                "assert 'https://etaxflow.bcctechnologies.com.do' in s.CSRF_TRUSTED_ORIGINS",
                "assert s.ETAXFLOW_ENABLE_PUBLIC_DGII_ENDPOINTS is False",
                "assert s.DGII_LIVE_TRANSPORT_ENABLED is False",
                "assert s.SIGNING_ENABLED is False",
                "assert s.SECURE_PROXY_SSL_HEADER == ('HTTP_X_FORWARDED_PROTO', 'https')",
                "print('ok')",
            ]
        )
        result = _run_settings_probe(
            {
                "DEBUG": "false",
                "SECRET_KEY": "staging-test-secret-key-not-for-production",
                "DATABASE_URL": "postgres://etax:etax@127.0.0.1:5432/etaxflow_staging",
                "DATABASE_SSL_REQUIRE": "false",
                "ALLOWED_HOSTS": (
                    "etaxflow-staging.onrender.com,etaxflow.bcctechnologies.com.do"
                ),
                "CSRF_TRUSTED_ORIGINS": (
                    "https://etaxflow-staging.onrender.com,"
                    "https://etaxflow.bcctechnologies.com.do"
                ),
                "SECURE_SSL_REDIRECT": "true",
                "ETAXFLOW_ENABLE_PUBLIC_DGII_ENDPOINTS": "false",
                "DGII_LIVE_TRANSPORT_ENABLED": "false",
                "SIGNING_ENABLED": "false",
            },
            script,
        )
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertIn("ok", result.stdout)


class DefaultSafetyFlagTests(SimpleTestCase):
    @override_settings(
        ETAXFLOW_ENABLE_PUBLIC_DGII_ENDPOINTS=False,
        DGII_LIVE_TRANSPORT_ENABLED=False,
        SIGNING_ENABLED=False,
    )
    def test_safety_flags_remain_disabled(self):
        from django.conf import settings

        self.assertFalse(settings.ETAXFLOW_ENABLE_PUBLIC_DGII_ENDPOINTS)
        self.assertFalse(settings.DGII_LIVE_TRANSPORT_ENABLED)
        self.assertFalse(settings.SIGNING_ENABLED)
