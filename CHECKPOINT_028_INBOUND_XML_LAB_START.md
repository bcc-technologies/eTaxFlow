# Checkpoint 028 — Inbound XML Lab Start

## Branch

`revamp/dgii-vault-mvp`

## Current commit

`c0e19bf` — Add pre-certification receiver endpoint contract

## Baseline

- Tests: **239 passed**
- Receiver contract: `receiver_processing_enabled=false`, `persistence=NOT_IMPLEMENTED`, `signature_verification=NOT_IMPLEMENTED`
- Endpoint plan: `endpoint_routes_status=DISABLED`, `public_base_url` blank
- Readiness: `overall_status=BLOCKED`, `NOT_DGII_COMPLIANT`, `dgii_submission_allowed=false`, 43 blockers
- Public stubs: 503 DISABLED JSON

## Intended scope

- Non-production inbound XML lab documentation
- Synthetic ECF/ARECF/ACECF fixtures (NON_OFFICIAL_SYNTHETIC_SAMPLE)
- `ecf/dgii/inbound_lab.py` — analyze, hash, classify
- `dgii_inbound_xml_lab` management command
- Phase 028 readiness blockers and receiver contract updates

## Explicit non-goals

- Live DGII calls or TrackId creation
- Enable public endpoints or production signing
- Signature verification or schema compliance claims
- Persist inbound XML to database
- Official DGII test-set fixtures
- DGII compliance claims
