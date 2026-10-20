# Checkpoint 037 — Certification Portal Package Draft Start

## Branch

`revamp/dgii-vault-mvp`

## Current commit

`6710797` — Add staging deployment evidence collector lab  
Tag: `dgii-phase-036-staging-evidence-lab`

## Baseline

- Tests: **428 passed**
- Staging evidence: `STAGING_EVIDENCE_BLOCKED`; offline/manual; no network checks
- Reporting lab: metadata-only; no raw XML
- Security policy: `SECURITY_POLICY_BLOCKED`
- Endpoint plan: routes DISABLED; DNS/SSL UNVERIFIED
- Receiver contract: public endpoints disabled; `production_staging_ready=false`
- Readiness: `BLOCKED` / `NOT_DGII_COMPLIANT` / `dgii_submission_allowed=false` / ~**121 blockers**

## Intended scope

- Draft-only certification portal software postulation package
- Planned URLs, supporting summaries, blockers, human decisions
- Export under `runtime/dgii_certification_package_drafts/`
- Command `dgii_certification_package_lab`
- Phase 037 readiness blockers

## Explicit non-goals

- Portal submission, signed XML, uploads, DGII calls, TrackId
- Public endpoint activation, live DNS/TLS/HTTPS
- Claim certification evidence or portal submission readiness
- Store secrets/certificates
- Weaken previous blockers
