# Checkpoint 007 — Tipo 31 Required Model Fields Complete

## Files changed

- `CHECKPOINT_007_TIPO31_REQUIRED_MODEL_FIELDS_START.md` (new)
- `CHECKPOINT_007_TIPO31_REQUIRED_MODEL_FIELDS_COMPLETE.md` (new)
- `fiscal/models.py`
- `fiscal/admin.py`
- `fiscal/migrations/0003_tipo31_required_model_fields.py` (new)
- `invoicing/models.py`
- `invoicing/admin.py`
- `invoicing/migrations/0004_tipo31_required_model_fields.py` (new)
- `ecf/models.py`
- `ecf/admin.py`
- `ecf/migrations/0002_tipo31_required_model_fields.py` (new)
- `core/management/commands/seed_bcc.py`
- `ecf/dgii/field_catalogs/tipo_ecf_31.py`
- `ecf/dgii/mapping.py`
- `ecf/dgii/types.py`
- `ecf/management/commands/inspect_dgii_mapping.py`
- `docs/dgii/mapping/TIPO_ECF_31_FIELD_CATALOG.md`
- `README.md`
- `tests/test_dgii_mapping.py`
- `tests/test_invoice_workflow.py`

## Migrations created

- `fiscal/migrations/0003_tipo31_required_model_fields.py`
- `invoicing/migrations/0004_tipo31_required_model_fields.py`
- `ecf/migrations/0002_tipo31_required_model_fields.py`

## New models / fields

### Fiscal catalogs
- `FiscalIncomeType` (`code`, `name`, `description`, `is_active`, timestamps)
- `PaymentType` (`code`, `name`, `description`, `is_active`, timestamps)
- `BillingIndicator` (`code`, `name`, `description`, `is_active`, timestamps)

### Invoice
- `sequence_expiration_date` (nullable `DateField`)
- `income_type` → `FiscalIncomeType` (nullable FK)
- `payment_type` → `PaymentType` (nullable FK)
- existing `official_encf` retained as eNCF source (nullable, not auto-generated)

### InvoiceLine
- `billing_indicator` → `BillingIndicator` (nullable FK)

### ECFDocument
- `signature_datetime` (nullable placeholder `DateTimeField`, admin read-only)

## seed_bcc behavior

- Seeds Formato/XSD-backed preliminary catalogs:
  - Income types `01`–`06`
  - Payment types `1`/`2`/`3`
  - Billing indicators `0`–`4`
- Demo invoice gets `income_type=01`, `payment_type=2`, synthetic `sequence_expiration_date`
- Demo lines get `billing_indicator=1`
- Leaves `official_encf` empty
- Ensures `ECFDocument.signature_datetime` stays `None`
- Idempotent on re-run

## Mapping result before / after

| metric | before (Phase 006) | after (Phase 007 seed) |
|---|---|---|
| Status | `READY_FOR_FUTURE_DRAFT` | `READY_FOR_FUTURE_DRAFT` |
| Available field count | 15 | 19 |
| Missing required count | 7 | 3 |
| Missing required fields | eNCF, FechaVencimientoSecuencia, TipoIngresos, TipoPago, IndicadorFacturacion, FechaHoraFirma, Signature | eNCF, FechaHoraFirma, Signature |
| Compliance | `NOT_DGII_COMPLIANT` | `NOT_DGII_COMPLIANT` |

## Remaining missing required fields

1. `eNCF` (`Invoice.official_encf` empty — no assignment workflow)
2. `FechaHoraFirma` (`ECFDocument.signature_datetime` never set — signing out of scope)
3. `Signature` (no signed XML / certificate storage)

## Final pytest result

**82 passed**

## Known limitations

- Catalog enums are preliminary internal copies of Formato/XSD codes — not a compliance claim.
- Synthetic sequence expiry is demo-only, not an authorized DGII range.
- No eNCF sequence allocation / authorization workflow.
- No digital signing, certificates, private keys, TrackId, or production XML.
- Remaining legal/service source PDFs still missing from inventory.

## Exact next recommended task

Design a **non-production eNCF sequence allocation model** (authorized ranges + `FechaVencimientoSecuencia` binding + assignment to `Invoice.official_encf`) still without DGII API calls, signing, or production XML — or collect remaining official Emisores/Acuse/legal sources if sequence rules need those docs first.
