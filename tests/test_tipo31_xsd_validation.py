import json
import tempfile
from datetime import date
from decimal import Decimal
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.test.utils import captured_stdout

from contacts.models import Contact
from documents.models import Document
from ecf.dgii.xsd.tipo_ecf_31_structure import DEFAULT_XSD_PATH
from ecf.dgii.xsd.tipo31_unsigned_validation import validate_tipo31_unsigned_draft
from ecf.dgii.xsd.validation import lxml_available, validate_xml_bytes_against_xsd
from ecf.models import ECFDocument
from ecf.services.signing_placeholder import prepare_signing_placeholder
from fiscal.models import (
    BillingIndicator,
    ENCFSequenceRange,
    FiscalDocumentType,
    FiscalIncomeType,
    PaymentType,
)
from fiscal.services.encf_sequences import allocate_next_encf
from invoicing.models import Invoice, InvoiceLine, ProductService
from organizations.models import Organization


class XSDValidationModuleTests(TestCase):
    def test_locates_local_ecf_31_xsd(self):
        self.assertTrue(DEFAULT_XSD_PATH.is_file())
        self.assertEqual(DEFAULT_XSD_PATH.as_posix(), "docs/dgii/sources/e-CF_31_v1.0.xsd")

    def test_validator_reports_engine_name(self):
        self.assertTrue(lxml_available())
        result = validate_xml_bytes_against_xsd(b"<ECF/>", DEFAULT_XSD_PATH)
        self.assertEqual(result.validator_engine, "lxml")
        self.assertTrue(result.available)


class Tipo31UnsignedXSDValidationBase(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="t31xsd", password="x")
        self.issuer = Organization.objects.create(
            legal_name="BCC XSD Issuer",
            commercial_name="BCC",
            rnc="1310000501",
            address="Calle XSD 1",
            email="issuer-xsd@example.com",
        )
        self.customer = Contact.objects.create(
            contact_type="CLIENT",
            legal_name="XSD Client",
            rnc_or_id="123457001",
            address="Calle Cliente XSD",
            email="client-xsd@example.com",
        )
        self.fiscal31 = FiscalDocumentType.objects.create(
            code="31",
            name="Factura de Crédito Fiscal Electrónica",
            document_group="INVOICE",
            direction="OUTBOUND",
        )
        self.income = FiscalIncomeType.objects.create(code="01", name="Ingresos")
        self.payment = PaymentType.objects.create(code="1", name="Contado")
        self.billing = BillingIndicator.objects.create(code="1", name="Gravado")
        ENCFSequenceRange.objects.create(
            issuer=self.issuer,
            fiscal_document_type=self.fiscal31,
            prefix="DEMO-E31-",
            start_number=1,
            end_number=100,
            next_number=1,
            number_pad_width=6,
            sequence_expiration_date=date(2030, 12, 31),
            environment="DEV",
            source="MANUAL_DEMO",
            is_authorized_by_dgii=False,
        )
        product = ProductService.objects.create(
            code="SVC-XSD",
            name="XSD Service",
            item_type="SERVICE",
        )
        self.invoice = Invoice.objects.create(
            issuer=self.issuer,
            customer=self.customer,
            invoice_direction="OUTBOUND",
            lifecycle_status="DRAFT",
            currency="DOP",
            issue_date=date(2026, 1, 15),
            created_by=self.user,
            internal_code="BCC-AR-2026-004001",
            fiscal_document_type_ref=self.fiscal31,
            income_type=self.income,
            payment_type=self.payment,
            sequence_expiration_date=date(2030, 12, 31),
        )
        InvoiceLine.objects.create(
            invoice=self.invoice,
            line_order=1,
            product_service=product,
            description="Line",
            quantity=Decimal("1.00"),
            unit_price=Decimal("100.00"),
            tax_amount=Decimal("18.00"),
            line_total=Decimal("118.00"),
            billing_indicator=self.billing,
            item_name_snapshot="XSD Service",
            item_code_snapshot="SVC-XSD",
            unit_snapshot="UND",
            tax_rate_snapshot="ITBIS18",
            currency_snapshot="DOP",
        )
        self.invoice.refresh_from_db()
        allocate_next_encf(self.invoice, allow_demo=True)
        self.invoice.refresh_from_db()
        prepare_signing_placeholder(self.invoice, actor=self.user)
        self.invoice.refresh_from_db()


class Tipo31UnsignedXSDValidationServiceTests(Tipo31UnsignedXSDValidationBase):
    def test_returns_expected_invalid_with_signature_missing(self):
        before_docs = Document.objects.count()
        before_ecf = ECFDocument.objects.count()
        before_track = self.invoice.ecf_document.dgii_track_id

        report = validate_tipo31_unsigned_draft(self.invoice, allow_demo_encf=True)

        self.assertFalse(report.is_valid)
        self.assertFalse(report.expected_validity)
        self.assertTrue(report.expected_invalid_unsigned_draft)
        self.assertEqual(report.compliance_status, "NOT_DGII_COMPLIANT")
        self.assertIn("Signature", report.known_missing_required_fields)
        self.assertFalse(report.signature_present)
        self.assertTrue(report.local_xsd_validation_expected_to_fail)
        self.assertEqual(report.validator_engine, "lxml")
        self.assertGreaterEqual(report.error_count, 1)
        joined_reasons = " ".join(report.expected_failure_reasons)
        self.assertIn("Signature", joined_reasons)
        self.assertEqual(Document.objects.count(), before_docs)
        self.assertEqual(ECFDocument.objects.count(), before_ecf)
        self.invoice.ecf_document.refresh_from_db()
        self.assertEqual(self.invoice.ecf_document.dgii_track_id, before_track)
        self.assertIsNone(self.invoice.ecf_document.dgii_track_id)
        self.assertFalse(self.invoice.ecf_document.xml_signed_file)

    def test_diagnostics_include_local_validation_flags(self):
        from ecf.dgii.xml_draft.tipo_ecf_31_unsigned import (
            build_tipo31_unsigned_draft_diagnostics,
        )

        diag = build_tipo31_unsigned_draft_diagnostics(
            self.invoice, allow_demo_encf=True
        )
        self.assertTrue(diag.local_xsd_validation_available)
        self.assertTrue(diag.local_xsd_validation_expected_to_fail)
        self.assertIn("Signature", diag.expected_failure_reason)
        self.assertEqual(diag.compliance_status, "NOT_DGII_COMPLIANT")


class Tipo31UnsignedXSDValidationCommandTests(Tipo31UnsignedXSDValidationBase):
    def test_human_output_works(self):
        with captured_stdout() as out:
            call_command(
                "validate_tipo31_unsigned_draft",
                internal_code=self.invoice.internal_code,
                allow_demo_encf=True,
            )
        text = out.getvalue()
        self.assertIn("Expected invalid unsigned draft", text)
        self.assertIn("NOT_DGII_COMPLIANT", text)
        self.assertIn("Signature", text)

    def test_json_output_is_parseable(self):
        with captured_stdout() as out:
            call_command(
                "validate_tipo31_unsigned_draft",
                internal_code=self.invoice.internal_code,
                allow_demo_encf=True,
                json_flag=True,
            )
        payload = json.loads(out.getvalue())
        self.assertFalse(payload["is_valid"])
        self.assertEqual(payload["compliance_status"], "NOT_DGII_COMPLIANT")
        self.assertIn("Signature", payload["known_missing_required_fields"])
        self.assertTrue(payload["expected_invalid_unsigned_draft"])

    def test_write_report_writes_markdown(self):
        with tempfile.TemporaryDirectory() as tmp:
            report_path = Path(tmp) / "tipo31_unsigned_validation.md"
            with captured_stdout() as out:
                call_command(
                    "validate_tipo31_unsigned_draft",
                    internal_code=self.invoice.internal_code,
                    allow_demo_encf=True,
                    write_report=str(report_path),
                )
            self.assertTrue(report_path.is_file())
            content = report_path.read_text(encoding="utf-8")
            self.assertIn("NOT_DGII_COMPLIANT", content)
            self.assertIn("Signature", content)
            self.assertIn("expected_invalid_unsigned_draft", content)
            self.assertIn("Wrote Markdown report", out.getvalue())

    def test_command_exits_successfully_for_expected_invalid(self):
        # call_command raises only on CommandError; success returns None.
        result = call_command(
            "validate_tipo31_unsigned_draft",
            internal_code=self.invoice.internal_code,
            allow_demo_encf=True,
        )
        self.assertIsNone(result)
