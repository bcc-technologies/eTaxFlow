from datetime import date
from decimal import Decimal
from xml.etree import ElementTree as ET

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from django.test.utils import captured_stdout

from audit.models import AuditEvent
from contacts.models import Contact
from documents.models import Document
from ecf.dgii.xml_preview.documents import generate_tipo31_preview_document
from ecf.dgii.xml_preview.tipo_ecf_31_preview import (
    Tipo31XmlPreviewError,
    build_tipo31_xml_preview,
)
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


class Tipo31XmlPreviewBase(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="t31prev", password="x")
        self.issuer = Organization.objects.create(
            legal_name="BCC Preview Issuer",
            commercial_name="BCC",
            rnc="1310000301",
            address="Calle Preview 1",
            phone="8090000001",
            email="issuer-preview@example.com",
        )
        self.customer = Contact.objects.create(
            contact_type="CLIENT",
            legal_name="Preview Client",
            rnc_or_id="123456801",
            address="Calle Cliente 1",
            email="client-preview@example.com",
            id_type="RNC",
        )
        self.fiscal31 = FiscalDocumentType.objects.create(
            code="31",
            name="Factura de Crédito Fiscal Electrónica",
            document_group="INVOICE",
            direction="OUTBOUND",
        )
        self.fiscal32 = FiscalDocumentType.objects.create(
            code="32",
            name="Factura de Consumo Electrónica",
            document_group="INVOICE",
            direction="OUTBOUND",
        )
        self.income = FiscalIncomeType.objects.create(code="01", name="Ingresos por operaciones")
        self.payment = PaymentType.objects.create(code="1", name="Contado")
        self.billing = BillingIndicator.objects.create(code="1", name="Gravado ITBIS")
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
        self.product = ProductService.objects.create(
            code="SVC-PREV",
            name="Original Service Name",
            item_type="SERVICE",
            default_unit_price=Decimal("100.00"),
        )
        self.invoice = Invoice.objects.create(
            issuer=self.issuer,
            customer=self.customer,
            invoice_direction="OUTBOUND",
            lifecycle_status="DRAFT",
            currency="DOP",
            issue_date=date(2026, 1, 15),
            due_date=date(2026, 2, 15),
            created_by=self.user,
            internal_code="BCC-AR-2026-002001",
            fiscal_document_type_ref=self.fiscal31,
            income_type=self.income,
            payment_type=self.payment,
            sequence_expiration_date=date(2030, 12, 31),
        )
        self.line1 = InvoiceLine.objects.create(
            invoice=self.invoice,
            line_order=2,
            product_service=self.product,
            description="Line B",
            quantity=Decimal("1.00"),
            unit_price=Decimal("50.00"),
            tax_amount=Decimal("9.00"),
            line_total=Decimal("59.00"),
            billing_indicator=self.billing,
            item_name_snapshot="Original Service Name",
            item_code_snapshot="SVC-PREV",
            unit_snapshot="UND",
            tax_rate_snapshot="ITBIS18",
            currency_snapshot="DOP",
        )
        self.line2 = InvoiceLine.objects.create(
            invoice=self.invoice,
            line_order=1,
            product_service=self.product,
            description="Line A",
            quantity=Decimal("2.00"),
            unit_price=Decimal("25.00"),
            tax_amount=Decimal("9.00"),
            line_total=Decimal("59.00"),
            billing_indicator=self.billing,
            item_name_snapshot="Original Service Name",
            item_code_snapshot="SVC-PREV",
            unit_snapshot="UND",
            tax_rate_snapshot="ITBIS18",
            currency_snapshot="DOP",
        )
        self.invoice.refresh_from_db()
        allocate_next_encf(self.invoice, allow_demo=True)
        self.invoice.refresh_from_db()
        prepare_signing_placeholder(
            self.invoice,
            actor=self.user,
            note="Local placeholder only; no real digital signature",
        )
        self.invoice.refresh_from_db()

    def _xml_root(self, xml_bytes: bytes) -> ET.Element:
        return ET.fromstring(xml_bytes)


class Tipo31XmlPreviewValidationTests(Tipo31XmlPreviewBase):
    def test_refuses_non_tipo_31_invoice(self):
        self.invoice.fiscal_document_type_ref = self.fiscal32
        self.invoice.save(update_fields=["fiscal_document_type_ref"])
        with self.assertRaises(Tipo31XmlPreviewError) as ctx:
            build_tipo31_xml_preview(self.invoice, allow_demo_encf=True)
        self.assertTrue(any("31" in m for m in ctx.exception.messages))

    def test_refuses_without_official_encf(self):
        self.invoice.official_encf = None
        self.invoice.save(update_fields=["official_encf"])
        with self.assertRaises(Tipo31XmlPreviewError) as ctx:
            build_tipo31_xml_preview(self.invoice, allow_demo_encf=True)
        self.assertTrue(any("official_encf" in m for m in ctx.exception.messages))

    def test_refuses_demo_encf_unless_allowed(self):
        with self.assertRaises(Tipo31XmlPreviewError) as ctx:
            build_tipo31_xml_preview(self.invoice, allow_demo_encf=False)
        self.assertTrue(any("allow_demo_encf" in m for m in ctx.exception.messages))

    def test_requires_sequence_expiration_date(self):
        self.invoice.sequence_expiration_date = None
        self.invoice.save(update_fields=["sequence_expiration_date"])
        with self.assertRaises(Tipo31XmlPreviewError) as ctx:
            build_tipo31_xml_preview(self.invoice, allow_demo_encf=True)
        self.assertTrue(any("sequence_expiration_date" in m for m in ctx.exception.messages))

    def test_requires_income_type(self):
        self.invoice.income_type = None
        self.invoice.save(update_fields=["income_type"])
        with self.assertRaises(Tipo31XmlPreviewError) as ctx:
            build_tipo31_xml_preview(self.invoice, allow_demo_encf=True)
        self.assertTrue(any("income_type" in m for m in ctx.exception.messages))

    def test_requires_payment_type(self):
        self.invoice.payment_type = None
        self.invoice.save(update_fields=["payment_type"])
        with self.assertRaises(Tipo31XmlPreviewError) as ctx:
            build_tipo31_xml_preview(self.invoice, allow_demo_encf=True)
        self.assertTrue(any("payment_type" in m for m in ctx.exception.messages))

    def test_requires_billing_indicator_on_all_lines(self):
        self.line1.billing_indicator = None
        self.line1.save(update_fields=["billing_indicator"])
        with self.assertRaises(Tipo31XmlPreviewError) as ctx:
            build_tipo31_xml_preview(self.invoice, allow_demo_encf=True)
        self.assertTrue(any("billing_indicator" in m for m in ctx.exception.messages))

    def test_requires_signing_placeholder_when_configured(self):
        ECFDocument.objects.filter(invoice=self.invoice).delete()
        with self.assertRaises(Tipo31XmlPreviewError) as ctx:
            build_tipo31_xml_preview(
                self.invoice,
                allow_demo_encf=True,
                require_signing_placeholder=True,
            )
        self.assertTrue(any("Signing placeholder" in m for m in ctx.exception.messages))


class Tipo31XmlPreviewBuilderTests(Tipo31XmlPreviewBase):
    def test_root_includes_not_dgii_compliant(self):
        xml_bytes = build_tipo31_xml_preview(self.invoice, allow_demo_encf=True)
        root = self._xml_root(xml_bytes)
        self.assertEqual(root.tag, "ETaxFlowTipo31EcfPreview")
        self.assertEqual(root.attrib.get("dgii_compliance"), "NOT_DGII_COMPLIANT")
        self.assertIn(b'dgii_compliance="NOT_DGII_COMPLIANT"', xml_bytes)

    def test_root_includes_xml_signature_not_implemented(self):
        xml_bytes = build_tipo31_xml_preview(self.invoice, allow_demo_encf=True)
        root = self._xml_root(xml_bytes)
        self.assertEqual(root.attrib.get("xml_signature"), "NOT_IMPLEMENTED")
        self.assertEqual(root.attrib.get("signature_field"), "MISSING")

    def test_contains_no_fake_signature_value(self):
        xml_bytes = build_tipo31_xml_preview(self.invoice, allow_demo_encf=True)
        text = xml_bytes.decode("utf-8")
        self.assertNotIn("<Signature>", text)
        self.assertNotIn("</Signature>", text)
        self.assertNotIn("SignedInfo", text)
        self.assertNotIn("http://www.w3.org/2000/09/xmldsig#", text)

    def test_signature_missing_diagnostic_only(self):
        xml_bytes = build_tipo31_xml_preview(self.invoice, allow_demo_encf=True)
        root = self._xml_root(xml_bytes)
        sig = root.find("SignaturePreview")
        self.assertIsNotNone(sig)
        self.assertEqual(sig.findtext("Status"), "MISSING")
        self.assertEqual(sig.findtext("Implemented"), "false")
        self.assertEqual(sig.findtext("XMLDSig"), "NOT_IMPLEMENTED")
        missing_fields = [
            el.text for el in root.findall("PreviewMetadata/MissingRequiredFields/Field")
        ]
        self.assertIn("Signature", missing_fields)

    def test_includes_fechahorafirma_from_ecf_signature_datetime(self):
        ecf = self.invoice.ecf_document
        xml_bytes = build_tipo31_xml_preview(self.invoice, allow_demo_encf=True)
        root = self._xml_root(xml_bytes)
        fecha = root.find("FechaHoraFirmaPreview/FechaHoraFirma")
        self.assertIsNotNone(fecha)
        expected = ecf.signature_datetime.strftime("%d-%m-%Y %H:%M:%S")
        self.assertEqual(fecha.text, expected)

    def test_includes_encf_from_invoice(self):
        xml_bytes = build_tipo31_xml_preview(self.invoice, allow_demo_encf=True)
        root = self._xml_root(xml_bytes)
        self.assertEqual(
            root.findtext("EncabezadoPreview/eNCF"),
            self.invoice.official_encf,
        )

    def test_includes_demo_or_unauthorized_encf_warning(self):
        xml_bytes = build_tipo31_xml_preview(self.invoice, allow_demo_encf=True)
        root = self._xml_root(xml_bytes)
        warnings = [el.text for el in root.findall("PreviewMetadata/Warnings/Warning")]
        self.assertIn("DEMO_OR_UNAUTHORIZED_ENCF", warnings)

    def test_deterministic_across_repeated_calls(self):
        a = build_tipo31_xml_preview(self.invoice, allow_demo_encf=True)
        b = build_tipo31_xml_preview(self.invoice, allow_demo_encf=True)
        self.assertEqual(a, b)

    def test_line_order_is_deterministic(self):
        xml_bytes = build_tipo31_xml_preview(self.invoice, allow_demo_encf=True)
        root = self._xml_root(xml_bytes)
        line_orders = [
            el.findtext("NumeroLinea")
            for el in root.findall("DetallesItemsPreview/ItemPreview")
        ]
        self.assertEqual(line_orders, ["1", "2"])

    def test_product_service_changes_do_not_mutate_line_snapshots(self):
        before = build_tipo31_xml_preview(self.invoice, allow_demo_encf=True)
        self.product.name = "Mutated Product Name After Snapshot"
        self.product.save(update_fields=["name"])
        after = build_tipo31_xml_preview(self.invoice, allow_demo_encf=True)
        self.assertEqual(before, after)
        root = self._xml_root(after)
        names = [
            el.findtext("NombreItem")
            for el in root.findall("DetallesItemsPreview/ItemPreview")
        ]
        self.assertTrue(all(n == "Original Service Name" for n in names))
        self.assertNotIn("Mutated Product Name After Snapshot", after.decode("utf-8"))


class Tipo31XmlPreviewDocumentTests(Tipo31XmlPreviewBase):
    def test_generate_creates_document_linked_with_hash(self):
        before_ecf = ECFDocument.objects.filter(invoice=self.invoice).count()
        before_track = self.invoice.ecf_document.dgii_track_id
        before_signed = bool(self.invoice.ecf_document.xml_signed_file)

        document, created = generate_tipo31_preview_document(
            self.invoice,
            created_by=self.user,
            allow_demo_encf=True,
        )
        self.assertTrue(created)
        self.assertEqual(document.document_kind, "XML")
        self.assertEqual(document.source, "GENERATED")
        self.assertEqual(document.related_invoice_id, self.invoice.pk)
        self.assertTrue(document.sha256_hash)
        self.assertEqual(len(document.sha256_hash), 64)
        self.assertEqual(
            document.original_filename,
            f"tipo31-preview-{self.invoice.internal_code}.xml",
        )
        self.assertEqual(ECFDocument.objects.filter(invoice=self.invoice).count(), before_ecf)
        self.invoice.ecf_document.refresh_from_db()
        self.assertEqual(self.invoice.ecf_document.dgii_track_id, before_track)
        self.assertIsNone(self.invoice.ecf_document.dgii_track_id)
        self.assertEqual(bool(self.invoice.ecf_document.xml_signed_file), before_signed)
        self.assertFalse(self.invoice.ecf_document.xml_signed_file)

    def test_repeated_generation_reuses_identical_document(self):
        first, created1 = generate_tipo31_preview_document(
            self.invoice, created_by=self.user, allow_demo_encf=True
        )
        second, created2 = generate_tipo31_preview_document(
            self.invoice, created_by=self.user, allow_demo_encf=True
        )
        self.assertTrue(created1)
        self.assertFalse(created2)
        self.assertEqual(first.pk, second.pk)
        self.assertEqual(
            Document.objects.filter(
                related_invoice=self.invoice,
                original_filename=f"tipo31-preview-{self.invoice.internal_code}.xml",
            ).count(),
            1,
        )

    def test_changed_invoice_content_creates_new_document(self):
        first, _ = generate_tipo31_preview_document(
            self.invoice, created_by=self.user, allow_demo_encf=True
        )
        self.line2.unit_price = Decimal("30.00")
        self.line2.save()
        self.invoice.refresh_from_db()
        second, created = generate_tipo31_preview_document(
            self.invoice, created_by=self.user, allow_demo_encf=True
        )
        self.assertTrue(created)
        self.assertNotEqual(first.pk, second.pk)
        self.assertNotEqual(first.sha256_hash, second.sha256_hash)

    def test_audit_event_created(self):
        document, _ = generate_tipo31_preview_document(
            self.invoice, created_by=self.user, allow_demo_encf=True
        )
        event = AuditEvent.objects.filter(
            event_type="tipo31_xml_preview_generated",
            entity_type="Invoice",
            entity_id=self.invoice.pk,
        ).latest("id")
        self.assertEqual(event.metadata.get("document_id"), document.pk)
        self.assertEqual(event.metadata.get("sha256"), document.sha256_hash)
        self.assertTrue(event.metadata.get("allow_demo_encf"))
        self.assertEqual(event.metadata.get("compliance_status"), "NOT_DGII_COMPLIANT")


class Tipo31XmlPreviewCommandTests(Tipo31XmlPreviewBase):
    def test_stdout_prints_xml_and_creates_no_document(self):
        before = Document.objects.filter(
            related_invoice=self.invoice,
            original_filename=f"tipo31-preview-{self.invoice.internal_code}.xml",
        ).count()
        # Do not pass stdout= to call_command: --stdout maps from keyword "stdout".
        with captured_stdout() as out:
            call_command(
                "generate_tipo31_preview_xml",
                internal_code=self.invoice.internal_code,
                allow_demo_encf=True,
                stdout_flag=True,
            )
        output = out.getvalue()
        self.assertIn("<ETaxFlowTipo31EcfPreview", output)
        self.assertIn('dgii_compliance="NOT_DGII_COMPLIANT"', output)
        after = Document.objects.filter(
            related_invoice=self.invoice,
            original_filename=f"tipo31-preview-{self.invoice.internal_code}.xml",
        ).count()
        self.assertEqual(before, after)

    def test_save_creates_or_reuses_document(self):
        with captured_stdout() as out1:
            call_command(
                "generate_tipo31_preview_xml",
                internal_code=self.invoice.internal_code,
                allow_demo_encf=True,
            )
        self.assertIn("Created Tipo 31 XML preview Document", out1.getvalue())
        docs = Document.objects.filter(
            related_invoice=self.invoice,
            original_filename=f"tipo31-preview-{self.invoice.internal_code}.xml",
        )
        self.assertEqual(docs.count(), 1)
        with captured_stdout() as out2:
            call_command(
                "generate_tipo31_preview_xml",
                internal_code=self.invoice.internal_code,
                allow_demo_encf=True,
            )
        self.assertIn("Reused Tipo 31 XML preview Document", out2.getvalue())
        self.assertEqual(docs.count(), 1)

    def test_command_refuses_demo_without_flag(self):
        with self.assertRaises(CommandError):
            call_command(
                "generate_tipo31_preview_xml",
                internal_code=self.invoice.internal_code,
            )

    def test_preview_generation_does_not_create_ecf_or_trackid_or_signed_xml(self):
        ECFDocument.objects.filter(invoice=self.invoice).delete()
        # Recreate placeholder so validation passes when required.
        prepare_signing_placeholder(self.invoice, actor=self.user)
        before_count = ECFDocument.objects.count()
        generate_tipo31_preview_document(self.invoice, allow_demo_encf=True)
        self.assertEqual(ECFDocument.objects.count(), before_count)
        ecf = self.invoice.ecf_document
        self.assertIsNone(ecf.dgii_track_id)
        self.assertFalse(ecf.xml_signed_file)
