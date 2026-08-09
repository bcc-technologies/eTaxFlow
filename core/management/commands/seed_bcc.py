from decimal import Decimal
from datetime import date

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from contacts.models import Contact
from ecf.models import ECFDocument
from fiscal.models import (
    FiscalDocumentType,
    InternalDocumentCode,
    TaxRate,
    UnitOfMeasure,
)
from invoicing.models import Invoice, InvoiceLine, ProductService
from organizations.models import Organization


class Command(BaseCommand):
    help = "Seed the database with demo BCC data."

    def _get_or_update_first(self, model, filters, defaults=None):
        defaults = defaults or {}
        queryset = model.objects.filter(**filters).order_by("pk")
        if queryset.exists():
            instance = queryset.first()
            if defaults:
                for key, value in defaults.items():
                    setattr(instance, key, value)
                instance.save(update_fields=list(defaults.keys()))
            if queryset.count() > 1:
                self.stdout.write(self.style.WARNING(
                    f"Multiple {model.__name__} records found for {filters}; using first pk={instance.pk}."
                ))
            return instance, False

        instance = model.objects.create(**filters, **defaults)
        return instance, True

    def handle(self, *args, **options):
        with transaction.atomic():
            user_model = get_user_model()
            demo_user, created_user = user_model.objects.get_or_create(
                username="bcc_demo",
                defaults={
                    "email": "demo.user@example.com",
                },
            )
            if created_user:
                demo_user.set_unusable_password()
                demo_user.save(update_fields=["password"])

            issuer, _ = self._get_or_update_first(
                Organization,
                {"rnc": "1310000000"},
                defaults={
                    "legal_name": "BARREIRO CASANOVA CASTILLO TECHNOLOGIES, S.R.L.",
                    "commercial_name": "BCC Technologies",
                    "address": "Santo Domingo",
                    "phone": "809-000-0000",
                    "email": "info@bcc.com",
                    "website": "https://bcc.com",
                    "is_default_issuer": True,
                },
            )

            client, _ = self._get_or_update_first(
                Contact,
                {"contact_type": "CLIENT", "rnc_or_id": "123456789"},
                defaults={
                    "legal_name": "Demo Client S.R.L.",
                    "commercial_name": "Demo Client",
                    "id_type": "RNC",
                    "address": "Santo Domingo",
                    "phone": "809-111-1111",
                    "email": "demo.client@example.com",
                    "tax_category": "GENERAL",
                    "is_active": True,
                },
            )

            supplier, _ = self._get_or_update_first(
                Contact,
                {"contact_type": "SUPPLIER", "rnc_or_id": "987654321"},
                defaults={
                    "legal_name": "Demo Supplier S.R.L.",
                    "commercial_name": "Demo Supplier",
                    "id_type": "RNC",
                    "address": "Santo Domingo",
                    "phone": "809-222-2222",
                    "email": "demo.supplier@example.com",
                    "tax_category": "GENERAL",
                    "is_active": True,
                },
            )

            fiscal_types = [
                ("31", "Factura de Crédito Fiscal Electrónica", "INVOICE", "OUTBOUND"),
                ("32", "Factura de Consumo Electrónica", "INVOICE", "OUTBOUND"),
                ("33", "Nota de Débito Electrónica", "DEBIT_NOTE", "OUTBOUND"),
                ("34", "Nota de Crédito Electrónica", "CREDIT_NOTE", "OUTBOUND"),
                ("41", "Compras Electrónico", "OTHER", "INBOUND"),
                ("43", "Gastos Menores Electrónico", "OTHER", "OUTBOUND"),
                ("44", "Regímenes Especiales Electrónico", "SPECIAL_REGIME", "OUTBOUND"),
                ("45", "Gubernamental Electrónico", "GOVERNMENT", "OUTBOUND"),
                ("46", "Comprobante de Exportaciones Electrónico", "EXPORT", "OUTBOUND"),
                ("47", "Comprobante para Pagos al Exterior Electrónico", "FOREIGN_PAYMENT", "OUTBOUND"),
            ]
            fiscal_catalog = {}
            for code, name, group, direction in fiscal_types:
                item, _ = self._get_or_update_first(
                    FiscalDocumentType,
                    {"code": code},
                    defaults={
                        "name": name,
                        "description": "Demo fiscal document type placeholder.",
                        "document_group": group,
                        "direction": direction,
                        "is_electronic": True,
                        "is_active": True,
                        "requires_customer_rnc": True,
                        "requires_printed_representation": False,
                        "affects_accounts_receivable": True,
                        "affects_accounts_payable": group in {"INVOICE", "DEBIT_NOTE", "CREDIT_NOTE"},
                    },
                )
                fiscal_catalog[code] = item

            tax_itbis_18, _ = self._get_or_update_first(
                TaxRate,
                {"code": "ITBIS_18"},
                defaults={
                    "name": "ITBIS 18%",
                    "rate": Decimal("18.00"),
                    "tax_type": "ITBIS",
                    "is_default": True,
                    "is_active": True,
                },
            )
            self._get_or_update_first(
                TaxRate,
                {"code": "ITBIS_0"},
                defaults={
                    "name": "ITBIS 0%",
                    "rate": Decimal("0.00"),
                    "tax_type": "ZERO_RATE",
                    "is_default": False,
                    "is_active": True,
                },
            )
            self._get_or_update_first(
                TaxRate,
                {"code": "EXEMPT"},
                defaults={
                    "name": "Exento",
                    "rate": Decimal("0.00"),
                    "tax_type": "EXEMPT",
                    "is_default": False,
                    "is_active": True,
                },
            )

            unit_service, _ = self._get_or_update_first(
                UnitOfMeasure,
                {"code": "SERVICE"},
                defaults={
                    "name": "Service",
                    "symbol": "SRV",
                    "is_active": True,
                },
            )
            self._get_or_update_first(
                UnitOfMeasure,
                {"code": "UNIT"},
                defaults={
                    "name": "Unit",
                    "symbol": "UN",
                    "is_active": True,
                },
            )
            self._get_or_update_first(
                UnitOfMeasure,
                {"code": "HOUR"},
                defaults={
                    "name": "Hour",
                    "symbol": "H",
                    "is_active": True,
                },
            )

            self._get_or_update_first(
                ProductService,
                {"code": "SOFTWARE_DEV_SERVICE"},
                defaults={
                    "name": "Software Development Service",
                    "description": "Demo software development service for seed data.",
                    "item_type": "SERVICE",
                    "default_unit": unit_service,
                    "default_tax_rate": tax_itbis_18,
                    "default_unit_price": Decimal("1200.00"),
                    "is_active": True,
                },
            )
            self._get_or_update_first(
                ProductService,
                {"code": "TECH_CONSULTING_SERVICE"},
                defaults={
                    "name": "Technical Consulting Service",
                    "description": "Demo technical consulting service for seed data.",
                    "item_type": "SERVICE",
                    "default_unit": unit_service,
                    "default_tax_rate": tax_itbis_18,
                    "default_unit_price": Decimal("1500.00"),
                    "is_active": True,
                },
            )

            seed_marker = "SEEDED_BCC_DEMO_INVOICE"
            invoice = Invoice.objects.filter(
                issuer=issuer,
                customer=client,
                notes__icontains=seed_marker,
            ).order_by("pk").first()

            if not invoice:
                candidates = Invoice.objects.filter(
                    issuer=issuer,
                    customer=client,
                    invoice_direction="OUTBOUND",
                    lifecycle_status="DRAFT",
                    fiscal_document_type_ref=fiscal_catalog["31"],
                    internal_code__startswith=f"BCC-AR-{date.today().year}-",
                ).order_by("pk")
                if candidates.exists():
                    invoice = candidates.first()
                    invoice.notes = seed_marker
                    invoice.save(update_fields=["notes"])
                    self.stdout.write(self.style.WARNING(
                        f"Found existing seeded invoice without marker; adopting invoice pk={invoice.pk}."
                    ))

            if invoice:
                invoice.issuer = issuer
                invoice.customer = client
                invoice.invoice_direction = "OUTBOUND"
                invoice.lifecycle_status = "DRAFT"
                invoice.currency = "DOP"
                invoice.issue_date = date.today()
                invoice.created_by = demo_user
                invoice.fiscal_document_type = "31"
                invoice.fiscal_document_type_ref = fiscal_catalog["31"]
                invoice.notes = seed_marker
                invoice.save()
            else:
                invoice_internal_code = InternalDocumentCode.generate_code("AR", date.today().year)
                while Invoice.objects.filter(internal_code=invoice_internal_code).exists():
                    invoice_internal_code = InternalDocumentCode.generate_code("AR", date.today().year)

                invoice = Invoice.objects.create(
                    internal_code=invoice_internal_code,
                    issuer=issuer,
                    customer=client,
                    invoice_direction="OUTBOUND",
                    lifecycle_status="DRAFT",
                    currency="DOP",
                    issue_date=date.today(),
                    created_by=demo_user,
                    fiscal_document_type="31",
                    fiscal_document_type_ref=fiscal_catalog["31"],
                    notes=seed_marker,
                )

            line_fields = {
                1: {
                    "description": "Software development service",
                    "product_service": ProductService.objects.get(code="SOFTWARE_DEV_SERVICE"),
                    "unit": unit_service,
                    "tax_rate_ref": tax_itbis_18,
                    "quantity": Decimal("1.00"),
                    "unit_price": Decimal("1200.00"),
                    "discount_amount": Decimal("0.00"),
                    "tax_rate": tax_itbis_18.rate,
                    "tax_amount": Decimal("216.00"),
                    "line_total": Decimal("1416.00"),
                },
                2: {
                    "description": "Technical consulting service",
                    "product_service": ProductService.objects.get(code="TECH_CONSULTING_SERVICE"),
                    "unit": unit_service,
                    "tax_rate_ref": tax_itbis_18,
                    "quantity": Decimal("1.00"),
                    "unit_price": Decimal("1500.00"),
                    "discount_amount": Decimal("0.00"),
                    "tax_rate": tax_itbis_18.rate,
                    "tax_amount": Decimal("270.00"),
                    "line_total": Decimal("1770.00"),
                },
            }
            for line_order, defaults in line_fields.items():
                line_defaults = {**defaults}
                line_description = line_defaults.pop("description")
                _, _ = self._get_or_update_first(
                    InvoiceLine,
                    {"invoice": invoice, "line_order": line_order},
                    defaults={"description": line_description, **line_defaults},
                )

            extra_lines = invoice.lines.exclude(line_order__in=[1, 2])
            if extra_lines.exists():
                extra_lines.delete()
                invoice._recalculate_totals()

            self._get_or_update_first(
                ECFDocument,
                {"invoice": invoice},
                defaults={
                    "environment": "DEV",
                    "ecf_type": "DEMO",
                    "dgii_status": "NOT_SENT",
                },
            )

            self.stdout.write(self.style.SUCCESS("Demo BCC data seeded."))
