# Checkpoint 011 — Schema-Aligned Unsigned Tipo 31 Start

## Branch

`revamp/dgii-vault-mvp`

## Current test result

**130 passed**

## Current mapping result (after `seed_bcc`)

For `BCC-AR-2026-000001`:

- Status: `READY_FOR_FUTURE_DRAFT`
- `official_encf`: empty
- Available field count: **19**
- Missing required: **3** — `eNCF`, `FechaHoraFirma`, `Signature`
- Compliance: **NOT_DGII_COMPLIANT**

After demo eNCF + signing placeholder (Phase 008/009 local flow): missing required is **`Signature` only** (available **21**).

## Current remaining required fields

After seed only: `eNCF`, `FechaHoraFirma`, `Signature`  
After allocate + placeholder: `Signature`

## Source files used

- `docs/dgii/sources/e-CF_31_v1.0.xsd`
- `docs/dgii/sources/Formato_Comprobante_Fiscal_Electronico_e-CF_v1.0.pdf` (via prior reviewed notes/catalog)
- `docs/dgii/mapping/TIPO_ECF_31_FIELD_CATALOG.md`
- `docs/dgii/mapping/TIPO_ECF_31_SOURCE_NOTES.md`
- `ecf/dgii/field_catalogs/tipo_ecf_31.py`

## Intended scope

- Conservative XSD structure extraction helpers (stdlib XML only)
- Schema-aligned **unsigned** Tipo 31 XML draft using source-backed tags/order
- Diagnostics outside the schema-shaped body (`NOT_DGII_COMPLIANT`, Signature missing)
- Deterministic output; optional Document save + AuditEvent
- Management command, admin action, tests, docs

## Explicit non-goals

- XMLDSig / real digital signing
- Certificate or private-key storage
- DGII submission / API calls / TrackId
- Claiming DGII compliance or production e-CF behavior
- Fake Signature content
- Adding lxml unless already present
- Full production XSD validation pipeline
