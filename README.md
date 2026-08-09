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

## Warnings

- `internal_code` is not the same as DGII official `NCF` or `e-NCF`.
- Fiscal catalog data is preliminary internal master data and placeholder-only.
- e-CF XML generation is not implemented yet.
- DGII production connection is not implemented.
- Digital signing is not implemented.
- XML schema compliance is not implemented.
- OCR, AI, payments, and a custom frontend are not implemented yet.
