# Checkpoint 004 — Contact Duplicate Merge

## Duplicate group before merge

```
Contacts by contact_type + rnc_or_id
  DUPLICATE count=3 filters={'contact_type': 'CLIENT', 'rnc_or_id': '123456789'} pks=[1, 3, 4]
    pk=1:'Demo Client S.R.L.':active=True, pk=3:'Customer':active=True, pk=4:'C':active=True
    Suggested merge (dry-run only):
      python manage.py merge_duplicate_contacts --contact-type CLIENT --rnc-or-id 123456789 --keep-pk 1 --dry-run
```

## Dry-run result

```
Group: contact_type=CLIENT rnc_or_id=123456789
Contacts found: pk=1:'Demo Client S.R.L.':active=True, pk=3:'Customer':active=True, pk=4:'C':active=True
Canonical contact: pk=1 ('Demo Client S.R.L.')
Duplicates to merge: pk=3 ('Customer'), pk=4 ('C')
Foreign keys that would be repointed:
  (none)
Contacts that would be soft-deactivated: pks=[3, 4]
Hard delete: disabled (never by default)
```

## Apply result

```
Merge applied.
  Repointed: (none)
  Soft-deactivated contact pks=[3, 4]
  AuditEvent: contact_duplicate_merged
  Reason: Resolve local demo duplicate contacts before DGII fixture mapping
```

## FK repoints performed

- None in this local database (Invoice/Document FKs already pointed at keeper pk=1).
- Command dynamically discovers Contact FKs via Django model metadata; currently:
  - `invoicing.Invoice.customer`
  - `documents.Document.related_contact`
- Covered by tests for both FK paths.

## Contacts soft-deactivated

- pk=3 (`Customer`)
- pk=4 (`C`)
- Keeper pk=1 remains active

## seed_bcc result after merge

```
Demo BCC data seeded.
Seeded invoice: BCC-AR-2026-000001 (lines=2, marker=SEEDED_BCC_DEMO_INVOICE)
Contacts used: client_pk=1, supplier_pk=2
```

No duplicate-contact WARNING (active-only natural-key checks).

## Final duplicate diagnosis

```
No duplicate seed records detected
```

## Final pytest result

**61 passed**

## Migrations

**No changes detected**

## Files changed

- `contacts/merge.py` (new)
- `contacts/natural_keys.py`
- `core/seed_demo.py`
- `core/management/commands/merge_duplicate_contacts.py` (new)
- `core/management/commands/diagnose_seed_duplicates.py`
- `core/management/commands/seed_bcc.py`
- `tests/test_merge_duplicate_contacts.py` (new)
- `README.md`
- `CHECKPOINT_004_CONTACT_MERGE.md` (this file)

## Known limitations

- Soft-deactivated duplicate Contact rows remain in the DB (no hard delete by default).
- Non-demo natural keys require `--allow-non-demo`.
- Merge never runs automatically; `--apply` is mandatory for mutation.
- Contact natural-key uniqueness is still not a DB constraint.
- Inactive leftovers are hidden from active duplicate diagnosis but still exist.

## Next recommended task

After a confirmed clean environment, add a deferred migration for a Contact unique constraint on `(contact_type, rnc_or_id)` (or unique among active rows), **or** begin Phase 005 DGII fixture/XML mapping groundwork — still without live DGII calls/signing.
