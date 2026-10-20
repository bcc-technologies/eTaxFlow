# Checkpoint 031 — Non-production Inbound Persistence Lab Start

## Branch

`revamp/dgii-vault-mvp`

## Current commit

`4a47093` — Add local inbound signature verification lab

## Baseline

- Tests: **309 passed**
- Inbound XML lab: classification/hash only; persistence not run
- Schema lab: `LOCAL_OFFLINE_ONLY`
- Signature lab: `LOCAL_OFFLINE_TEST_ONLY`; cryptographic XMLDSig `NOT_IMPLEMENTED`
- Receiver contract: `persistence=NOT_IMPLEMENTED`, public endpoints disabled
- Endpoint plan: routes DISABLED
- Readiness: `overall_status=BLOCKED`, `NOT_DGII_COMPLIANT`, `dgii_submission_allowed=false`

## Intended scope

- Lab-only `InboundXMLLabRecord` model (no Invoice/Document/ECFDocument links)
- Persistence service + dry-run-by-default command
- Deduplicate by `raw_sha256`; raw XML off by default
- Phase 031 readiness blockers

## Explicit non-goals

- Public route persistence or XML parse
- DGII calls, TrackId, production signing
- Production inbound/fiscal document workflow
- Claim DGII compliance or certification evidence
- Weaken previous blockers
- Store real certificates or private keys
