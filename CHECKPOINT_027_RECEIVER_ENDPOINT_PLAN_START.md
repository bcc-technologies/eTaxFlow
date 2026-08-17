# Checkpoint 027 — Receiver Endpoint Plan Start

## Branch

`revamp/dgii-vault-mvp`

## Current commit

`c129a2f` — Add staging DNS and SSL checklist

## Baseline

- Tests: **223 passed**
- Endpoint plan: `deployment_readiness_status=BLOCKED`, `endpoint_routes_status=DISABLED`, `public_base_url` blank
- Readiness: `overall_status=BLOCKED`, `NOT_DGII_COMPLIANT`, `dgii_submission_allowed=false`, 35 blockers
- Public stubs: 503 DISABLED JSON (Phase 026 hardened)

## Intended scope

- Internal receiver endpoint contract document (ECF, ARECF, ACECF)
- Pure-function receiver service skeleton (`ecf/dgii/receiver.py`)
- `dgii_receiver_contract` management command
- Phase 027 readiness blockers
- Tests for classification, disabled boundaries, no DB/XML on public routes

## Explicit non-goals

- Live DGII transport or HTTP calls
- Enable public endpoints by default
- Production signing or signature verification
- Inbound persistence or duplicate detection implementation
- Real receiver processing on public routes
- TrackId creation
- DGII compliance claims
