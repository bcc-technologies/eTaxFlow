# Checkpoint 004 — seed_bcc Idempotence Fix

## Duplicate diagnosis (local/dev DB)

| Entity | Natural key | Result |
|--------|-------------|--------|
| Contact | `rnc_or_id` | **3 duplicates** for `123456789` (pks 1, 3, 4) |
| Contact | `rnc_or_id` + `contact_type` | **3 CLIENT** rows for `123456789` |
| Contact | `legal_name` | none |
| Organization | `rnc` / `legal_name` | none |
| Invoice (seed marker) | `notes` contains `SEEDED_BCC_DEMO_INVOICE` | 1 (stable) |
| ProductService / TaxRate / UnitOfMeasure / FiscalDocumentType | `code` | none |

**Root cause:** `Contact` has no uniqueness constraint on `(contact_type, rnc_or_id)`. Earlier seed / demo / test data created multiple CLIENT rows with the same RNC. Prior `get_or_create` / `.get()` usage raised `MultipleObjectsReturned` on dirty local databases.

## Files changed

- `core/management/commands/seed_bcc.py`
- `tests/test_invoice_workflow.py`
- `CHECKPOINT_004_SEED_IDEMPOTENCE_FIX.md` (this file)

## Migrations

**No changes detected** — no new migrations created.

## seed_bcc behavior

### Before

- Failed (or was unsafe) on dirty DBs with duplicate demo contacts via `MultipleObjectsReturned`.
- Demo invoice creation was not reliably idempotent across repeated runs.

### After

- Uses `get_first_or_create` / `update_first_or_create`:
  - filter by stable natural key
  - if one or more exist → update first deterministic row (`order_by("pk")`)
  - if none → create
  - print `WARNING: Found N duplicate ...` with counts; do not crash
  - do **not** auto-delete real or ambiguous duplicates
- Demo invoice keyed by `SEEDED_BCC_DEMO_INVOICE` marker; reused/updated across runs
- Always rebuilds/keeps exactly **two** seeded lines (`line_order` 1 and 2); removes extra lines on that invoice
- Catalog rows keyed by `code` (fiscal types, tax rates, units, products)
- Organization keyed by `rnc` (fallback `legal_name`)
- Contact keyed by `contact_type` + `rnc_or_id`
- No fake `official_ncf` / `official_encf`

### Two consecutive seed runs (verification)

```
WARNING: Found 3 duplicate Contact records for {'contact_type': 'CLIENT', 'rnc_or_id': '123456789'}; using first pk=1.
Demo BCC data seeded.
Seeded invoice: BCC-AR-2026-000001 (lines=2, marker=SEEDED_BCC_DEMO_INVOICE)

WARNING: Found 3 duplicate Contact records for {'contact_type': 'CLIENT', 'rnc_or_id': '123456789'}; using first pk=1.
Demo BCC data seeded.
Seeded invoice: BCC-AR-2026-000001 (lines=2, marker=SEEDED_BCC_DEMO_INVOICE)

contacts= 6
seed_invoices= 1
```

## Final pytest result

**38 passed**

## Remaining limitations

- Existing duplicate Contacts are **not** deleted; seed only warns and uses the lowest `pk`.
- `Contact` still lacks a DB unique constraint on `(contact_type, rnc_or_id)`.
- Non-demo invoices with the same customer/issuer are untouched unless they match the seed marker / adoption heuristic.
- Duplicate cleanup is intentionally manual for safety.

## Next recommended task

Add an optional, explicit **demo-data cleanup / dedupe** management command (opt-in only) that safely merges or archives clearly seeded duplicate Contacts, **or** introduce a soft uniqueness rule / constrained uniqueness for demo identifiers — still without implementing DGII XML mapping.
