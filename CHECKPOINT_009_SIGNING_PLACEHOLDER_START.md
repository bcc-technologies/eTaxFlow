# Checkpoint 009 — Signing Placeholder Start

## Branch

`revamp/dgii-vault-mvp`

## Current test result

**95 passed**

## Current remaining required Tipo 31 fields

1. `FechaHoraFirma`
2. `Signature`

## Mapping result for BCC-AR-2026-000001

- Status: `READY_FOR_FUTURE_DRAFT`
- After Phase 008 demo allocation, `official_encf` may be present (e.g. `DEMO-E31-000001`)
- Available field count: **20** (when eNCF allocated)
- Missing required: **2** — `FechaHoraFirma`, `Signature`
- Warning: `DEMO_OR_UNAUTHORIZED_ENCF` when demo eNCF present
- Compliance: **NOT_DGII_COMPLIANT**

## Intended scope

- Explicit UNSIGNED / SIGNING_PLACEHOLDER state on `ECFDocument`
- Non-production FechaHoraFirma placeholder via `signature_datetime`
- Service + management command + admin action
- Mapping warning `SIGNING_PLACEHOLDER_ONLY`
- Keep `Signature` missing and compliance **NOT_DGII_COMPLIANT**

## Explicit non-goals

- Real digital signing / XMLDSig
- Certificate or private-key storage
- DGII submission / TrackId polling
- Production e-CF XML generation
- Claiming DGII compliance
