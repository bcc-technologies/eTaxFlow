# Checkpoint 010 — Tipo 31 XML Preview Start

## Branch

`revamp/dgii-vault-mvp`

## Current test result

**104 passed**

## Current mapping result (after `seed_bcc`, no allocate/placeholder)

For `BCC-AR-2026-000001`:

- Status: `READY_FOR_FUTURE_DRAFT`
- `official_encf`: empty
- Available field count: **19**
- Missing required: **3** — `eNCF`, `FechaHoraFirma`, `Signature`
- Compliance: **NOT_DGII_COMPLIANT**

After prior Phase 008/009 local flow (`allocate_demo_encf` + `prepare_signing_placeholder`), expected mapping is:

- Available: **21**
- Missing required: **1** — `Signature`
- Warnings: `DEMO_OR_UNAUTHORIZED_ENCF`, `SIGNING_PLACEHOLDER_ONLY`
- Compliance: **NOT_DGII_COMPLIANT**

## Current missing required fields

After seed only: `eNCF`, `FechaHoraFirma`, `Signature`  
After demo eNCF + signing placeholder: `Signature`

## Intended scope

- Deterministic non-production Tipo e-CF 31 XML **structure preview**
- Root `ETaxFlowTipo31EcfPreview` with explicit `NOT_DGII_COMPLIANT` / `xml_signature=NOT_IMPLEMENTED`
- Preview sections from reviewed field matrix + mapped invoice data
- Demo eNCF only when `allow_demo_encf=True`
- FechaHoraFirma from existing `ECFDocument.signature_datetime` placeholder when present
- Signature remains missing (diagnostic only; no fake signature content)
- Optional save as internal `Document` + AuditEvent
- Management command, admin action, tests, docs

## Explicit non-goals

- Real DGII-compliant e-CF XML
- XMLDSig / real digital signing
- Certificate or private-key storage
- DGII submission / API calls
- TrackId creation or polling
- Production e-CF behavior or compliance claims
- Fake `<Signature>` payload content
