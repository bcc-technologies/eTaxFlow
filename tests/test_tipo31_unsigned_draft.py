import json
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
from ecf.dgii.xml_draft.documents import generate_tipo31_unsigned_draft_document
from ecf.dgii.xml_draft.tipo_ecf_31_unsigned import (
    Tipo31UnsignedDraftError,
    build_tipo31_unsigned_draft_diagnostics,
    build_tipo31_unsigned_xml_draft,
)
from ecf.dgii.xsd.tipo_ecf_31_structure import (
    extract_tipo31_root_name,
    extract_tipo31_top_level_sequence,
    get_tipo31_xsd_structure_summary,
    load_tipo31_xsd_tree,
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


class Tipo31XsdStructureHelperTests(TestCase):
    def test_loads_local_ecf_31_xsd(self):
        tree = load_tipo31_xsd_tree()
        self.assertIsNotNone(tree.getroot())

    def test_extracts_non_empty_structure_summary(self):
        summary = get_tipo31_xsd_structure_summary()
        self.assertEqual(summary["root_name"], "ECF")
        self.assertGreater(len(summary["top_level_sequence"]), 0)
        self.assertIn("Encabezado", summary["top_level_sequence"])
        self.assertIn("DetallesItems", summary["top_level_sequence"])
        self.assertIn("FechaHoraFirma", summary["top_level_sequence"])
        self.assertGreater(summary["required_path_count"], 0)
        self.assertEqual(extract_tipo31_root_name(), "ECF")
        particles = extract_tipo31_top_level_sequence()
        self.assertTrue(any(p.get("kind") == "any" for p in particles))


class Tipo31UnsignedDraftBase(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="t31usgn", password="x")
        self.issuer = Organization.objects.create(
            legal_name="BCC Unsigned Issuer",
            commercial_name="BCC",
            rnc="1310000401",
            address="Calle Draft 1",
            phone="8090000002",
            email="issuer-draft@example.com",
        )
        self.customer = Contact.objects.create(
            contact_type="CLIENT",
            legal_name="Draft Client",
            rnc_or_id="123456901",
            address="Calle Cliente Draft 1",
            email="client-draft@example.com",
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
            code="SVC-USGN",
            name="Original Draft Service",
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
            internal_code="BCC-AR-2026-003001",
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
            item_name_snapshot="Original Draft Service",
            item_code_snapshot="SVC-USGN",
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
            item_name_snapshot="Original Draft Service",
            item_code_snapshot="SVC-USGN",
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


class Tipo31UnsignedDraftValidationTests(Tipo31UnsignedDraftBase):
    def test_refuses_non_tipo_31_invoice(self):
        self.invoice.fiscal_document_type_ref = self.fiscal32
        self.invoice.save(update_fields=["fiscal_document_type_ref"])
        with self.assertRaises(Tipo31UnsignedDraftError):
            build_tipo31_unsigned_xml_draft(self.invoice, allow_demo_encf=True)

    def test_refuses_without_official_encf(self):
        self.invoice.official_encf = None
        self.invoice.save(update_fields=["official_encf"])
        with self.assertRaises(Tipo31UnsignedDraftError):
            build_tipo31_unsigned_xml_draft(self.invoice, allow_demo_encf=True)

    def test_refuses_demo_encf_unless_allowed(self):
        with self.assertRaises(Tipo31UnsignedDraftError):
            build_tipo31_unsigned_xml_draft(self.invoice, allow_demo_encf=False)

    def test_requires_signing_placeholder_by_default(self):
        ECFDocument.objects.filter(invoice=self.invoice).delete()
        with self.assertRaises(Tipo31UnsignedDraftError):
            build_tipo31_unsigned_xml_draft(self.invoice, allow_demo_encf=True)


class Tipo31UnsignedDraftBuilderTests(Tipo31UnsignedDraftBase):
    def test_uses_source_backed_root(self):
        xml_bytes = build_tipo31_unsigned_xml_draft(self.invoice, allow_demo_encf=True)
        root = self._xml_root(xml_bytes)
        self.assertEqual(root.tag, extract_tipo31_root_name())
        self.assertEqual(root.tag, "ECF")

    def test_schema_root_has_no_preview_compliance_attributes(self):
        xml_bytes = build_tipo31_unsigned_xml_draft(self.invoice, allow_demo_encf=True)
        root = self._xml_root(xml_bytes)
        self.assertNotIn("dgii_compliance", root.attrib)
        self.assertNotIn("NOT_DGII_COMPLIANT", root.attrib.values())
        self.assertNotIn(b'dgii_compliance="NOT_DGII_COMPLIANT"', xml_bytes)

    def test_child_order_matches_xsd_top_level_expectations(self):
        xml_bytes = build_tipo31_unsigned_xml_draft(self.invoice, allow_demo_encf=True)
        root = self._xml_root(xml_bytes)
        emitted = [child.tag for child in list(root)]
        xsd_names = [
            p["name"]
            for p in extract_tipo31_top_level_sequence()
            if p.get("kind") == "element" and p.get("name") in emitted
        ]
        self.assertEqual(emitted, xsd_names)
        self.assertEqual(emitted, ["Encabezado", "DetallesItems", "FechaHoraFirma"])

    def test_diagnostics_not_dgii_compliant_and_signature_missing(self):
        diag = build_tipo31_unsigned_draft_diagnostics(
            self.invoice, allow_demo_encf=True
        )
        self.assertEqual(diag.compliance_status, "NOT_DGII_COMPLIANT")
        self.assertFalse(diag.signature_present)
        self.assertFalse(diag.dgii_submission_allowed)
        self.assertIn("Signature", diag.missing_required_fields)

    def test_no_fake_signature_content(self):
        xml_bytes = build_tipo31_unsigned_xml_draft(self.invoice, allow_demo_encf=True)
        text = xml_bytes.decode("utf-8")
        self.assertNotIn("<Signature>", text)
        self.assertNotIn("</Signature>", text)
        self.assertNotIn("SignedInfo", text)
        self.assertNotIn("http://www.w3.org/2000/09/xmldsig#", text)

    def test_includes_fechahorafirma_and_encf(self):
        ecf = self.invoice.ecf_document
        xml_bytes = build_tipo31_unsigned_xml_draft(self.invoice, allow_demo_encf=True)
        root = self._xml_root(xml_bytes)
        expected = ecf.signature_datetime.strftime("%d-%m-%Y %H:%M:%S")
        self.assertEqual(root.findtext("FechaHoraFirma"), expected)
        self.assertEqual(
            root.findtext("Encabezado/IdDoc/eNCF"),
            self.invoice.official_encf,
        )

    def test_deterministic_and_line_order(self):
        a = build_tipo31_unsigned_xml_draft(self.invoice, allow_demo_encf=True)
        b = build_tipo31_unsigned_xml_draft(self.invoice, allow_demo_encf=True)
        self.assertEqual(a, b)
        root = self._xml_root(a)
        orders = [
            el.findtext("NumeroLinea")
            for el in root.findall("DetallesItems/Item")
        ]
        self.assertEqual(orders, ["1", "2"])

    def test_product_service_changes_do_not_mutate_line_xml(self):
        before = build_tipo31_unsigned_xml_draft(self.invoice, allow_demo_encf=True)
        self.product.name = "Mutated After Snapshot"
        self.product.save(update_fields=["name"])
        after = build_tipo31_unsigned_xml_draft(self.invoice, allow_demo_encf=True)
        self.assertEqual(before, after)
        self.assertNotIn("Mutated After Snapshot", after.decode("utf-8"))
        root = self._xml_root(after)
        names = [el.findtext("NombreItem") for el in root.findall("DetallesItems/Item")]
        self.assertTrue(all(n == "Original Draft Service" for n in names))


class Tipo31UnsignedDraftDocumentTests(Tipo31UnsignedDraftBase):
    def test_generate_creates_linked_document_with_hash(self):
        before_ecf = ECFDocument.objects.filter(invoice=self.invoice).count()
        document, created = generate_tipo31_unsigned_draft_document(
            self.invoice,
            created_by=self.user,
            allow_demo_encf=True,
        )
        self.assertTrue(created)
        self.assertEqual(document.document_kind, "XML")
        self.assertEqual(document.source, "GENERATED")
        self.assertEqual(document.related_invoice_id, self.invoice.pk)
        self.assertEqual(len(document.sha256_hash), 64)
        self.assertEqual(
            document.original_filename,
            f"tipo31-unsigned-draft-{self.invoice.internal_code}.xml",
        )
        self.assertEqual(ECFDocument.objects.filter(invoice=self.invoice).count(), before_ecf)
        self.invoice.ecf_document.refresh_from_db()
        self.assertIsNone(self.invoice.ecf_document.dgii_track_id)
        self.assertFalse(self.invoice.ecf_document.xml_signed_file)

    def test_repeated_generation_reuses_identical_document(self):
        first, created1 = generate_tipo31_unsigned_draft_document(
            self.invoice, created_by=self.user, allow_demo_encf=True
        )
        second, created2 = generate_tipo31_unsigned_draft_document(
            self.invoice, created_by=self.user, allow_demo_encf=True
        )
        self.assertTrue(created1)
        self.assertFalse(created2)
        self.assertEqual(first.pk, second.pk)

    def test_changed_invoice_content_creates_new_document(self):
        first, _ = generate_tipo31_unsigned_draft_document(
            self.invoice, created_by=self.user, allow_demo_encf=True
        )
        self.line2.unit_price = Decimal("30.00")
        self.line2.save()
        self.invoice.refresh_from_db()
        second, created = generate_tipo31_unsigned_draft_document(
            self.invoice, created_by=self.user, allow_demo_encf=True
        )
        self.assertTrue(created)
        self.assertNotEqual(first.pk, second.pk)
        self.assertNotEqual(first.sha256_hash, second.sha256_hash)

    def test_audit_event_created(self):
        document, _ = generate_tipo31_unsigned_draft_document(
            self.invoice, created_by=self.user, allow_demo_encf=True
        )
        event = AuditEvent.objects.filter(
            event_type="tipo31_unsigned_draft_generated",
            entity_type="Invoice",
            entity_id=self.invoice.pk,
        ).latest("id")
        self.assertEqual(event.metadata.get("document_id"), document.pk)
        self.assertEqual(event.metadata.get("sha256"), document.sha256_hash)
        self.assertEqual(event.metadata.get("compliance_status"), "NOT_DGII_COMPLIANT")
        self.assertIn("Signature", event.metadata.get("missing_required_fields") or [])


class Tipo31UnsignedDraftCommandTests(Tipo31UnsignedDraftBase):
    def test_stdout_prints_xml_and_creates_no_document(self):
        before = Document.objects.filter(
            related_invoice=self.invoice,
            original_filename=f"tipo31-unsigned-draft-{self.invoice.internal_code}.xml",
        ).count()
        with captured_stdout() as out:
            call_command(
                "generate_tipo31_unsigned_draft",
                internal_code=self.invoice.internal_code,
                allow_demo_encf=True,
                stdout_flag=True,
            )
        output = out.getvalue()
        self.assertIn("<ECF>", output)
        self.assertIn("<Encabezado>", output)
        self.assertNotIn("<ECF dgii_compliance=", output)
        after = Document.objects.filter(
            related_invoice=self.invoice,
            original_filename=f"tipo31-unsigned-draft-{self.invoice.internal_code}.xml",
        ).count()
        self.assertEqual(before, after)

    def test_diagnostics_json_is_parseable(self):
        with captured_stdout() as out:
            call_command(
                "generate_tipo31_unsigned_draft",
                internal_code=self.invoice.internal_code,
                allow_demo_encf=True,
                diagnostics_json=True,
            )
        text = out.getvalue()
        start = text.index("{")
        end = text.rindex("}") + 1
        payload = json.loads(text[start:end])
        self.assertEqual(payload["compliance_status"], "NOT_DGII_COMPLIANT")
        self.assertFalse(payload["signature_present"])
        self.assertIn("Signature", payload["missing_required_fields"])

    def test_save_creates_or_reuses_document(self):
        with captured_stdout() as out1:
            call_command(
                "generate_tipo31_unsigned_draft",
                internal_code=self.invoice.internal_code,
                allow_demo_encf=True,
            )
        self.assertIn("Created Tipo 31 unsigned draft Document", out1.getvalue())
        docs = Document.objects.filter(
            related_invoice=self.invoice,
            original_filename=f"tipo31-unsigned-draft-{self.invoice.internal_code}.xml",
        )
        self.assertEqual(docs.count(), 1)
        with captured_stdout() as out2:
            call_command(
                "generate_tipo31_unsigned_draft",
                internal_code=self.invoice.internal_code,
                allow_demo_encf=True,
            )
        self.assertIn("Reused Tipo 31 unsigned draft Document", out2.getvalue())
        self.assertEqual(docs.count(), 1)

    def test_command_refuses_demo_without_flag(self):
        with self.assertRaises(CommandError):
            call_command(
                "generate_tipo31_unsigned_draft",
                internal_code=self.invoice.internal_code,
            )

    def test_no_ecf_trackid_or_signed_xml_created(self):
        before_count = ECFDocument.objects.count()
        generate_tipo31_unsigned_draft_document(self.invoice, allow_demo_encf=True)
        self.assertEqual(ECFDocument.objects.count(), before_count)
        ecf = self.invoice.ecf_document
        self.assertIsNone(ecf.dgii_track_id)
        self.assertFalse(ecf.xml_signed_file)
