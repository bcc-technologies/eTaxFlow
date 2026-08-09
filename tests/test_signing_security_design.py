from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase

from ecf.models import ECFDocument
from ecf.services.signing_placeholder import attempt_real_signing


class SigningSecurityDesignTests(SimpleTestCase):
    def test_signing_defaults_are_disabled_and_test_safe(self):
        self.assertEqual(settings.SIGNING_MODE, "DISABLED")
        self.assertEqual(settings.SIGNING_BACKEND, "NONE")
        self.assertFalse(settings.SIGNING_ENABLED)
        self.assertFalse(settings.SIGNING_ALLOW_TEST_ONLY)
        self.assertEqual(settings.SIGNING_CERT_PATH, "")
        self.assertEqual(settings.SIGNING_KEY_PATH, "")
        self.assertEqual(settings.SIGNING_PASS_ENV_VAR, "")

    def test_ecf_document_has_no_key_or_certificate_secret_fields(self):
        field_names = {field.name.lower() for field in ECFDocument._meta.fields}
        forbidden_tokens = (
            "private_key",
            "privatekey",
            "certificate",
            "cert_pem",
            "passphrase",
            "password",
        )
        self.assertFalse(
            any(
                token in field_name
                for field_name in field_names
                for token in forbidden_tokens
            ),
            field_names,
        )

    def test_real_signing_is_blocked(self):
        with self.assertRaises(NotImplementedError):
            attempt_real_signing(b"<ECF />")

    def test_committed_docs_and_defaults_contain_no_secret_material_markers(self):
        repo_root = Path(__file__).resolve().parents[1]
        paths = [repo_root / "README.md", repo_root / "etaxflow" / "settings.py"]
        paths.extend(repo_root.glob("CHECKPOINT_*.md"))
        secret_markers = (
            "-----BEGIN PRIVATE KEY-----",
            "-----BEGIN RSA PRIVATE KEY-----",
            "-----BEGIN CERTIFICATE-----",
            "password=",
            "passphrase=",
            "AWS_SECRET_ACCESS_KEY=",
        )
        for path in paths:
            text = path.read_text(encoding="utf-8")
            for marker in secret_markers:
                self.assertNotIn(marker, text, path.as_posix())
