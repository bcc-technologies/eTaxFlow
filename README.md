# eTaxFlow

eTaxFlow is a Django-based MVP for internal invoice vaulting and invoicing workflows for BARREIRO CASANOVA CASTILLO TECHNOLOGIES, S.R.L.

## Local setup

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt
python manage.py migrate
python -m pytest -q
python manage.py runserver
```

## Seed demo data

```bash
python manage.py seed_bcc
```

Diagnose and optionally clean duplicate demo/seed rows:

```bash
python manage.py diagnose_seed_duplicates
python manage.py cleanup_seed_demo_data          # dry-run (default)
python manage.py cleanup_seed_demo_data --apply  # mutate clearly-demo duplicates only
```

Explicit opt-in merge for ambiguous duplicate contacts (never automatic):

```bash
python manage.py merge_duplicate_contacts \
  --contact-type CLIENT --rnc-or-id 123456789 --keep-pk 1 --dry-run
python manage.py merge_duplicate_contacts \
  --contact-type CLIENT --rnc-or-id 123456789 --keep-pk 1 --apply \
  --reason "Resolve local demo duplicate contacts"
```

**Contact uniqueness warning:** `(contact_type, rnc_or_id)` is a soft/business-level natural key only. It is **not** enforced with a database `UniqueConstraint` yet, because local databases may already contain duplicates. Prefer `contacts.natural_keys.resolve_contact_by_natural_key` for deterministic resolution.

## Admin workflow

- Use the Django admin to create and manage organizations, contacts, invoices, documents, and ECF placeholders.
- Invoice totals are calculated automatically and are read-only in admin.
- Invoice lifecycle transitions are enforced through safe state methods.
- Document invoice links create audit events when a document is associated with an invoice.

## Fiscal master data

This project now includes preliminary internal fiscal master data for demo and workflow development:

- `FiscalDocumentType`
- `TaxRate`
- `UnitOfMeasure`
- `ProductService`
- line-item snapshot fields for invoice persistence

## Internal XML draft layer

- Generate internal XML draft documents for invoices using `python manage.py generate_internal_xml --invoice <INVOICE_CODE>` or `python manage.py generate_internal_xml --all`
- Use the admin action `Generate internal XML draft documents` on invoices to create XML artifacts from normalized invoice data.
- This XML is a deterministic internal draft only and not DGII-compliant or signed.

## DGII schema mapping groundwork

Phase 005 maps existing normalized invoice data to **future** DGII e-CF concepts only.

```bash
python manage.py inspect_dgii_mapping --internal-code BCC-AR-2026-000001
python manage.py inspect_dgii_mapping --internal-code BCC-AR-2026-000001 --json
python manage.py inspect_dgii_mapping --invoice-id 1 --strict
```

- Inventory of official DGII source documents: `docs/dgii/DGII_ECF_DOCUMENT_INVENTORY.md`
- Mapping package: `ecf/dgii/`
- This phase does **not** generate DGII-compliant XML
- It does **not** digitally sign
- It does **not** authenticate with DGII (semilla/token)
- It does **not** send anything to DGII
- Official DGII documents must be collected and reviewed before claiming compliance

## Warnings

- `internal_code` is not the same as DGII official `NCF` or `e-NCF`.
- Fiscal catalog data is preliminary internal master data and placeholder-only.
- e-CF XML generation is not implemented yet.
- DGII production connection is not implemented.
- Digital signing is not implemented.
- XML schema compliance is not implemented.
- OCR, AI, payments, and a custom frontend are not implemented yet.
