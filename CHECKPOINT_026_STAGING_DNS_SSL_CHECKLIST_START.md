# Checkpoint 026 — Staging DNS/SSL Checklist Start

## Branch

`revamp/dgii-vault-mvp`

## Current commit

`690ea1d` — Add pre-certification endpoint design

## Baseline

- Tests: **215 passed**
- Endpoint plan: `readiness_status=BLOCKED`, `url_status=BLOCKED`, `public_base_url` blank
- Readiness: `overall_status=BLOCKED`, `NOT_DGII_COMPLIANT`, `dgii_submission_allowed=false`, ~27 blockers
- Route stubs: 503 DISABLED JSON (Phase 025)

## Intended scope

- Staging/pre-cert DNS/SSL deployment checklist (no deploy, no DGII calls)
- Harden disabled `/fe/...` route stub responses
- Extend endpoint plan + readiness with Phase 026 deployment verification placeholders
- Update `.env.staging.example` with safe placeholders

## Explicit non-goals

- Live DGII integration or HTTP transport
- Enable public endpoints by default
- Deploy DNS/SSL or set real production URLs
- Production signing or compliance claims
- Merge staging/pre-cert/production environments
