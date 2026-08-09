# Checkpoint 012 — Local XSD Validation Start

## Branch

`revamp/dgii-vault-mvp`

## Current test result

**153 passed**

## Current unsigned draft status

- Phase 011 schema-aligned unsigned draft available (`ECF` root)
- Signature omitted; diagnostics mark `NOT_DGII_COMPLIANT`
- After `seed_bcc` alone: missing required `eNCF`, `FechaHoraFirma`, `Signature`
- After allocate + placeholder: missing required `Signature` only

## Local XSD file used

`docs/dgii/sources/e-CF_31_v1.0.xsd`

## Current missing required fields

After seed: `eNCF`, `FechaHoraFirma`, `Signature`  
After demo eNCF + signing placeholder: `Signature`

## Intended scope

- Add constrained local XSD validation dependency (`lxml`) — stdlib cannot validate XSD
- Validate unsigned Tipo 31 draft against local XSD only
- Structured expected-failure report (Signature missing / unsigned limitations)
- Management command + Markdown report writer
- Diagnostics fields for local validation availability/expected failure
- Tests and docs

## Explicit non-goals

- XMLDSig / digital signing
- Certificate or private-key storage
- DGII submission / API calls / TrackId
- Claiming DGII compliance or certification evidence
- Fake Signature content
- Remote schema fetching / network validation
