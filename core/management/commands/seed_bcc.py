from decimal import Decimal
from datetime import date

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from contacts.natural_keys import (
    find_contacts_by_natural_key,
    resolve_contact_by_natural_key,
)
from core.seed_demo import (
    DEMO_CLIENT_DEFAULTS,
    DEMO_CLIENT_RNC,
    DEMO_ISSUER_RNC,
    DEMO_SUPPLIER_DEFAULTS,
    DEMO_SUPPLIER_RNC,
    SEED_INVOICE_MARKER,
)
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

    def get_first_or_create(self, model, filters, defaults=None):
        """Return the first matching row by natural key, or create one.

        Safe against MultipleObjectsReturned: never uses get()/get_or_create
        on non-unique natural keys. If duplicates exist, updates the first
        deterministic record (lowest pk) and prints a warning with counts.
        """
        defaults = defaults or {}
        queryset = model.objects.filter(**filters).order_by("pk")
        duplicate_count = queryset.count()

        if duplicate_count:
            instance = queryset.first()
            if defaults:
                for key, value in defaults.items():
                    setattr(instance, key, value)
                # Full save so model.save() side effects (e.g. InvoiceLine
                # snapshots/totals) persist even when update_fields would omit them.
                instance.save()
            if duplicate_count > 1:
                self.stdout.write(
                    self.style.WARNING(
                        f"WARNING: Found {duplicate_count} duplicate {model.__name__} "
                        f"records for {filters}; using first pk={instance.pk}."
                    )
                )
            return instance, False

        instance = model.objects.create(**filters, **defaults)
        return instance, True

    # Alias used by callers / tests for clarity.
    update_first_or_create = get_first_or_create

    def _get_organization(self, rnc, defaults):
        if rnc:
            return self.get_first_or_create(Organization, {"rnc": rnc}, defaults=defaults)
        return self.get_first_or_create(
            Organization,
            {"legal_name": defaults["legal_name"]},
            defaults={**defaults, "rnc": rnc or ""},
        )

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

            issuer, _ = self._get_organization(
                DEMO_ISSUER_RNC,
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

            client, _, _ = resolve_contact_by_natural_key(
                "CLIENT",
                DEMO_CLIENT_RNC,
                defaults=DEMO_CLIENT_DEFAULTS,
            )
            supplier, _, _ = resolve_contact_by_natural_key(
                "SUPPLIER",
                DEMO_SUPPLIER_RNC,
                defaults=DEMO_SUPPLIER_DEFAULTS,
            )
            for contact_type, rnc, contact in (
                ("CLIENT", DEMO_CLIENT_RNC, client),
                ("SUPPLIER", DEMO_SUPPLIER_RNC, supplier),
            ):
                count = find_contacts_by_natural_key(
                    contact_type, rnc, active_only=True
                ).count()
                if count > 1:
                    self.stdout.write(
                        self.style.WARNING(
                            f"WARNING: Found {count} duplicate Contact records for "
                            f"{{'contact_type': '{contact_type}', 'rnc_or_id': '{rnc}'}}; "
                            f"using first pk={contact.pk}."
                        )
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
                item, _ = self.get_first_or_create(
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

            tax_itbis_18, _ = self.get_first_or_create(
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
            self.get_first_or_create(
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
            self.get_first_or_create(
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

            unit_service, _ = self.get_first_or_create(
                UnitOfMeasure,
                {"code": "SERVICE"},
                defaults={
                    "name": "Service",
                    "symbol": "SRV",
                    "is_active": True,
                },
            )
            self.get_first_or_create(
                UnitOfMeasure,
                {"code": "UNIT"},
                defaults={
                    "name": "Unit",
                    "symbol": "UN",
                    "is_active": True,
                },
            )
            self.get_first_or_create(
                UnitOfMeasure,
                {"code": "HOUR"},
                defaults={
                    "name": "Hour",
                    "symbol": "H",
                    "is_active": True,
                },
            )

            product_software, _ = self.get_first_or_create(
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
            product_consulting, _ = self.get_first_or_create(
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

            invoice = (
                Invoice.objects.filter(
                    issuer=issuer,
                    customer=client,
                    notes__icontains=SEED_INVOICE_MARKER,
                )
                .order_by("pk")
                .first()
            )

            if not invoice:
                # Adopt a prior draft demo invoice that predates the marker.
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
                    invoice.notes = SEED_INVOICE_MARKER
                    invoice.save(update_fields=["notes"])
                    if candidates.count() > 1:
                        self.stdout.write(
                            self.style.WARNING(
                                f"WARNING: Found {candidates.count()} candidate demo invoices; "
                                f"adopting first pk={invoice.pk}."
                            )
                        )
                    else:
                        self.stdout.write(
                            self.style.WARNING(
                                f"Found existing seeded invoice without marker; "
                                f"adopting invoice pk={invoice.pk}."
                            )
                        )

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
                invoice.notes = SEED_INVOICE_MARKER
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
                    notes=SEED_INVOICE_MARKER,
                )

            line_fields = {
                1: {
                    "description": "Software development service",
                    "product_service": product_software,
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
                    "product_service": product_consulting,
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
                self.get_first_or_create(
                    InvoiceLine,
                    {"invoice": invoice, "line_order": line_order},
                    defaults={"description": line_description, **line_defaults},
                )

            extra_lines = invoice.lines.exclude(line_order__in=[1, 2])
            if extra_lines.exists():
                extra_lines.delete()

            invoice._recalculate_totals()

            self.get_first_or_create(
                ECFDocument,
                {"invoice": invoice},
                defaults={
                    "environment": "DEV",
                    "ecf_type": "DEMO",
                    "dgii_status": "NOT_SENT",
                },
            )

            self.stdout.write(self.style.SUCCESS("Demo BCC data seeded."))
            self.stdout.write(
                f"Seeded invoice: {invoice.internal_code} "
                f"(lines={invoice.lines.count()}, marker={SEED_INVOICE_MARKER})"
            )
            self.stdout.write(
                f"Contacts used: client_pk={client.pk}, supplier_pk={supplier.pk}"
            )
