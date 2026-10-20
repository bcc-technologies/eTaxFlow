# Checkpoint 029 — Local Inbound Schema Validation Start

## Branch

`revamp/dgii-vault-mvp`

## Current commit

`aa50821` — Add non-production inbound XML lab

## Baseline

- Tests: **263 passed**
- Inbound lab: `dgii_inbound_xml_lab` classification/hash only; `schema_validation` not run by default
- Receiver contract: `inbound_xml_lab_available=true`, `persistence=NOT_IMPLEMENTED`, `signature_verification=NOT_IMPLEMENTED`
- Endpoint plan: `endpoint_routes_status=DISABLED`, `public_base_url` blank
- Readiness: `overall_status=BLOCKED`, `NOT_DGII_COMPLIANT`, `dgii_submission_allowed=false`

## Intended scope

- Local/offline XSD validation lab for synthetic ECF / ARECF / ACECF fixtures
- Map document types to local files under `docs/dgii/sources/`
- `dgii_inbound_schema_lab` command with JSON/path/summary
- Honest reporting of local invalid synthetic samples
- Phase 029 readiness blockers

## Explicit non-goals

- Live DGII calls, TrackId, or public endpoint enablement
- Production signing or XMLDSig verification
- Persist inbound XML
- Claim DGII compliance or certification evidence
- Fetch remote XSDs or use network during validation
- Modify official local XSD files
- Force synthetic fixtures to appear schema-valid
