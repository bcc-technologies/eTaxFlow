# Checkpoint 005 — DGII Schema Mapping Complete

## Files changed

- `CHECKPOINT_005_DGII_SCHEMA_MAPPING_START.md`
- `CHECKPOINT_005_DGII_SCHEMA_MAPPING_COMPLETE.md` (this file)
- `docs/dgii/DGII_ECF_DOCUMENT_INVENTORY.md`
- `ecf/dgii/__init__.py`
- `ecf/dgii/types.py`
- `ecf/dgii/validators.py`
- `ecf/dgii/mapping.py`
- `ecf/dgii/README.md`
- `ecf/management/commands/inspect_dgii_mapping.py`
- `tests/fixtures/dgii/README.md`
- `tests/fixtures/dgii/synthetic_invoice_mapping_case.json`
- `tests/test_dgii_mapping.py`
- `README.md`

## Migrations

**No changes detected**

## DGII document inventory status

All inventoried official sources are currently **`missing` locally**:

- Informe Técnico e-CF
- Descripción Técnica Servicios DGII
- Formatos XML / Anexos
- XSD e-CF 31–47
- Representación Impresa
- Aprobación / Rechazo Comercial
- Acuse de Recibo
- Autenticación / semilla / token
- Certificación / set de pruebas
- Contingencia
- Norma General 01-2020
- Ley 32-23
- Decreto 587-24

Portal hub recorded in `docs/dgii/DGII_ECF_DOCUMENT_INVENTORY.md`. No PDF/XSD contents were invented.

## Commands run

```bash
.venv/bin/python manage.py makemigrations   # No changes detected
.venv/bin/python manage.py migrate
.venv/bin/python manage.py check
.venv/bin/python -m pytest -q               # 72 passed
.venv/bin/python manage.py seed_bcc
.venv/bin/python manage.py inspect_dgii_mapping --internal-code BCC-AR-2026-000001
.venv/bin/python manage.py inspect_dgii_mapping --internal-code BCC-AR-2026-000001 --json
.venv/bin/python -m pytest -q               # 72 passed
```

## Mapping command output summary (seeded invoice)

- Invoice: `BCC-AR-2026-000001`
- Fiscal type 31 mapped to TipoeCF concept (placeholder catalog)
- Issuer / customer / lines / totals: available
- `official_ncf`: missing
- `official_encf`: missing (WARNING only)
- Status: `READY_FOR_FUTURE_DRAFT`
- Enough internal data for future e-CF draft: **True**
- Compliance claim: **NOT_DGII_COMPLIANT**
- Blocking issues: **0**

## Final pytest result

**72 passed**

## What works now

- Official DGII document inventory scaffolding
- Typed mapping structures in `ecf/dgii`
- Read-only `build_invoice_dgii_mapping_report(invoice)`
- `inspect_dgii_mapping` human + JSON + `--strict`
- Synthetic fixture directory conventions
- Tests proving no Document/ECFDocument creation and no invoice mutation

## What remains intentionally unimplemented

- DGII-compliant XML generation
- XSD validation against official schemas
- Digital signing
- Semilla/token authentication
- TrackId submission / status polling
- Any network call to DGII
- Certificate/private key storage
- Production e-CF emission

## Exact next recommended task

Collect official DGII PDFs/XSDs into a local ignored store, mark inventory rows as `collected`, then begin a **non-production TipoeCF 31 field catalog** derived from the official XSD/format docs (still no signing, auth, or submission).
