# Checkpoint 030 — Local Inbound Signature Lab Start

## Branch

`revamp/dgii-vault-mvp`

## Current commit

`46ebd21` — Add local inbound schema validation lab

## Baseline

- Tests: **286 passed**
- Inbound XML lab: classification/hash only; schema/signature verification not run by default
- Schema lab: `LOCAL_OFFLINE_ONLY`; synthetic fixtures locally invalid / Tipo 31 XSD compile defect reported
- Receiver contract: `persistence=NOT_IMPLEMENTED`, `signature_verification=NOT_IMPLEMENTED`
- Endpoint plan: routes DISABLED, public_base_url blank
- Readiness: `overall_status=BLOCKED`, `NOT_DGII_COMPLIANT`, `dgii_submission_allowed=false`

## Intended scope

- Local/offline XMLDSig inspection lab for synthetic inbound XML
- Placeholder vs missing Signature classification
- Optional test-only verification only if a safe verifier exists (otherwise NOT_IMPLEMENTED)
- Command `dgii_inbound_signature_lab`
- Phase 030 readiness blockers

## Explicit non-goals

- Live DGII calls, TrackId, public endpoint enablement
- Production signing or real certificates/private keys in repo
- Cryptographic XMLDSig if it requires unsafe/heavy new dependencies
- CRL/OCSP/network certificate fetch
- Persist inbound XML
- Claim DGII compliance or certification evidence
- Weaken previous blockers
