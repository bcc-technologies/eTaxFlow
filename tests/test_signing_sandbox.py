from pathlib import Path
from xml.etree import ElementTree as ET

from django.test import SimpleTestCase

from ecf.services.signing_placeholder import attempt_real_signing
from ecf.services.signing_sandbox import (
    TEST_ONLY_SIGNATURE,
    SandboxSigningError,
    sandbox_signature_diagnostics,
    sign_xml_sandbox,
    verify_xml_sandbox_signature,
)


class SigningSandboxTests(SimpleTestCase):
    unsigned_xml = b"<ECF><Body>test-only</Body></ECF>"

    def test_sandbox_signing_creates_verifiable_signature(self):
        signed = sign_xml_sandbox(self.unsigned_xml, test_only=True)
        root = ET.fromstring(signed)
        self.assertIsNotNone(
            root.find("{http://www.w3.org/2000/09/xmldsig#}Signature")
        )
        self.assertTrue(verify_xml_sandbox_signature(signed, test_only=True))
        diagnostics = sandbox_signature_diagnostics(signed)
        self.assertEqual(diagnostics["signature_status"], TEST_ONLY_SIGNATURE)
        self.assertTrue(diagnostics["signature_present"])
        self.assertEqual(diagnostics["compliance_status"], "NOT_DGII_COMPLIANT")
        self.assertFalse(diagnostics["dgii_submission_allowed"])
        self.assertIsNone(diagnostics["track_id"])

    def test_unsigned_input_remains_unsigned_until_sandbox_operation(self):
        root = ET.fromstring(self.unsigned_xml)
        self.assertIsNone(
            root.find("{http://www.w3.org/2000/09/xmldsig#}Signature")
        )
        signed = sign_xml_sandbox(self.unsigned_xml, test_only=True)
        self.assertNotEqual(signed, self.unsigned_xml)

    def test_real_or_implicit_non_test_signing_is_blocked(self):
        with self.assertRaises(SandboxSigningError):
            sign_xml_sandbox(self.unsigned_xml, test_only=False)
        with self.assertRaises(SandboxSigningError):
            verify_xml_sandbox_signature(self.unsigned_xml, test_only=False)
        with self.assertRaises(NotImplementedError):
            attempt_real_signing(self.unsigned_xml)

    def test_no_key_files_or_secret_markers_are_present(self):
        repo_root = Path(__file__).resolve().parents[1]
        fixture_dir = repo_root / "tests" / "fixtures" / "signing"
        committed_like_files = [
            path
            for path in fixture_dir.rglob("*")
            if path.is_file() and path.suffix.lower() in {".pem", ".key", ".p12", ".pfx"}
        ]
        self.assertEqual(committed_like_files, [])
        source = (repo_root / "ecf" / "services" / "signing_sandbox.py").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("-----BEGIN PRIVATE KEY-----", source)
        self.assertNotIn("-----BEGIN CERTIFICATE-----", source)

    def test_sandbox_does_not_log_secret_material(self):
        signed = sign_xml_sandbox(self.unsigned_xml, test_only=True)
        rendered = signed.decode("utf-8")
        self.assertNotIn("PRIVATE KEY", rendered)
        self.assertNotIn("passphrase", rendered.lower())
        self.assertNotIn("TEST ONLY KEY", rendered)
