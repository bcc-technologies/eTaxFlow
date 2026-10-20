# Checkpoint 034 — Inbound Security Controls Policy Review Lab Start

## Branch

`revamp/dgii-vault-mvp`

## Current commit

`49b920d` — Add non-production inbound audit retention lab

## Baseline

- Tests: **374 passed** (expected from Phase 033)
- Public `/fe/...` routes: **503 DISABLED**
- Persistence / workflow / audit labs: dry-run by default; lab-only models
- Receiver contract: production_*_ready false; public routes disabled
- Endpoint plan: routes DISABLED
- Readiness: `overall_status=BLOCKED`, `NOT_DGII_COMPLIANT`, `dgii_submission_allowed=false`, **89 blockers**

## Intended scope

- Lab-only inbound security controls catalog and policy evaluation
- Dry-run/report-only `dgii_inbound_security_policy_lab` command
- Metadata-only export under `runtime/dgii_security_reports/`
- Safe settings placeholders (CONFIGURED_PLACEHOLDER ≠ ENFORCED)
- Phase 034 readiness blockers

## Explicit non-goals

- Enable public endpoints or enforce body/rate/content-type in public views
- Production security approval or penetration testing
- DGII calls, TrackId, production signing
- Claim compliance or certification evidence
- Weaken previous blockers
- Destructive retention or secret storage
