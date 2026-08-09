# Checkpoint 008 — eNCF Sequence Allocation Complete

## Files changed

- `CHECKPOINT_008_ENCF_SEQUENCE_START.md` (new)
- `CHECKPOINT_008_ENCF_SEQUENCE_COMPLETE.md` (new)
- `fiscal/models.py` — `ENCFSequenceRange`
- `fiscal/admin.py`
- `fiscal/migrations/0004_encf_sequence_range.py` (new)
- `fiscal/services/__init__.py` (new)
- `fiscal/services/encf_sequences.py` (new)
- `fiscal/management/__init__.py` (new)
- `fiscal/management/commands/__init__.py` (new)
- `fiscal/management/commands/allocate_demo_encf.py` (new)
- `core/management/commands/seed_bcc.py`
- `invoicing/admin.py` — demo allocate action
- `ecf/dgii/mapping.py` — demo/non-authorized eNCF warning
- `ecf/dgii/field_catalogs/tipo_ecf_31.py`
- `ecf/dgii/types.py`
- `docs/dgii/mapping/TIPO_ECF_31_FIELD_CATALOG.md`
- `README.md`
- `tests/test_encf_sequences.py` (new)
- `tests/test_invoice_workflow.py`

## Migrations created

- `fiscal/migrations/0004_encf_sequence_range.py`

## Sequence model summary

`ENCFSequenceRange`:
- issuer, fiscal_document_type, prefix
- start_number / end_number / next_number / number_pad_width
- sequence_expiration_date
- environment (`DEV`…`PRODUCTION`)
- source (`MANUAL_DEMO`…`OTHER`)
- is_authorized_by_dgii (default False)
- is_active, notes, timestamps
- PRODUCTION requires `is_authorized_by_dgii=True`
- Unique active range per issuer + type + prefix + environment

## Allocation service summary

`fiscal/services/encf_sequences.py`:
- `preview_next_encf(...)` (dry-run helper)
- `allocate_next_encf(invoice, range_id=None, actor=None, allow_demo=False)`
- Formats local eNCF as `prefix + zero-padded number` (demo format; not claimed XSD/DGII-authorized)
- Sets `Invoice.official_encf` + `sequence_expiration_date`
- Increments `next_number` under `transaction.atomic` + row locks
- Writes `AuditEvent(event_type="encf_allocated")`
- Does not create ECFDocument / XML / signatures / DGII calls

## Seed range behavior

- Creates/updates one DEV `MANUAL_DEMO` range: prefix `DEMO-E31-`, 1–999999
- Preserves `next_number` on re-seed
- Does **not** auto-allocate `official_encf`

## Dry-run result

- Candidate: `DEMO-E31-000001`
- No mutation

## Apply result

- Allocated: `DEMO-E31-000001`
- `sequence_expiration_date`: `2027-12-31`

## Mapping result after allocation

- Status: `READY_FOR_FUTURE_DRAFT`
- `official_encf`: `DEMO-E31-000001`
- Available field count: **20**
- Missing required: **2** — `FechaHoraFirma`, `Signature`
- Warning: `DEMO_OR_UNAUTHORIZED_ENCF`
- Compliance: **NOT_DGII_COMPLIANT**

## Remaining missing required fields

1. `FechaHoraFirma`
2. `Signature`

## Final pytest result

**95 passed**

## Known limitations

- Demo eNCF format (`DEMO-E31-######`) is local-only and not XSD length-13 / DGII-authorized.
- No DGII authorization client or imported official ranges.
- No signing, certificates, TrackId, or production XML.
- PRODUCTION ranges are validated to require an authorization flag, but this app never obtains that authorization from DGII.

## Exact next recommended task

Design a **non-production signing placeholder / FechaHoraFirma workflow stub** that records an explicit “unsigned” state and never stores private keys — or collect remaining Emisores/legal sources needed before any future authorized-range import model.
