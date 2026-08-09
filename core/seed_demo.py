"""Shared constants and helpers for BCC demo/seed data safety."""

from __future__ import annotations

from django.db.models import Count

from contacts.models import Contact
from fiscal.models import FiscalDocumentType, TaxRate, UnitOfMeasure
from invoicing.models import Invoice, ProductService
from organizations.models import Organization


SEED_INVOICE_MARKER = "SEEDED_BCC_DEMO_INVOICE"
# Must not contain SEED_INVOICE_MARKER as a substring (notes__icontains checks).
RETIRED_SEED_INVOICE_MARKER = "RETIRED_BCC_DEMO_INVOICE_DUPLICATE"

DEMO_CLIENT_RNC = "123456789"
DEMO_SUPPLIER_RNC = "987654321"
DEMO_ISSUER_RNC = "1310000000"

DEMO_CONTACT_NATURAL_KEYS = (
    ("CLIENT", DEMO_CLIENT_RNC),
    ("SUPPLIER", DEMO_SUPPLIER_RNC),
)

DEMO_CLIENT_DEFAULTS = {
    "legal_name": "Demo Client S.R.L.",
    "commercial_name": "Demo Client",
    "id_type": "RNC",
    "address": "Santo Domingo",
    "phone": "809-111-1111",
    "email": "demo.client@example.com",
    "tax_category": "GENERAL",
    "is_active": True,
}

DEMO_SUPPLIER_DEFAULTS = {
    "legal_name": "Demo Supplier S.R.L.",
    "commercial_name": "Demo Supplier",
    "id_type": "RNC",
    "address": "Santo Domingo",
    "phone": "809-222-2222",
    "email": "demo.supplier@example.com",
    "tax_category": "GENERAL",
    "is_active": True,
}

DEMO_LEGAL_NAMES = {
    DEMO_CLIENT_DEFAULTS["legal_name"],
    DEMO_SUPPLIER_DEFAULTS["legal_name"],
}
DEMO_COMMERCIAL_NAMES = {
    DEMO_CLIENT_DEFAULTS["commercial_name"],
    DEMO_SUPPLIER_DEFAULTS["commercial_name"],
}
DEMO_EMAILS = {
    DEMO_CLIENT_DEFAULTS["email"],
    DEMO_SUPPLIER_DEFAULTS["email"],
}

DEMO_CATALOG_CODES = {
    "FiscalDocumentType": {"31", "32", "33", "34", "41", "43", "44", "45", "46", "47"},
    "TaxRate": {"ITBIS_18", "ITBIS_0", "EXEMPT"},
    "UnitOfMeasure": {"SERVICE", "UNIT", "HOUR"},
    "ProductService": {"SOFTWARE_DEV_SERVICE", "TECH_CONSULTING_SERVICE"},
}


def is_demo_contact_natural_key(contact_type: str, rnc_or_id: str) -> bool:
    return (contact_type, rnc_or_id) in DEMO_CONTACT_NATURAL_KEYS


def is_clearly_demo_contact(contact: Contact) -> bool:
    """Return True only for contacts that match seed/demo placeholders."""
    if not is_demo_contact_natural_key(contact.contact_type, contact.rnc_or_id):
        return False

    legal = (contact.legal_name or "").strip()
    commercial = (contact.commercial_name or "").strip()
    email = (contact.email or "").strip().lower()

    if legal in DEMO_LEGAL_NAMES or commercial in DEMO_COMMERCIAL_NAMES:
        return True
    if email in DEMO_EMAILS:
        return True
    if legal.startswith("Demo ") or commercial.startswith("Demo "):
        return True
    if email.endswith("@example.com") and "demo" in email:
        return True
    return False


def iter_duplicate_groups(model, fields):
    """Yield (filters_dict, count, queryset ordered by pk) for groups with count > 1."""
    rows = (
        model.objects.values(*fields)
        .annotate(c=Count("id"))
        .filter(c__gt=1)
        .order_by(*fields)
    )
    for row in rows:
        filters = {field: row[field] for field in fields}
        qs = model.objects.filter(**filters).order_by("pk")
        yield filters, row["c"], qs


def collect_seed_duplicate_report():
    """Build a structured duplicate report for seed/demo-relevant records."""
    sections = []

    def add_section(title, model, fields, formatter=None):
        groups = []
        for filters, count, qs in iter_duplicate_groups(model, fields):
            pks = list(qs.values_list("pk", flat=True))
            detail = formatter(qs) if formatter else ""
            groups.append({"filters": filters, "count": count, "pks": pks, "detail": detail})
        sections.append({"title": title, "groups": groups})

    # Active-only for natural-key groups so soft-merged (inactive) leftovers
    # no longer appear as actionable duplicates after an explicit merge.
    active_contact_groups = []
    active_rows = (
        Contact.objects.filter(is_active=True)
        .values("contact_type", "rnc_or_id")
        .annotate(c=Count("id"))
        .filter(c__gt=1)
        .order_by("contact_type", "rnc_or_id")
    )
    for row in active_rows:
        filters = {"contact_type": row["contact_type"], "rnc_or_id": row["rnc_or_id"]}
        qs = Contact.objects.filter(is_active=True, **filters).order_by("pk")
        active_contact_groups.append(
            {
                "filters": filters,
                "count": row["c"],
                "pks": list(qs.values_list("pk", flat=True)),
                "detail": ", ".join(
                    f"pk={c.pk}:{c.legal_name!r}:active={c.is_active}" for c in qs
                ),
            }
        )
    sections.append(
        {
            "title": "Contacts by contact_type + rnc_or_id",
            "groups": active_contact_groups,
        }
    )
    add_section(
        "Contacts by legal_name",
        Contact,
        ["legal_name"],
        formatter=lambda qs: ", ".join(
            f"pk={c.pk}:{c.contact_type}/{c.rnc_or_id}" for c in qs
        ),
    )
    add_section("Organizations by rnc", Organization, ["rnc"])
    add_section("Organizations by legal_name", Organization, ["legal_name"])
    add_section("FiscalDocumentType by code", FiscalDocumentType, ["code"])
    add_section("TaxRate by code", TaxRate, ["code"])
    add_section("UnitOfMeasure by code", UnitOfMeasure, ["code"])
    add_section("ProductService by code", ProductService, ["code"])

    seed_invoices = Invoice.objects.filter(notes__icontains=SEED_INVOICE_MARKER).order_by("pk")
    seed_count = seed_invoices.count()
    seed_groups = []
    if seed_count > 1:
        seed_groups.append(
            {
                "filters": {"notes__icontains": SEED_INVOICE_MARKER},
                "count": seed_count,
                "pks": list(seed_invoices.values_list("pk", flat=True)),
                "detail": ", ".join(
                    f"pk={inv.pk}:{inv.internal_code}" for inv in seed_invoices
                ),
            }
        )
    sections.append({"title": "Demo invoices by SEEDED_BCC_DEMO_INVOICE marker", "groups": seed_groups})

    total_groups = sum(len(section["groups"]) for section in sections)
    return sections, total_groups
