# Checkpoint 032 — Non-production Inbound Workflow Routing Lab Start

## Branch

`revamp/dgii-vault-mvp`

## Current commit

`f7adeea` — Add non-production inbound persistence lab

## Baseline

- Tests: **328 passed**
- Persistence lab: dry-run default; `--persist-lab-records` upserts lab rows only
- Schema lab: `LOCAL_OFFLINE_ONLY`
- Signature lab: `LOCAL_OFFLINE_TEST_ONLY`; cryptographic XMLDSig `NOT_IMPLEMENTED`
- Receiver contract: persistence lab available; production persistence `NOT_IMPLEMENTED`; public endpoints disabled
- Endpoint plan: routes DISABLED
- Readiness: `overall_status=BLOCKED`, `NOT_DGII_COMPLIANT`, `dgii_submission_allowed=false`, **73 blockers**

## Intended scope

- Lab-only workflow routing service for `InboundXMLLabRecord` rows
- `InboundXMLLabWorkflowEvent` model (no Invoice/Document/ECFDocument links)
- Dry-run-by-default `dgii_inbound_workflow_lab` command
- Explicit `--apply-lab-workflow` to persist workflow events
- Phase 032 readiness blockers

## Explicit non-goals

- Public route workflow or XML parse
- Fiscal acceptance, acuse, or aprobación generation
- DGII calls, TrackId, production signing
- Production document mutation
- Claim DGII compliance or certification evidence
- Weaken previous blockers
