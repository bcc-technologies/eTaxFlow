# Checkpoint 004 — Demo Data Cleanup & Duplicate Diagnostics

## Duplicate diagnosis before cleanup

```
Contacts by contact_type + rnc_or_id
  DUPLICATE count=3 filters={'contact_type': 'CLIENT', 'rnc_or_id': '123456789'} pks=[1, 3, 4]
    pk=1:'Demo Client S.R.L.':active=True, pk=3:'Customer':active=True, pk=4:'C':active=True

Contacts by legal_name: (none)
Organizations / fiscal catalog / products: (none)
Demo invoices by SEEDED_BCC_DEMO_INVOICE marker: (none)  # single seed invoice, not duplicated

Found 1 duplicate group(s).
```

## Cleanup strategy

- **Diagnose** (`diagnose_seed_duplicates`): read-only report of seed/demo-relevant duplicate groups.
- **Cleanup** (`cleanup_seed_demo_data`):
  - default `--dry-run`; `--apply` required to mutate
  - Contacts: keep lowest `pk` for known demo natural keys; soft-deactivate (`is_active=False`) only **clearly demo** duplicates (Demo names / demo emails / `Demo …` prefixes)
  - Ambiguous duplicates sharing demo RNC (e.g. `Customer`, `C`) are **skipped** and reported — never deleted
  - Seed invoices: keep first marker invoice; retire extra markers to `RETIRED_BCC_DEMO_INVOICE_DUPLICATE`; delete extra lines beyond `line_order` 1–2 on the keeper
  - Catalog duplicates by code: report only (no auto-delete); DB unique constraints already prevent most cases
- Soft Contact natural-key helper: `contacts.natural_keys.resolve_contact_by_natural_key`
- No DB `UniqueConstraint` on Contact yet

## Files changed

- `core/seed_demo.py` (new)
- `contacts/natural_keys.py` (new)
- `contacts/models.py`
- `core/management/commands/diagnose_seed_duplicates.py` (new)
- `core/management/commands/cleanup_seed_demo_data.py` (new)
- `core/management/commands/seed_bcc.py`
- `tests/test_seed_demo_cleanup.py` (new)
- `tests/test_invoice_workflow.py` (prior seed idempotence tests)
- `README.md`
- `CHECKPOINT_004_DEMO_DATA_CLEANUP.md` (this file)

## Migrations

**No changes detected**

## Commands run

```bash
.venv/bin/python manage.py makemigrations   # No changes detected
.venv/bin/python manage.py migrate          # No migrations to apply
.venv/bin/python manage.py check            # no issues
.venv/bin/python -m pytest -q               # 50 passed
.venv/bin/python manage.py diagnose_seed_duplicates
.venv/bin/python manage.py cleanup_seed_demo_data --dry-run
.venv/bin/python manage.py cleanup_seed_demo_data --apply
.venv/bin/python manage.py seed_bcc
.venv/bin/python -m pytest -q               # 50 passed
```

## Cleanup result (local DB)

```
NOTE: SKIP Contact pk=3 ('Customer') — ambiguous duplicate of demo key (CLIENT, 123456789); keeper pk=1
NOTE: SKIP Contact pk=4 ('C') — ambiguous duplicate of demo key (CLIENT, 123456789); keeper pk=1
No mutable demo cleanup actions; see notes above.
```

## seed_bcc result after cleanup

```
WARNING: Found 3 duplicate Contact records for {'contact_type': 'CLIENT', 'rnc_or_id': '123456789'}; using first pk=1.
Demo BCC data seeded.
Seeded invoice: BCC-AR-2026-000001 (lines=2, marker=SEEDED_BCC_DEMO_INVOICE)
Contacts used: client_pk=1, supplier_pk=2
```

## Final pytest result

**50 passed**

## Remaining limitations

- Ambiguous contacts sharing demo RNC (`Customer`, `C`) are not auto-cleaned.
- Contact natural-key uniqueness remains soft (no DB constraint).
- Catalog rows are never hard-deleted by cleanup.
- Non-seed invoices are never deleted.

## Next recommended task

Introduce an explicit **opt-in merge** for ambiguous demo-RNC contacts (repoint FKs to the keeper, then soft-deactivate orphans), **or** add a deferred DB unique constraint migration after a confirmed clean environment — still without DGII XML mapping.
