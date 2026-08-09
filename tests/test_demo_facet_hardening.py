"""Phase 013 — seed/demo XSD facet hardening (local only; NOT DGII compliant)."""

from __future__ import annotations

import json
from io import StringIO

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from django.test.utils import captured_stdout

from contacts.models import Contact
from core.demo_profiles import (
    DEMO_XSD_FACET_CUSTOMER_RNC,
    DEMO_XSD_FACET_ENCF_PREFIX,
    DEMO_XSD_FACET_ISSUER_RNC,
)
from core.seed_demo import (
    DEMO_CLIENT_RNC,
    DEMO_ISSUER_LEGAL_NAME,
    DEMO_ISSUER_RNC,
    DEMO_SUPPLIER_RNC,
    LEGACY_DEMO_ISSUER_RNCS,
    SEED_INVOICE_MARKER,
)
from documents.models import Document
from ecf.dgii.mapping import build_invoice_dgii_mapping_report
from ecf.dgii.xsd.facets import (
    encf_matches_xsd_facet,
    extract_tipo31_xsd_facets,
    rnc_matches_xsd_facet,
)
from ecf.dgii.xsd.tipo31_unsigned_validation import (
    ERROR_GROUP_DEMO_FACET,
    ERROR_GROUP_SIGNATURE,
    ERROR_GROUP_STRUCTURAL_MISSING,
    ERROR_GROUP_STRUCTURAL_ORDER,
    ERROR_GROUP_STRUCTURAL_TYPE,
    ERROR_GROUP_STRUCTURAL_UNEXPECTED,
    classify_xsd_validation_error,
    validate_tipo31_unsigned_draft,
)
from ecf.models import ECFDocument
from ecf.services.signing_placeholder import prepare_signing_placeholder
from fiscal.models import ENCFSequenceRange
from fiscal.services.encf_sequences import allocate_next_encf
from invoicing.models import Invoice
from organizations.models import Organization


class Tipo31XSDFacetExtractionTests(TestCase):
    def test_extracts_rnc_pattern(self):
        facets = extract_tipo31_xsd_facets()
        self.assertEqual(facets["RNC"]["type_name"], "RNCValidationType")
        self.assertEqual(facets["RNC"]["pattern"], "[0-9]{11}|[0-9]{9}")
        self.assertTrue(rnc_matches_xsd_facet(DEMO_XSD_FACET_ISSUER_RNC, facets))
        self.assertFalse(rnc_matches_xsd_facet("1310000000", facets))

    def test_extracts_encf_pattern(self):
        facets = extract_tipo31_xsd_facets()
        self.assertEqual(facets["eNCF"]["type_name"], "eNCFValidationType")
        self.assertEqual(facets["eNCF"]["pattern"], "([a-z0-9A-Z]{13})")
        self.assertEqual(facets["eNCF"]["min_length"], "13")
        self.assertEqual(facets["eNCF"]["max_length"], "13")
        self.assertTrue(encf_matches_xsd_facet("E319000000001", facets))
        self.assertFalse(encf_matches_xsd_facet("DEMO-E31-000001", facets))


class SeedBccFacetHardeningTests(TestCase):
    def test_seed_creates_pattern_compatible_issuer_and_customer_rncs(self):
        call_command("seed_bcc")
        issuer = Organization.objects.get(rnc=DEMO_ISSUER_RNC, is_default_issuer=True)
        self.assertEqual(issuer.rnc, DEMO_XSD_FACET_ISSUER_RNC)
        self.assertTrue(rnc_matches_xsd_facet(issuer.rnc))
        client = Contact.objects.filter(
            contact_type="CLIENT", rnc_or_id=DEMO_CLIENT_RNC
        ).order_by("pk").first()
        self.assertIsNotNone(client)
        self.assertEqual(client.rnc_or_id, DEMO_XSD_FACET_CUSTOMER_RNC)
        self.assertTrue(rnc_matches_xsd_facet(client.rnc_or_id))
        supplier = Contact.objects.filter(
            contact_type="SUPPLIER", rnc_or_id=DEMO_SUPPLIER_RNC
        ).order_by("pk").first()
        self.assertIsNotNone(supplier)
        self.assertTrue(rnc_matches_xsd_facet(supplier.rnc_or_id))

    def test_seed_bcc_idempotent_with_facet_values(self):
        call_command("seed_bcc")
        call_command("seed_bcc")
        self.assertEqual(
            Organization.objects.filter(rnc=DEMO_ISSUER_RNC, is_default_issuer=True).count(),
            1,
        )
        self.assertEqual(
            ENCFSequenceRange.objects.filter(
                prefix=DEMO_XSD_FACET_ENCF_PREFIX, source="XSD_FACET_DEMO"
            ).count(),
            1,
        )
        self.assertEqual(
            ENCFSequenceRange.objects.filter(prefix="DEMO-E31-", source="MANUAL_DEMO").count(),
            1,
        )

    def test_seed_migrates_owned_legacy_issuer_rnc(self):
        legacy = next(iter(LEGACY_DEMO_ISSUER_RNCS))
        Organization.objects.create(
            legal_name=DEMO_ISSUER_LEGAL_NAME,
            commercial_name="BCC Technologies",
            rnc=legacy,
            is_default_issuer=True,
        )
        call_command("seed_bcc")
        self.assertFalse(
            Organization.objects.filter(rnc=legacy, is_default_issuer=True).exists()
        )
        self.assertTrue(
            Organization.objects.filter(rnc=DEMO_ISSUER_RNC, is_default_issuer=True).exists()
        )

    def test_non_demo_org_with_invalid_rnc_is_not_overwritten(self):
        dirty = Organization.objects.create(
            legal_name="External Dirty Org SRL",
            commercial_name="Dirty",
            rnc="1310000000",
            is_default_issuer=False,
        )
        out = StringIO()
        call_command("seed_bcc", stdout=out)
        dirty.refresh_from_db()
        self.assertEqual(dirty.rnc, "1310000000")
        self.assertIn("Non-demo Organization", out.getvalue())
        self.assertIn("left unchanged", out.getvalue())

    def test_xsd_facet_demo_encf_range_is_seeded(self):
        call_command("seed_bcc")
        seq = ENCFSequenceRange.objects.get(
            prefix=DEMO_XSD_FACET_ENCF_PREFIX, source="XSD_FACET_DEMO"
        )
        self.assertFalse(seq.is_authorized_by_dgii)
        self.assertEqual(seq.environment, "DEV")
        self.assertTrue(seq.is_xsd_facet_demo)
        self.assertTrue(seq.is_demo_or_unauthorized)
        sample = f"{seq.prefix}{str(seq.next_number).zfill(seq.number_pad_width)}"
        self.assertTrue(encf_matches_xsd_facet(sample))


class AllocateXsdFacetDemoTests(TestCase):
    def setUp(self):
        call_command("seed_bcc")
        self.invoice = Invoice.objects.filter(notes__icontains=SEED_INVOICE_MARKER).get()

    def test_xsd_facet_demo_apply_requires_allow_demo(self):
        with self.assertRaises(CommandError):
            call_command(
                "allocate_demo_encf",
                internal_code=self.invoice.internal_code,
                xsd_facet_demo=True,
                apply=True,
            )

    def test_xsd_facet_demo_allocates_pattern_compatible_non_authorized_encf(self):
        before_docs = Document.objects.count()
        before_ecf = ECFDocument.objects.count()
        out = StringIO()
        call_command(
            "allocate_demo_encf",
            internal_code=self.invoice.internal_code,
            xsd_facet_demo=True,
            allow_demo=True,
            apply=True,
            stdout=out,
        )
        self.invoice.refresh_from_db()
        self.assertTrue(encf_matches_xsd_facet(self.invoice.official_encf))
        self.assertTrue(self.invoice.official_encf.startswith(DEMO_XSD_FACET_ENCF_PREFIX))
        self.assertIn("NOT DGII-authorized", out.getvalue())
        seq = ENCFSequenceRange.objects.get(source="XSD_FACET_DEMO", prefix=DEMO_XSD_FACET_ENCF_PREFIX)
        self.assertFalse(seq.is_authorized_by_dgii)
        self.assertEqual(seq.environment, "DEV")
        self.assertEqual(Document.objects.count(), before_docs)
        self.assertEqual(ECFDocument.objects.count(), before_ecf)

    def test_mapping_warns_demo_encf_even_when_pattern_compatible(self):
        allocate_next_encf(self.invoice, allow_demo=True, xsd_facet_demo=True)
        self.invoice.refresh_from_db()
        self.assertTrue(encf_matches_xsd_facet(self.invoice.official_encf))
        report = build_invoice_dgii_mapping_report(self.invoice)
        codes = {i.code for i in report.issues}
        self.assertIn("DEMO_OR_UNAUTHORIZED_ENCF", codes)
        self.assertIn("NOT_DGII_COMPLIANT", report.compliance_claim)


class ValidationErrorGroupingTests(TestCase):
    def test_classify_signature_as_expected_unsigned_gap(self):
        msg = (
            "Element 'ECF': Missing child element(s). Expected is one of "
            "( {http://www.w3.org/2000/09/xmldsig#}* )."
        )
        self.assertEqual(classify_xsd_validation_error(msg), ERROR_GROUP_SIGNATURE)

    def test_classify_demo_facet_separately(self):
        self.assertEqual(
            classify_xsd_validation_error(
                "Element 'eNCF': [facet 'pattern'] The value 'DEMO-E31-000001' "
                "is not accepted by the pattern '([a-z0-9A-Z]{13})'."
            ),
            ERROR_GROUP_DEMO_FACET,
        )

    def test_classify_structural_categories_separately(self):
        self.assertEqual(
            classify_xsd_validation_error(
                "Element 'ECF': Missing child element(s). Expected is one of ( 'Totales' )."
            ),
            ERROR_GROUP_STRUCTURAL_MISSING,
        )
        self.assertEqual(
            classify_xsd_validation_error(
                "Element 'FechaHoraFirma': This element is not expected. Expected is ( 'Totales' )."
            ),
            ERROR_GROUP_STRUCTURAL_ORDER,
        )
        self.assertEqual(
            classify_xsd_validation_error(
                "Unexpected element 'Unexpected': extra content."
            ),
            ERROR_GROUP_STRUCTURAL_UNEXPECTED,
        )
        self.assertEqual(
            classify_xsd_validation_error(
                "Element 'MontoTotal': The value is invalid for the declared type."
            ),
            ERROR_GROUP_STRUCTURAL_TYPE,
        )
        self.assertEqual(
            classify_xsd_validation_error(
                "Element 'RNCEmisor': [facet 'pattern'] The value '1310000000' "
                "is not accepted by the pattern '[0-9]{11}|[0-9]{9}'."
            ),
            ERROR_GROUP_DEMO_FACET,
        )

    def test_avoidable_facet_errors_decrease_after_facet_safe_seed_and_allocation(self):
        call_command("seed_bcc")
        invoice = Invoice.objects.filter(notes__icontains=SEED_INVOICE_MARKER).get()

        # Baseline: classic DEMO-E31- eNCF + facet-safe issuer RNC after seed.
        allocate_next_encf(invoice, allow_demo=True, xsd_facet_demo=False)
        invoice.refresh_from_db()
        prepare_signing_placeholder(
            invoice,
            note="Local placeholder only; no real digital signature",
        )
        invoice.refresh_from_db()
        before = validate_tipo31_unsigned_draft(invoice, allow_demo_encf=True)
        self.assertGreaterEqual(before.avoidable_demo_facet_error_count, 1)
        self.assertGreaterEqual(before.intentional_unsigned_error_count, 1)
        self.assertEqual(before.compliance_status, "NOT_DGII_COMPLIANT")
        self.assertFalse(before.signature_present)

        # Re-seed clears official_encf on owned demo invoice; allocate facet-safe.
        call_command("seed_bcc")
        invoice.refresh_from_db()
        self.assertIsNone(invoice.official_encf)
        allocate_next_encf(invoice, allow_demo=True, xsd_facet_demo=True)
        invoice.refresh_from_db()
        prepare_signing_placeholder(
            invoice,
            note="Local placeholder only; no real digital signature",
        )
        invoice.refresh_from_db()

        before_docs = Document.objects.count()
        before_ecf = ECFDocument.objects.count()
        after = validate_tipo31_unsigned_draft(invoice, allow_demo_encf=True)

        self.assertLess(
            after.avoidable_demo_facet_error_count,
            before.avoidable_demo_facet_error_count,
        )
        self.assertEqual(after.avoidable_demo_facet_error_count, 0)
        self.assertGreaterEqual(after.intentional_unsigned_error_count, 1)
        self.assertEqual(after.compliance_status, "NOT_DGII_COMPLIANT")
        self.assertFalse(after.signature_present)
        self.assertFalse(after.is_valid)
        self.assertIn(
            ERROR_GROUP_SIGNATURE,
            after.error_groups,
        )
        self.assertGreaterEqual(len(after.error_groups[ERROR_GROUP_SIGNATURE]), 1)
        self.assertEqual(Document.objects.count(), before_docs)
        self.assertEqual(ECFDocument.objects.count(), before_ecf)
        invoice.ecf_document.refresh_from_db()
        self.assertIsNone(invoice.ecf_document.dgii_track_id)
        self.assertFalse(invoice.ecf_document.xml_signed_file)

    def test_validate_command_json_includes_grouped_counts(self):
        call_command("seed_bcc")
        invoice = Invoice.objects.filter(notes__icontains=SEED_INVOICE_MARKER).get()
        allocate_next_encf(invoice, allow_demo=True, xsd_facet_demo=True)
        invoice.refresh_from_db()
        prepare_signing_placeholder(
            invoice,
            note="Local placeholder only; no real digital signature",
        )
        with captured_stdout() as out:
            call_command(
                "validate_tipo31_unsigned_draft",
                internal_code=invoice.internal_code,
                allow_demo_encf=True,
                json_flag=True,
            )
        payload = json.loads(out.getvalue())
        self.assertIn("avoidable_demo_facet_error_count", payload)
        self.assertIn("intentional_unsigned_error_count", payload)
        self.assertIn("error_groups", payload)
        self.assertIn("non_signature_structural_mismatch_count", payload)
        self.assertIn("signature_missing_expected_count", payload)
        self.assertIn("facet_mismatch_count", payload)
        self.assertIn("xsd_stub_informational_count", payload)
        self.assertIn("unsigned_body_structurally_aligned_except_signature", payload)
        self.assertEqual(payload["avoidable_demo_facet_error_count"], 0)
        self.assertEqual(payload["facet_mismatch_count"], 0)
        self.assertGreaterEqual(payload["intentional_unsigned_error_count"], 1)
        self.assertEqual(payload["signature_missing_expected_count"], 1)
        self.assertEqual(payload["non_signature_structural_mismatch_count"], 0)
        self.assertTrue(payload["unsigned_body_structurally_aligned_except_signature"])
        self.assertEqual(payload["compliance_status"], "NOT_DGII_COMPLIANT")
        self.assertFalse(payload["signature_present"])
