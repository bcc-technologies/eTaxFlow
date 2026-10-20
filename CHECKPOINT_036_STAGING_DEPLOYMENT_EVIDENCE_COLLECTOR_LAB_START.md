# Checkpoint 036 — Staging Deployment Evidence Collector Lab Start

## Branch

`revamp/dgii-vault-mvp`

## Current commit

`f82a249` — Add inbound reporting export lab  
Tag: `dgii-phase-035-inbound-reporting-export-lab`

## Baseline

- Tests: **415 passed**
- Reporting lab: metadata-only; no raw XML; `production_dashboard_ready=false`
- Security policy: `SECURITY_POLICY_BLOCKED`, `production_security_ready=false`
- Endpoint plan: routes DISABLED; DNS/SSL UNVERIFIED
- Receiver contract: public endpoints disabled
- Readiness: `overall_status=BLOCKED`, `NOT_DGII_COMPLIANT`, `dgii_submission_allowed=false`, ~**109 blockers**

## Intended scope

- Offline/manual staging evidence catalog, template, validation, and metadata report
- Safe paths under `runtime/dgii_staging_evidence/`
- Command `dgii_staging_evidence_lab`
- Phase 036 readiness blockers

## Explicit non-goals

- Live DNS/TLS/HTTPS/network checks
- Public endpoint activation or deployment
- DGII calls, TrackId, production signing
- Claim staging approval or certification evidence
- Store real certificates/secrets
- Weaken previous blockers
