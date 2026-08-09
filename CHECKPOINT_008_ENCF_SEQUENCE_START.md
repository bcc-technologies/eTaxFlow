# Checkpoint 008 — eNCF Sequence Allocation Start

## Branch

`revamp/dgii-vault-mvp`

## Current test result

**82 passed**

## Current remaining required Tipo 31 fields

1. `eNCF`
2. `FechaHoraFirma`
3. `Signature`

## Current mapping result for BCC-AR-2026-000001

- Status: `READY_FOR_FUTURE_DRAFT`
- `official_encf`: `None`
- Available field count: **19**
- Missing required: **3** — `eNCF`, `FechaHoraFirma`, `Signature`
- Compliance: **NOT_DGII_COMPLIANT**

## Intended scope

- Local non-production `ENCFSequenceRange` model
- Controlled demo allocation into `Invoice.official_encf`
- Admin + management command + seed range (no auto-allocate)
- Mapping warnings for demo/non-authorized eNCF values

## Explicit non-goals

- DGII connectivity / requesting authorized ranges
- Digital signing / certificates / private keys
- TrackId submission or polling
- Production e-CF XML generation
- Claiming DGII compliance
- Sending anything to DGII
- Auto-allocating eNCF during `seed_bcc`
