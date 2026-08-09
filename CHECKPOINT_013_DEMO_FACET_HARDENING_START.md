# Checkpoint 013 — Demo Facet Hardening Start

## Branch

`revamp/dgii-vault-mvp`

## Current test result

**161 passed**

## Current validation errors (seeded invoice + DEMO-E31 allocate + placeholder)

1. `eNCF` maxLength 15 > 13 — **avoidable_demo_data_facet**
2. `eNCF` pattern fails (`DEMO-E31-…` has hyphens) — **avoidable_demo_data_facet**
3. `RNCEmisor` pattern fails (`1310000000` is 10 digits; XSD wants 9 or 11) — **avoidable_demo_data_facet**
4. Missing child after `FechaHoraFirma` (Signature/`xs:any`) — **intentional_unsigned_gap**

Additional context (not always an instance error):

- Local XSD defines ` IndicadorServicioTodoIncluidoType` (leading space) while element references `IndicadorServicioTodoIncluidoType` — **local_xsd_defect_or_stub**
- Customer RNC `123456789` already matches 9-digit facet — no current error

## Current avoidable vs intentional

| Class | Count (typical) |
|---|---|
| intentional_unsigned_gap | 1 (Signature) |
| avoidable_demo_data_facet | 3 (eNCF×2 + RNCEmisor) |
| local_xsd_defect_or_stub | compile stub required |
| structural_mapping_mismatch | 0 in instance errors |
| unknown | 0 |

## Intended scope

- Extract exact local XSD facets for eNCF / RNC
- Facet-safe synthetic demo profile (issuer RNC + XSD_FACET_DEMO eNCF range)
- Harden `seed_bcc` for owned demo records only
- Explicit `--xsd-facet-demo` allocation flag
- Grouped validation error classification
- Tests + docs; keep Signature missing and **NOT_DGII_COMPLIANT**

## Explicit non-goals

- XMLDSig / real signing / certificates / private keys
- DGII submission / TrackId / compliance claims
- Fake Signature
- Using real RNCs unless verified
- Removing demo/non-authorized warnings
