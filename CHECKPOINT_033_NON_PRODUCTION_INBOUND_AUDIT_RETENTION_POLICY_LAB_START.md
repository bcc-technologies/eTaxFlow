# Checkpoint 033 — Non-production Inbound Audit & Retention Policy Lab Start

## Branch

`revamp/dgii-vault-mvp`

## Current commit

`43f440e` — Add non-production inbound workflow routing lab  
Tag: `dgii-phase-032-inbound-workflow-routing-lab` (published)

## Baseline

- Tests: **352 passed** (Phase 032)
- Persistence lab: dry-run default; lab-only upserts
- Workflow lab: dry-run default; lab-only workflow events
- Receiver contract: workflow lab available; production workflow false
- Endpoint plan: routes DISABLED
- Readiness: `overall_status=BLOCKED`, `NOT_DGII_COMPLIANT`, `dgii_submission_allowed=false`, **81 blockers**

## Intended scope

- Lab-only `InboundXMLLabAuditEvent` model
- Audit/retention service + dry-run-by-default command
- Metadata-only export manifests under `runtime/dgii_lab_exports/`
- Explicit `--apply-lab-audit`; no destructive delete in Phase 033
- Phase 033 readiness blockers

## Explicit non-goals

- Public route audit ingestion
- Production fiscal audit trail or legal retention claim
- Destructive purge/delete of lab records
- DGII calls, TrackId, production signing
- Claim DGII compliance or certification evidence
- Weaken previous blockers
