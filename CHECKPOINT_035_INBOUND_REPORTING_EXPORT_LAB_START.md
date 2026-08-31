# Checkpoint 035 — Inbound Reporting Export Lab Start

## Branch

`revamp/dgii-vault-mvp`

## Current commit

`b379f25` — Add inbound security controls policy review lab  
Tag: `dgii-phase-034-inbound-security-policy-lab`

## Baseline

- Tests: **396 passed**
- XML/schema/signature labs: available; LOCAL_OFFLINE / LOCAL_OFFLINE_TEST_ONLY; crypto verify NOT_IMPLEMENTED
- Persistence / workflow / audit labs: dry-run by default; lab-only models
- Security policy: `SECURITY_POLICY_BLOCKED`, `production_security_ready=false`
- Endpoint plan: routes DISABLED
- Receiver contract: public endpoints disabled; production_*_ready false
- Readiness: `overall_status=BLOCKED`, `NOT_DGII_COMPLIANT`, `dgii_submission_allowed=false`, **102 blockers**

## Intended scope

- Metadata-only consolidated inbound lab reporting
- JSON / CSV / Markdown / bundle exports under `runtime/dgii_lab_reports/`
- Report-only command `dgii_inbound_reporting_lab`
- Phase 035 readiness blockers

## Explicit non-goals

- Production dashboard or public endpoint reporting
- Raw XML export
- DGII calls, TrackId, production signing
- Claim compliance or certification evidence
- Mutate Invoice/Document/ECFDocument
- Weaken previous blockers
