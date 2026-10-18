from pathlib import Path

from django.test import SimpleTestCase


ROOT = Path(__file__).resolve().parents[1]


class StagingDeploymentDocumentationTests(SimpleTestCase):
    def test_required_staging_documents_exist(self):
        for relative_path in (
            "docs/deployment/STAGING_DEPLOYMENT_PLAN.md",
            "docs/deployment/ENVIRONMENT_VARIABLES.md",
            "docs/deployment/SECURITY_BASELINE.md",
            "docs/deployment/RENDER_STAGING_DEPLOYMENT.md",
            ".env.staging.example",
        ):
            self.assertTrue((ROOT / relative_path).is_file(), relative_path)

    def test_staging_example_is_placeholder_only(self):
        content = (ROOT / ".env.staging.example").read_text()
        self.assertIn("DGII_LIVE_TRANSPORT_ENABLED=false", content)
        self.assertIn("SIGNING_ENABLED=false", content)
        self.assertIn("SIGNING_KEY_PATH=", content)
        self.assertNotIn("BEGIN PRIVATE KEY", content)
        self.assertNotIn("BEGIN CERTIFICATE", content)
        self.assertNotIn("password=", content.lower())
        self.assertNotIn("token=", content.lower())
        self.assertNotIn("rnc=", content.lower())
